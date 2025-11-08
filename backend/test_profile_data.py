"""
Test script with real profile data format from Playwright scraping.
Tests the full agent pipeline with a Waterloo student profile.
"""

import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()

from utils.logger import feedback, logger
from utils.redis_client import redis_client
from agents.messaging_agent import MessagingAgent
from agents.dating_agent import DatingAgent

# Test profile data (from Playwright scraping)
test_profile = {
    "url": "https://www.linkedin.com/in/elrich-chen/",
    "scraped_at": "2025-11-08T16:47:09.871850",
    "name": "Elrich Chen",
    "headline": "CS @ UWaterloo | AI automations for DoneMaker | Aspiring Backend Engineer 💻☁️",
    "location": "He/Him",
    "bio": "📧 eklchen@uwaterloo.ca for connecting with me (or send a connection req) :)\n\nMy story: 🌎\n\nI'm one who identifies strongly with change. To keep it short, I grew up in India for 18 years before moving back to my citizen home Canada, to pursue CS at Queen's University (Kingston). Unbenowkst to me I would feel the need for a higher level of challenge, so I then transferred to the University of Waterloo's highly esteemed CS program. Now I find myself as a learner in backend development, while also seizing every opportunity on campus for more involvement and leadership.\n\nAlways open to meeting people who care about debating ideas, building, connecting, and pushing boundaries.\n\nSkills snapshot (for the recruiters): product development, user research, product roadmapping, agile methodologies, data analysis, technical writing, stakeholder communication, UX/UI design, software development life cycle (SDLC), business analysis, process improvement, programming (Python, TypeScript, React, Flask), project management, leadership, and cross-functional collaboration.",
    "experience": [
        {
            "title": "AI automation",
            "company": "AI automation",
            "location": "DoneMaker · Internship"
        },
        {
            "title": "Logistics Organizer",
            "company": "Logistics Organizer",
            "location": "Tech+ UW"
        },
        {
            "title": "Residence Counsellor for DEEP, BLUEPRINT, CREATE engineering",
            "company": "Residence Counsellor for DEEP, BLUEPRINT, CREATE engineering",
            "location": "University of Toronto · Contract Full-time"
        },
        {
            "title": "Product Developer",
            "company": "Product Developer",
            "location": "Queen's Technology & Media Association (QTMA) · Internship"
        }
    ],
    "education": [
        {
            "school": "University of Waterloo",
            "degree": "University of Waterloo"
        },
        {
            "school": "Transferred into 2A term.",
            "degree": "Transferred into 2A term."
        },
        {
            "school": "Queen's University",
            "degree": "Queen's University"
        },
        {
            "school": "Grade: Accumulated GPA - 4.3/4.3",
            "degree": "Grade: Accumulated GPA - 4.3/4.3"
        }
    ]
}


def format_profile_for_agents(profile_data):
    """Convert Playwright scraped format to agent-friendly format."""
    # Extract bio
    bio = profile_data.get("bio", "")
    if not bio and profile_data.get("headline"):
        bio = profile_data.get("headline", "")
    
    # Format experience
    experience_list = profile_data.get("experience", [])
    experience_text = []
    for exp in experience_list:
        if isinstance(exp, dict):
            title = exp.get("title", "")
            company = exp.get("company", "")
            location = exp.get("location", "")
            if title and company:
                exp_str = f"{title} at {company}"
                if location:
                    exp_str += f" ({location})"
                experience_text.append(exp_str)
    
    experience = "\n".join(experience_text) if experience_text else "Not available"
    
    # Format education
    education_list = profile_data.get("education", [])
    education_text = []
    for edu in education_list:
        if isinstance(edu, dict):
            school = edu.get("school", "")
            degree = edu.get("degree", "")
            if school and school not in education_text:
                education_text.append(school)
            elif degree and degree not in education_text:
                education_text.append(degree)
    
    education = "\n".join(education_text) if education_text else "Not available"
    
    return {
        "url": profile_data.get("url", ""),
        "bio": bio,
        "experience": experience,
        "education": education,
        "name": profile_data.get("name", ""),
        "headline": profile_data.get("headline", "")
    }


