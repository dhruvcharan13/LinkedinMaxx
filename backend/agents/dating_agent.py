"""
Dating Agent - Detects Waterloo students, estimates their stream,
and generates pickup lines for students in the same stream.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import os
import json
import re
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


class StreamEstimate(BaseModel):
    """Stream estimation result."""
    is_waterloo: bool = Field(description="Whether the person is a Waterloo student")
    estimated_stream: Optional[str] = Field(description="Estimated stream (1A, 1B, 2A, 2B, 4, 8, or None)")
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Reasoning for the estimate")


class DatingAgent:
    """Agent that detects Waterloo students and generates pickup lines."""
    
    def __init__(self, waterloo_streams_path: str = "./data/waterloo_streams.json", user_stream: Optional[str] = None):
        # Set API key as environment variable for Gemini
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        # Always use gemini-2.5-flash for speed - no mapping needed, just use flash directly
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Hardcoded for speed - flash is fastest
            temperature=0.7  # Slightly lower for faster, more consistent responses
        )
        self.output_parser = JsonOutputParser(pydantic_object=StreamEstimate)
        self.waterloo_streams = self._load_waterloo_streams(waterloo_streams_path)
        self.user_stream = user_stream or os.getenv("USER_STREAM", "1A")  # Default stream, should be set in .env
        self._setup_prompts()
    
    def _load_waterloo_streams(self, path: str) -> Dict[str, Any]:
        """Load Waterloo stream data."""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Waterloo streams file not found at {path}, using defaults")
            return {
                "streams": {},
                "programs": {},
                "coop_keywords": {
                    "fall": ["september", "october", "november", "dec", "fall"],
                    "winter": ["january", "february", "march", "april", "winter"],
                    "spring": ["may", "june", "july", "august", "spring", "summer"]
                }
            }
    
    def _setup_prompts(self):
        """Set up prompt templates."""
        # Stream estimation prompt (optimized for speed)
        self.stream_estimation_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze Waterloo student profiles. Return valid JSON.
Streams: 1A (Fall co-op), 1B (Winter), 2A (Spring), 2B (Summer), 4 (Alt Fall), 8 (No co-op).
Return JSON with: is_waterloo (boolean), estimated_stream (string or null), confidence (float 0-1), reasoning (string, brief)."""),
            ("human", """Profile:
Bio: {bio}
Experience: {experience}
Education: {education}
Dates: {internship_dates}

Analyze and return valid JSON only.""")
        ])
        
        # Pickup line generation prompt (optimized for speed)
        self.pickup_line_prompt = ChatPromptTemplate.from_messages([
            ("system", """Generate a witty, LinkedIn-appropriate pickup line for a Waterloo {stream} student. 
Requirements:
- 1-2 sentences maximum
- Reference Waterloo or co-op culture
- Playful but professional tone
- Appropriate for LinkedIn

Return only the pickup line text, no additional explanation."""),
            ("human", """Profile: {profile_summary}

Generate pickup line:""")
        ])
    
    def extract_internship_dates(self, experience: str) -> str:
        """Extract internship/co-op dates from experience text."""
        # Look for date patterns
        date_patterns = [
            r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
            r'\d{4}\s*-\s*\d{4}',
            r'(Spring|Summer|Fall|Winter)\s+\d{4}',
            r'Co-op|Intern|Internship'
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, experience, re.IGNORECASE)
            dates_found.extend(matches)
        
        return ", ".join(set(dates_found)) if dates_found else "No dates found"
    
    def estimate_stream(self, profile_data: Dict[str, Any]) -> StreamEstimate:
        """
        Estimate if profile is a Waterloo student and their stream.
        
        Args:
            profile_data: Dictionary with profile information
            
        Returns:
            StreamEstimate object
        """
        feedback.agent_action("Dating Agent", "Estimating Waterloo stream...")
        
        bio = profile_data.get("bio", "")
        experience = profile_data.get("experience", "")
        education = profile_data.get("education", "")
        
        # Extract internship dates
        internship_dates = self.extract_internship_dates(experience)
        
        # Check for Waterloo mentions
        waterloo_keywords = ["university of waterloo", "uwaterloo", "waterloo", "uw"]
        is_waterloo_mentioned = any(
            keyword.lower() in (bio + " " + education).lower() 
            for keyword in waterloo_keywords
        )
        
        if not is_waterloo_mentioned:
            feedback.agent_action("Dating Agent", "Not a Waterloo student (no Waterloo mention)")
            return StreamEstimate(
                is_waterloo=False,
                estimated_stream=None,
                confidence=0.9,
                reasoning="No Waterloo keywords found in profile"
            )
        
        # Try to infer stream from profile data first (simple rule-based check)
        # Look for "2A", "1A", "1B", "2B" in education/bio
        stream_keywords = {
            "2A": ["2A", "2a", "2 A", "second year", "sophomore"],
            "1A": ["1A", "1a", "1 A", "first year", "freshman"],
            "1B": ["1B", "1b", "1 B"],
            "2B": ["2B", "2b", "2 B"]
        }
        
        profile_text = (bio + " " + education).lower()
        inferred_stream = None
        
        for stream, keywords in stream_keywords.items():
            if any(keyword in profile_text for keyword in keywords):
                inferred_stream = stream
                break
        
        # Use LLM to estimate stream (with fallback to inferred stream)
        estimation_chain = self.stream_estimation_prompt | self.llm | self.output_parser
        
        try:
            result = estimation_chain.invoke({
                "bio": bio,
                "experience": experience,
                "education": education,
                "internship_dates": internship_dates
            })
            
            estimate = StreamEstimate(**result)
            
            # If LLM couldn't estimate but we inferred one, use inferred
            if not estimate.estimated_stream and inferred_stream:
                estimate.estimated_stream = inferred_stream
                estimate.confidence = 0.7
                estimate.reasoning = f"Inferred from profile text: {inferred_stream}"
            
            logger.info(f"Stream estimate: {estimate.estimated_stream} (confidence: {estimate.confidence:.2%})")
            logger.info(f"Reasoning: {estimate.reasoning}")
            
            feedback.agent_action("Dating Agent", 
                                f"Estimated stream: {estimate.estimated_stream}",
                                f"Confidence: {estimate.confidence:.2%}")
            
            return estimate
            
        except Exception as e:
            feedback.error("Failed to estimate stream", e)
            logger.error(f"Error estimating stream: {e}")
            # Use inferred stream if available, otherwise return None
            return StreamEstimate(
                is_waterloo=True,
                estimated_stream=inferred_stream,  # Use inferred stream as fallback
                confidence=0.6 if inferred_stream else 0.5,
                reasoning=f"Estimation failed, using inferred: {inferred_stream}" if inferred_stream else f"Estimation failed: {str(e)}"
            )
    
    def is_same_stream(self, estimated_stream: Optional[str]) -> bool:
        """Check if estimated stream matches user's stream."""
        if not estimated_stream:
            return False
        return estimated_stream.upper() == self.user_stream.upper()
    
    def generate_pickup_line(self, profile_data: Dict[str, Any], stream: str) -> str:
        """
        Generate a pickup line for a Waterloo student in the same stream.
        
        Args:
            profile_data: Profile information
            stream: Their estimated stream
            
        Returns:
            Pickup line message
        """
        feedback.agent_action("Dating Agent", "Generating pickup line...")
        
        bio = profile_data.get("bio", "")
        experience = profile_data.get("experience", "")
        profile_summary = f"Bio: {bio[:200]}, Experience: {experience[:200]}"
        
        chain = self.pickup_line_prompt | self.llm | StrOutputParser()
        
        try:
            pickup_line = chain.invoke({
                "stream": stream,
                "profile_summary": profile_summary
            })
            
            logger.info(f"Generated pickup line: {pickup_line}")
            feedback.agent_action("Dating Agent", "Pickup line generated!", pickup_line[:100])
            
            return pickup_line
            
        except Exception as e:
            feedback.error("Failed to generate pickup line", e)
            # Fallback pickup line
            return f"Hey! Saw you're in {stream} - same stream here! Want to grab coffee and compare co-op experiences? ☕"
    
    def process_waterloo_student(self, profile_url: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a Waterloo student profile: estimate stream and generate pickup line if same stream.
        
        Args:
            profile_url: URL of the LinkedIn profile
            profile_data: Profile information
            
        Returns:
            Dictionary with processing result
        """
        feedback.task_processing("dating_processing", profile_url)
        
        # Estimate stream
        estimate = self.estimate_stream(profile_data)
        
        result = {
            "profile_url": profile_url,
            "is_waterloo": estimate.is_waterloo,
            "estimated_stream": estimate.estimated_stream,
            "confidence": estimate.confidence,
            "user_stream": self.user_stream,
            "processed_at": datetime.now().isoformat()
        }
        
        if not estimate.is_waterloo:
            result["action"] = "skip"
            result["message"] = None
            feedback.task_completed("dating_processing", profile_url, "Not a Waterloo student")
            return result
        
        # Check if same stream
        if self.is_same_stream(estimate.estimated_stream):
            # Generate pickup line
            pickup_line = self.generate_pickup_line(profile_data, estimate.estimated_stream)
            result["message"] = pickup_line
            result["action"] = "send_message"
            result["same_stream"] = True
            
            # Publish message instruction (format matches test_profile.json)
            name = profile_data.get("name", "LinkedIn User")
            task_id = redis_client.queue_message_instruction(profile_url, pickup_line, "send_message", name=name)
            result["task_id"] = task_id
            
            feedback.task_completed("dating_processing", profile_url, 
                                  f"Pickup line generated for same stream ({estimate.estimated_stream})")
            
        else:
            # Different stream, just connect
            result["action"] = "connect_only"
            result["message"] = None
            result["same_stream"] = False
            
            # Publish connection instruction (format matches test_profile.json)
            name = profile_data.get("name", "LinkedIn User")
            task_id = redis_client.queue_message_instruction(profile_url, "", "connect_only", name=name)
            result["task_id"] = task_id
            
            feedback.task_completed("dating_processing", profile_url, 
                                  f"Different stream ({estimate.estimated_stream} vs {self.user_stream}), connection queued")
        
        return result


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = DatingAgent(user_stream="1A")
    
    # Test profile
    test_profile = {
        "url": "https://linkedin.com/in/test",
        "bio": "Software Engineering student at University of Waterloo | Co-op at Google",
        "experience": "Software Engineering Intern at Google (Fall 2024), Software Developer at Shopify (Spring 2024)",
        "education": "University of Waterloo - Software Engineering"
    }
    
    print("Testing Dating Agent...")
    result = agent.process_waterloo_student(test_profile["url"], test_profile)
    print(f"\n✅ Profile processed: {result}")

