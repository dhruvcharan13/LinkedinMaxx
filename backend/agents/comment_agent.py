"""
Comment Agent - Analyzes LinkedIn posts and generates relevant comments.
Decides whether to comment and generates appropriate comment text.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
from utils.logger import feedback, logger
from utils.redis_client import redis_client

# Fix for langchain attribute errors (verbose, debug, llm_cache)
import langchain
if not hasattr(langchain, 'verbose'):
    langchain.verbose = False
if not hasattr(langchain, 'debug'):
    langchain.debug = False
if not hasattr(langchain, 'llm_cache'):
    langchain.llm_cache = None

load_dotenv()


class CommentDecision(BaseModel):
    """Decision on whether to comment on a post."""
    should_comment: bool = Field(description="Whether we should comment on this post")
    reasoning: str = Field(description="Brief reasoning for the decision")
    confidence: float = Field(description="Confidence score between 0 and 1")


class CommentAgent:
    """Agent that analyzes posts and generates comments."""
    
    def __init__(self):
        # Set API key as environment variable for Gemini
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        # Always use gemini-2.5-flash for speed - no mapping needed, just use flash directly
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Hardcoded for speed - flash is fastest
            temperature=0.7,
            max_tokens=150  # Comments should be concise
        )
        self.output_parser = JsonOutputParser(pydantic_object=CommentDecision)
        self.str_parser = StrOutputParser()
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Set up prompt templates."""
        # Comment decision prompt (optimized for speed)
        self.decision_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze LinkedIn posts and decide if we should comment. Return valid JSON.
Criteria for commenting:
- Post is relevant to tech, career, startups, or Waterloo
- Post is not spam or low-quality
- We can add value with our comment
- Post is recent/active

Return JSON with: should_comment (boolean), confidence (float 0-1), reasoning (string, brief).
Example format: {{"should_comment": true, "confidence": 0.8, "reasoning": "Relevant tech post"}}"""),
            ("human", """Post:
Body: {body}
Author: {author}
Engagement: {engagement}