def test_messaging_agent():
    """Test messaging agent with the profile."""
    print("\n" + "="*70)
    print("TEST 1: Messaging Agent - Profile Classification")
    print("="*70)
    
    try:
        agent = MessagingAgent()
        formatted_profile = format_profile_for_agents(test_profile)
        
        print(f"\n📋 Profile: {formatted_profile['name']}")
        print(f"🔗 URL: {formatted_profile['url']}")
        print(f"📝 Headline: {formatted_profile['headline']}")
        print(f"\n📄 Bio (first 200 chars): {formatted_profile['bio'][:200]}...")
        print(f"\n💼 Experience: {formatted_profile['experience'][:150]}...")
        print(f"\n🎓 Education: {formatted_profile['education']}")
        
        result = agent.process_profile(formatted_profile["url"], formatted_profile)
        
        print(f"\n✅ Classification Result:")
        print(f"   Category: {result['classification']['category']}")
        print(f"   Confidence: {result['classification']['confidence']:.2%}")
        print(f"   Reasoning: {result['classification']['reasoning']}")
        print(f"   Action: {result['action']}")
        
        if result.get('message'):
            print(f"\n💬 Generated Message:")
            print(f"   {result['message']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_dating_agent():
    """Test dating agent with the profile."""
    print("\n" + "="*70)
    print("TEST 2: Dating Agent - Waterloo Student Detection & Pickup Line")
    print("="*70)
    
    try:
        agent = DatingAgent(user_stream="1A")
        formatted_profile = format_profile_for_agents(test_profile)
        
        print(f"\n📋 Profile: {formatted_profile['name']}")
        print(f"🔗 URL: {formatted_profile['url']}")
        print(f"👤 User Stream: 1A")
        
        result = agent.process_waterloo_student(formatted_profile["url"], formatted_profile)
        
        print(f"\n✅ Dating Agent Result:")
        print(f"   Is Waterloo Student: {result['is_waterloo']}")
        print(f"   Estimated Stream: {result.get('estimated_stream', 'Unknown')}")
        print(f"   Confidence: {result.get('confidence', 0):.2%}")
        print(f"   Same Stream: {result.get('same_stream', False)}")
        print(f"   Action: {result['action']}")
        
        if result.get('message'):
            print(f"\n💕 Generated Pickup Line:")
            print(f"   {result['message']}")
        
        if result.get('task_id'):
            print(f"\n📤 Task ID: {result['task_id']}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_full_pipeline():
    """Test the full pipeline: Messaging Agent → Dating Agent."""
    print("\n" + "="*70)
    print("TEST 3: Full Pipeline - Messaging → Dating Agent")
    print("="*70)
    
    try:
        messaging_agent = MessagingAgent()
        dating_agent = DatingAgent(user_stream="1A")
        
        formatted_profile = format_profile_for_agents(test_profile)
        
        print(f"\n📋 Processing: {formatted_profile['name']}")
        print(f"🔗 URL: {formatted_profile['url']}")
        
        # Step 1: Messaging Agent classification
        print(f"\n🔍 Step 1: Classifying profile...")
        msg_result = messaging_agent.process_profile(formatted_profile["url"], formatted_profile)
        
        print(f"   ✅ Classified as: {msg_result['classification']['category']}")
        print(f"   ✅ Action: {msg_result['action']}")
        
        # Step 2: If Waterloo student, process with Dating Agent
        if msg_result.get('action') == 'route_to_dating_agent':
            print(f"\n💕 Step 2: Routing to Dating Agent...")
            dating_result = dating_agent.process_waterloo_student(
                formatted_profile["url"], 
                formatted_profile
            )
            
            print(f"   ✅ Is Waterloo: {dating_result['is_waterloo']}")
            print(f"   ✅ Estimated Stream: {dating_result.get('estimated_stream', 'Unknown')}")
            print(f"   ✅ Same Stream: {dating_result.get('same_stream', False)}")
            print(f"   ✅ Final Action: {dating_result['action']}")
            
            if dating_result.get('message'):
                print(f"\n💬 Final Message:")
                print(f"   {dating_result['message']}")
            
            return {
                "messaging": msg_result,
                "dating": dating_result
            }
        else:
            print(f"\n⚠️  Profile not routed to Dating Agent")
            return {
                "messaging": msg_result,
                "dating": None
            }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("LINKEDINMAXX AGENT TESTING - Real Profile Data")
    print("="*70)
    print(f"\n📋 Test Profile: {test_profile['name']}")
    print(f"🔗 URL: {test_profile['url']}")
    print(f"🏫 Education: University of Waterloo (CS)")
    print(f"💼 Headline: {test_profile['headline']}")
    
    # Test 1: Messaging Agent
    msg_result = test_messaging_agent()
    
    # Test 2: Dating Agent (direct)
    dating_result = test_dating_agent()
    
    # Test 3: Full Pipeline
    pipeline_result = test_full_pipeline()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if msg_result:
        print(f"✅ Messaging Agent: {msg_result['classification']['category']}")
    
    if dating_result:
        print(f"✅ Dating Agent: {'Waterloo Student' if dating_result['is_waterloo'] else 'Not Waterloo'}")
        if dating_result.get('estimated_stream'):
            print(f"   Stream: {dating_result['estimated_stream']}")
        if dating_result.get('same_stream'):
            print(f"   Same Stream: ✅")
            if dating_result.get('message'):
                print(f"   Pickup Line Generated: ✅")
    
    if pipeline_result:
        print(f"✅ Full Pipeline: Completed")
    
    print("\n" + "="*70)
    print("🎉 Testing Complete!")
    print("="*70)


if __name__ == "__main__":
    main()

