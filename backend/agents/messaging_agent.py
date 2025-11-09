"""
Messaging Agent - Classifies LinkedIn profiles and generates appropriate messages.
Categories: Recruiter, Co-founder/Founder, Waterloo Student (for dating agent)
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import os
import json
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


class ProfileClassification(BaseModel):
    """Classification result for a LinkedIn profile."""
    category: Literal["recruiter", "cofounder", "waterloo_student", "other"] = Field(
        description="The category of the profile"
    )
    confidence: float = Field(description="Confidence score between 0 and 1")
    reasoning: str = Field(description="Brief reasoning for the classification")


class MessagingAgent:
    """Agent that classifies profiles and generates messages."""
    
    def __init__(self):
        # Set API key as environment variable for Gemini
        os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")
        # Always use gemini-2.5-flash for speed - no mapping needed, just use flash directly
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",  # Hardcoded for speed - flash is fastest
            temperature=0.6,  # Lower temperature for faster, more deterministic responses
            max_tokens=200  # Limit response length for speed
        )
        self.output_parser = JsonOutputParser(pydantic_object=ProfileClassification)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Set up prompt templates."""
        # Classification prompt (optimized for speed)
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """Classify LinkedIn profiles. Return valid JSON.
Categories: "recruiter" (Talent Acquisition/HR), "cofounder" (Founder/Co-founder), "waterloo_student" (UWaterloo student), "other".
Return JSON with: category (string), confidence (float 0-1), reasoning (string, brief)."""),
            ("human", """Profile:
Bio: {bio}
Experience: {experience}
Education: {education}

Classify and return valid JSON only.""")
        ])
        
        # Message generation prompts (optimized for speed - concise)
        self.recruiter_message_prompt = ChatPromptTemplate.from_messages([
            ("system", """Write a 2-3 sentence LinkedIn message to a recruiter. 
Professional, friendly. Mention you're a Waterloo student. Ask about internships."""),
            ("human", "Recruiter profile: {bio}\nWrite message:")
        ])
        
        self.cofounder_message_prompt = ChatPromptTemplate.from_messages([
            ("system", """Write a 2-3 sentence LinkedIn message to a founder/co-founder.
Show you reviewed their profile. Express interest in startups."""),
            ("human", "Founder profile: {bio}\nExperience: {experience}\nWrite message:")
        ])
    
    def classify_profile(self, profile_data: Dict[str, Any]) -> ProfileClassification:
        """
        Classify a LinkedIn profile into a category.
        If profile_data already has a 'type' field from Patchright, use it.
        Otherwise, use LLM to classify.
        
        Args:
            profile_data: Dictionary with profile information (bio, experience, education, type)
            
        Returns:
            ProfileClassification object
        """
        # Check if type is already provided by Patchright
        profile_type = profile_data.get("type", "").lower()
        
        if profile_type:
            # Map Patchright types to agent categories
            type_mapping = {
                "waterloo": "waterloo_student",
                "recruiter": "recruiter",
                "cofounder": "cofounder",
                "co-founder": "cofounder",
                "founder": "cofounder",
                "other": "other"
            }
            
            category = type_mapping.get(profile_type, "other")
            feedback.agent_action("Messaging Agent", f"Using pre-classified type: {profile_type}")
            feedback.agent_classification(
                profile_data.get("url", "unknown"),
                category,
                1.0  # High confidence since Patchright already classified it
            )
            
            return ProfileClassification(
                category=category,
                confidence=1.0,
                reasoning=f"Pre-classified by Patchright as: {profile_type}"
            )
        
        # No type provided, use LLM to classify
        feedback.agent_action("Messaging Agent", "Classifying profile with LLM...")
        
        bio = profile_data.get("bio", "Not available")
        experience = profile_data.get("experience", "Not available")
        education = profile_data.get("education", "Not available")
        
        # Create classification chain
        classification_chain = self.classification_prompt | self.llm | self.output_parser
        
        try:
            result = classification_chain.invoke({
                "bio": bio,
                "experience": experience,
                "education": education
            })
            
            classification = ProfileClassification(**result)
            
            # Display classification
            feedback.agent_classification(
                profile_data.get("url", "unknown"),
                classification.category,
                classification.confidence
            )
            logger.info(f"Classification: {classification.category} (confidence: {classification.confidence:.2%})")
            logger.info(f"Reasoning: {classification.reasoning}")
            
            return classification
            
        except Exception as e:
            feedback.error("Failed to classify profile", e)
            logger.error(f"Error classifying profile: {e}")
            # Return default classification
            return ProfileClassification(
                category="other",
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}"
            )
    
    def generate_recruiter_message(self, profile_data: Dict[str, Any]) -> str:
        """Generate a message for a recruiter."""
        feedback.agent_action("Messaging Agent", "Generating recruiter message...")
        
        bio = profile_data.get("bio", "")
        chain = self.recruiter_message_prompt | self.llm | StrOutputParser()
        
        try:
            message = chain.invoke({"bio": bio})
            logger.info(f"Generated recruiter message: {message[:100]}...")
            return message
        except Exception as e:
            feedback.error("Failed to generate recruiter message", e)
            raise
    
    def generate_cofounder_message(self, profile_data: Dict[str, Any]) -> str:
        """Generate a message for a co-founder/founder."""
        feedback.agent_action("Messaging Agent", "Generating co-founder message...")
        
        bio = profile_data.get("bio", "")
        experience = profile_data.get("experience", "")
        chain = self.cofounder_message_prompt | self.llm | StrOutputParser()
        
        try:
            message = chain.invoke({"bio": bio, "experience": experience})
            logger.info(f"Generated co-founder message: {message[:100]}...")
            return message
        except Exception as e:
            feedback.error("Failed to generate co-founder message", e)
            raise
    
    def process_profile(self, profile_url: str, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a profile: classify and generate appropriate message or route to dating agent.
        If profile_data has a 'type' field from Patchright, uses that instead of LLM classification.
        
        Args:
            profile_url: URL of the LinkedIn profile
            profile_data: Profile information (bio, experience, education, type)
            
        Returns:
            Dictionary with processing result
        """
        feedback.task_processing("profile_processing", profile_url)
        
        # Classify profile (will use pre-classified type if available)
        classification = self.classify_profile(profile_data)
        
        result = {
            "profile_url": profile_url,
            "classification": classification.dict(),
            "processed_at": datetime.now().isoformat()
        }
        
        # Route based on classification
        if classification.category == "recruiter":
            message = self.generate_recruiter_message(profile_data)
            result["message"] = message
            result["action"] = "send_message"
            
            # Queue for frontend approval
            name = profile_data.get("name", "LinkedIn User")
            task_data = {
                "type": "message",
                "content": message,
                "url": profile_url,
                "name": name,
                "agent_name": "Messaging Agent",
                "agent_emoji": "💬",
                "metadata": {
                    "action": "send_message",
                    "classification": "recruiter",
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                }
            }
            task_id = redis_client.queue_pending_task(task_data)
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  f"Recruiter message generated and queued for approval")
            
        elif classification.category == "cofounder":
            message = self.generate_cofounder_message(profile_data)
            result["message"] = message
            result["action"] = "send_message"
            
            # Queue for frontend approval
            name = profile_data.get("name", "LinkedIn User")
            task_data = {
                "type": "message",
                "content": message,
                "url": profile_url,
                "name": name,
                "agent_name": "Messaging Agent",
                "agent_emoji": "💬",
                "metadata": {
                    "action": "send_message",
                    "classification": "cofounder",
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                }
            }
            task_id = redis_client.queue_pending_task(task_data)
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  f"Co-founder message generated and queued for approval")
            
        elif classification.category == "waterloo_student":
            # Route to dating agent (will be handled by orchestration)
            result["action"] = "route_to_dating_agent"
            result["message"] = None
            
            feedback.task_completed("profile_processing", profile_url, 
                                  "Routed to Dating Agent")
            
        else:
            # Just connect, no message
            result["action"] = "connect_only"
            result["message"] = None
            
            # Queue for frontend approval (even connect-only tasks need approval)
            name = profile_data.get("name", "LinkedIn User")
            task_data = {
                "type": "message",
                "content": "",
                "url": profile_url,
                "name": name,
                "agent_name": "Messaging Agent",
                "agent_emoji": "💬",
                "metadata": {
                    "action": "connect_only",
                    "classification": "other",
                    "confidence": classification.confidence,
                    "reasoning": classification.reasoning
                }
            }
            task_id = redis_client.queue_pending_task(task_data)
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  "Connection request queued for approval")
        
        return result


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = MessagingAgent()
    
    # Test profile
    test_profile = {
        "url": "https://linkedin.com/in/test",
        "bio": "Talent Acquisition Specialist at Google. Helping connect great talent with amazing opportunities.",
        "experience": "Talent Acquisition at Google, Recruiter at Microsoft",
        "education": "University of Toronto"
    }
    
    print("Testing Messaging Agent...")
    result = agent.process_profile(test_profile["url"], test_profile)
    print(f"\n✅ Profile processed: {result}")