Analyze and return valid JSON only.""")
        ])
        
        # Comment generation prompt (optimized for speed)
        self.comment_prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate a LinkedIn comment for a post. Return only the comment text.
Requirements:
- 1-2 sentences maximum
- Professional but engaging
- Add value or show genuine interest
- Relevant to the post content
- Appropriate for LinkedIn

Return only the comment text, no additional explanation."""),
            ("human", """Post:
Body: {body}
Author: {author}

Generate a comment:""")
        ])
    
    def should_comment(self, post_data: Dict[str, Any]) -> CommentDecision:
        """
        Decide if we should comment on a post.
        
        Args:
            post_data: Dictionary with post information (body, author, engagement, etc.)
            
        Returns:
            CommentDecision object
        """
        feedback.agent_action("Comment Agent", "Analyzing post...")
        
        body = post_data.get("body", "")
        author = post_data.get("author", "Unknown")
        engagement = post_data.get("engagement", "Unknown")
        
        # Quick filter: skip if body is too short or empty
        if not body or len(body.strip()) < 10:
            feedback.agent_action("Comment Agent", "Skipping post (too short/empty)")
            return CommentDecision(
                should_comment=False,
                confidence=0.9,
                reasoning="Post body is too short or empty"
            )
        
        # Use LLM to decide - use simple keyword-based approach for speed
        # Check for relevant keywords first
        tech_keywords = ['tech', 'ai', 'software', 'startup', 'career', 'waterloo', 'engineering', 'developer', 'coding', 'programming']
        has_relevant_keywords = any(keyword in body.lower() for keyword in tech_keywords)
        
        # Simple heuristic: comment on tech-related posts
        if has_relevant_keywords and len(body) > 20:
            feedback.agent_action("Comment Agent", 
                                f"Decision: Comment (keywords found)",
                                f"Confidence: 75%")
            return CommentDecision(
                should_comment=True,
                confidence=0.75,
                reasoning="Relevant tech/career keywords found in post"
            )
        else:
            feedback.agent_action("Comment Agent", 
                                f"Decision: Skip",
                                f"Confidence: 70%")
            return CommentDecision(
                should_comment=False,
                confidence=0.7,
                reasoning="No relevant keywords or post too short"
            )
    
    def generate_comment(self, post_data: Dict[str, Any]) -> str:
        """
        Generate a comment for a LinkedIn post.
        
        Args:
            post_data: Dictionary with post information
            
        Returns:
            Comment text
        """
        feedback.agent_action("Comment Agent", "Generating comment...")
        
        body = post_data.get("body", "")
        author = post_data.get("author", "Unknown")
        
        comment_chain = self.comment_prompt | self.llm
        
        try:
            # Get raw response
            raw_response = comment_chain.invoke({
                "body": body,
                "author": author
            })
            
            # Extract content
            comment = raw_response.content if hasattr(raw_response, 'content') else str(raw_response)
            
            # Clean up comment (remove markdown, extra whitespace)
            comment = comment.strip()
            if comment.startswith('"') and comment.endswith('"'):
                comment = comment[1:-1]
            if comment.startswith("'") and comment.endswith("'"):
                comment = comment[1:-1]
            
            # Fallback if comment is empty
            if not comment or len(comment) < 5:
                comment = f"Great post{', ' + author if author != 'Unknown' else ''}! Thanks for sharing. 👍"
            
            logger.info(f"Generated comment: {comment}")
            feedback.agent_action("Comment Agent", "Comment generated!", comment[:100])
            
            return comment
            
        except Exception as e:
            feedback.error("Failed to generate comment", e)
            logger.error(f"Error generating comment: {e}")
            # Fallback comment
            return f"Great post{', ' + author if author != 'Unknown' else ''}! Thanks for sharing. 👍"
    
    def process_post(self, post_url: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a LinkedIn post: decide if we should comment and generate comment if yes.
        
        Args:
            post_url: URL of the LinkedIn post
            post_data: Post information (must include "body" field)
            
        Returns:
            Dictionary with processing result
        """
        feedback.task_processing("comment_processing", post_url)
        
        # Check if body field exists
        if "body" not in post_data:
            feedback.error("Post data missing 'body' field", None)
            return {
                "post_url": post_url,
                "should_comment": False,
                "comment": None,
                "action": "skip",
                "reasoning": "Post data missing 'body' field",
                "processed_at": datetime.now().isoformat()
            }
        
        # Decide if we should comment
        decision = self.should_comment(post_data)
        
        result = {
            "post_url": post_url,
            "should_comment": decision.should_comment,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "processed_at": datetime.now().isoformat()
        }
        
        if decision.should_comment:
            # Generate comment
            comment = self.generate_comment(post_data)
            result["comment"] = comment
            result["action"] = "comment"
            
            # Queue for frontend approval
            author = post_data.get("author", "Unknown")
            task_data = {
                "type": "comment",
                "content": comment,
                "url": post_url,
                "name": author,
                "agent_name": "Comment Agent",
                "agent_emoji": "💬",
                "metadata": {
                    "confidence": decision.confidence,
                    "reasoning": decision.reasoning,
                    "engagement": post_data.get("engagement", "Unknown")
                }
            }
            task_id = redis_client.queue_pending_task(task_data)
            result["task_id"] = task_id
            
            feedback.task_completed("comment_processing", post_url, 
                                  f"Comment generated and queued for approval")
        else:
            # Skip commenting
            result["comment"] = None
            result["action"] = "skip"
            
            feedback.task_completed("comment_processing", post_url, 
                                  f"Skipping post: {decision.reasoning}")
        
        return result


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = CommentAgent()
    
    # Test post
    test_post = {
        "url": "https://linkedin.com/feed/update/...",
        "body": "Just finished building an AI agent system for LinkedIn automation! Excited to share what we've learned.",
        "author": "Tech Influencer",
        "engagement": "50 likes, 10 comments"
    }
    
    print("Testing Comment Agent...")
    result = agent.process_post(test_post["url"], test_post)
    print(f"\n✅ Post processed: {result}")

