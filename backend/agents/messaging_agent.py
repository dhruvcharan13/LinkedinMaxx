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
        self.llm = ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-pro"),
            temperature=0.7
        )
        self.output_parser = JsonOutputParser(pydantic_object=ProfileClassification)
        self._setup_prompts()
    
    def _setup_prompts(self):
        """Set up prompt templates."""
        # Classification prompt
        self.classification_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at analyzing LinkedIn profiles. 
Classify profiles into these categories:
1. "recruiter" - Someone who recruits talent (Talent Acquisition, Recruiter, HR)
2. "cofounder" - Co-founder or Founder of a company
3. "waterloo_student" - Current or recent Waterloo student (University of Waterloo)
4. "other" - Doesn't fit the above categories

Return JSON with category, confidence (0-1), and reasoning."""),
            ("human", """Analyze this LinkedIn profile:

Bio: {bio}
Experience: {experience}
Education: {education}

Classify this profile.""")
        ])
        
        # Message generation prompts
        self.recruiter_message_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Waterloo student reaching out to a recruiter.
Write a professional, friendly message asking about internship opportunities.
Keep it concise (2-3 sentences), mention you're a Waterloo student, and express genuine interest."""),
            ("human", "Write a LinkedIn message for this recruiter profile:\n{bio}")
        ])
        
        self.cofounder_message_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a Waterloo student reaching out to a co-founder/founder.
Write an engaging message about collaboration, startup interest, or potential partnership.
Be authentic, show you've looked at their profile, and express genuine curiosity about their work."""),
            ("human", "Write a LinkedIn message for this founder profile:\n{bio}\nExperience: {experience}")
        ])
    
    def classify_profile(self, profile_data: Dict[str, Any]) -> ProfileClassification:
        """
        Classify a LinkedIn profile into a category.
        
        Args:
            profile_data: Dictionary with profile information (bio, experience, education)
            
        Returns:
            ProfileClassification object
        """
        feedback.agent_action("Messaging Agent", "Classifying profile...")
        
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
        
        Args:
            profile_url: URL of the LinkedIn profile
            profile_data: Profile information (bio, experience, education)
            
        Returns:
            Dictionary with processing result
        """
        feedback.task_processing("profile_processing", profile_url)
        
        # Classify profile
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
            
            # Publish message instruction
            task_id = redis_client.queue_message_instruction(profile_url, message, "send_message")
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  f"Recruiter message generated and queued")
            
        elif classification.category == "cofounder":
            message = self.generate_cofounder_message(profile_data)
            result["message"] = message
            result["action"] = "send_message"
            
            # Publish message instruction
            task_id = redis_client.queue_message_instruction(profile_url, message, "send_message")
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  f"Co-founder message generated and queued")
            
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
            
            # Publish connection instruction
            task_id = redis_client.queue_message_instruction(profile_url, "", "connect_only")
            result["task_id"] = task_id
            
            feedback.task_completed("profile_processing", profile_url, 
                                  "Connection request queued (no message)")
        
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

