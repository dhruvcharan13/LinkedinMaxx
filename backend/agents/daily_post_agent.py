"""
Daily Post Agent - Generates LinkedIn posts using LangChain and Google Gemini.
Publishes post instructions to Redis for Playwright to execute.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
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


class DailyPostAgent:
    """Agent that generates daily LinkedIn posts."""
    
    def __init__(self):
        # Set API key as environment variable for Gemini
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        # Always use gemini-2.5-flash for speed - no mapping needed, just use flash directly
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Hardcoded for speed - flash is fastest
            temperature=0.7,
            max_tokens=300  # Limit response length for speed
        )
        self.output_parser = StrOutputParser()
        self._setup_prompt()
    
    def _setup_prompt(self):
        """Set up the prompt template for post generation (optimized for speed)."""
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """Create a LinkedIn post as a Waterloo student. 
2-3 paragraphs. Professional but authentic. Include hashtags. First person. Be genuine."""),
            ("human", """Context: {context}
Date: {date}

Generate post:""")
        ])
    
    def generate_post(self, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a daily LinkedIn post.
        
        Args:
            context: Optional context (e.g., from Google Calendar, Notion, or activities)
            
        Returns:
            Dictionary with post content and metadata
        """
        feedback.agent_action("Daily Post Agent", "Generating LinkedIn post...")
        
        # Get current date
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Use default context if none provided
        if not context:
            context = "A typical day as a Waterloo student - working on projects, attending classes, or building something cool."
        
        # Create chain
        chain = self.prompt | self.llm | self.output_parser
        
        try:
            # Generate post
            feedback.task_processing("post_generation", "daily_post")
            post_content = chain.invoke({
                "context": context,
                "date": current_date
            })
            
            # Create metadata
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "context_used": context,
                "model": os.getenv("GEMINI_MODEL", "gemini-pro"),
                "agent": "daily_post_agent"
            }
            
            feedback.task_completed("post_generation", "daily_post", f"Generated {len(post_content)} characters")
            feedback.agent_action("Daily Post Agent", "Post generated successfully", 
                                f"Length: {len(post_content)} chars")
            
            # Display the generated post
            logger.info(f"\n{'='*60}")
            logger.info("GENERATED POST:")
            logger.info(f"{'='*60}")
            logger.info(post_content)
            logger.info(f"{'='*60}\n")
            
            return {
                "content": post_content,
                "metadata": metadata
            }
            
        except Exception as e:
            feedback.error("Failed to generate post", e)
            logger.error(f"Error generating post: {e}")
            raise
    
    def publish_post(self, post_content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Publish post instruction to Redis for Playwright to execute.
        
        Args:
            post_content: The generated post content
            metadata: Optional metadata about the post
            
        Returns:
            Task ID
        """
        feedback.agent_action("Daily Post Agent", "Publishing post instruction to Playwright queue...")
        
        task_id = redis_client.queue_post_instruction(post_content, metadata)
        
        feedback.task_completed("post_publish", task_id, "Post instruction queued for Playwright")
        
        return task_id
    
    def generate_and_publish(self, context: Optional[str] = None) -> str:
        """
        Generate a post and immediately publish it to the queue.
        
        Args:
            context: Optional context for post generation
            
        Returns:
            Task ID
        """
        # Generate post
        result = self.generate_post(context)
        
        # Publish to queue
        task_id = self.publish_post(result["content"], result["metadata"])
        
        return task_id


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = DailyPostAgent()
    
    # Generate and publish a test post
    print("Testing Daily Post Agent...")
    task_id = agent.generate_and_publish(
        context="Just finished building an AI agent system for LinkedIn automation!"
    )
    print(f"\n✅ Post published with task ID: {task_id}")

