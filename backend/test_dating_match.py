"""
Test script for dating agent with sample profile data.
Assumes the profile matches the user's stream and generates a pickup line.
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

from utils.logger import feedback, logger
from utils.redis_client import redis_client
from agents.dating_agent import DatingAgent

# Sample profile data (from user)
test_profile = {
    "url": "https://www.linkedin.com/in/elrich-chen/",
    "scraped_at": "2025-11-08T16:47:09.871850",
    "name": "Elrich Chen",
    "headline": "CS @ UWaterloo | AI automations for DoneMaker | Aspiring Backend Engineer 💻☁️",
    "location": "He/Him",
    "type": "waterloo",  # Pre-classified by Patchright
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


def format_profile_for_agent(profile_data):
    """Convert profile data to agent-friendly format."""
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
        "headline": profile_data.get("headline", ""),
        "type": profile_data.get("type", "")
    }


def test_dating_match():
    """Test dating agent with sample profile, assuming it matches user's stream."""
    print("\n" + "="*80)
    print("🧪 TESTING DATING AGENT - SAMPLE PROFILE (ASSUMING STREAM MATCH)")
    print("="*80)
    
    # Force user stream to match - profile mentions "2A term", so set to "2A"
    # This ensures we get a match and generate a pickup line
    user_stream = "2A"  # Match the "Transferred into 2A term" in profile
    print(f"\n👤 User Stream: {user_stream} (set to match profile)")
    print(f"📋 Profile: {test_profile['name']}")
    print(f"🔗 URL: {test_profile['url']}")
    print(f"🏫 Education: {test_profile['education'][0]['school']}")
    print(f"💼 Headline: {test_profile['headline']}")
    print(f"📝 Note: Profile mentions '2A term', so setting user stream to 2A for match")
    
    try:
        # Initialize dating agent
        print(f"\n🚀 Initializing Dating Agent...")
        agent = DatingAgent(user_stream=user_stream)
        
        # Format profile for agent
        formatted_profile = format_profile_for_agent(test_profile)
        
        print(f"\n📝 Processing profile through Dating Agent...")
        print(f"   Bio preview: {formatted_profile['bio'][:150]}...")
        print(f"   Experience: {formatted_profile['experience'][:100]}...")
        
        # Process profile
        result = agent.process_waterloo_student(
            formatted_profile["url"], 
            formatted_profile
        )
        
        # Display results
        print("\n" + "="*80)
        print("✅ PROCESSING RESULTS")
        print("="*80)
        
        print(f"\n🏫 Is Waterloo Student: {'✅ Yes' if result['is_waterloo'] else '❌ No'}")
        print(f"📊 Estimated Stream: {result.get('estimated_stream', 'Unknown')}")
        print(f"👤 User Stream: {result.get('user_stream', 'Unknown')}")
        print(f"🎯 Same Stream: {'✅ YES' if result.get('same_stream', False) else '❌ No'}")
        print(f"💯 Confidence: {result.get('confidence', 0):.2%}")
        print(f"🎬 Action: {result.get('action', 'unknown')}")
        
        # Show message if generated
        if result.get('message'):
            print("\n" + "="*80)
            print("💕 GENERATED PICKUP LINE")
            print("="*80)
            print(f"\n{result['message']}\n")
        
        # Show Redis status
        print("="*80)
        print("📤 REDIS PUBLICATION")
        print("="*80)
        
        if result.get('task_id'):
            print(f"✅ Task ID: {result['task_id']}")
            print(f"✅ Message published to Redis queue: playwright:message")
            
            # Check Redis queue length
            if redis_client and redis_client.is_connected():
                queue_length = redis_client.get_queue_length("playwright:message")
                print(f"✅ Queue length: {queue_length} message(s)")
                
                # Show what was published
                print(f"\n📋 Published Instruction:")
                print(f"   Action: {result.get('action')}")
                print(f"   Profile URL: {result.get('profile_url')}")
                if result.get('message'):
                    print(f"   Message: {result['message'][:100]}...")
            else:
                print("⚠️  Redis not connected (message would be published when Redis is available)")
        else:
            print("⚠️  No task ID (message not published)")
        
        print("\n" + "="*80)
        print("🎉 TEST COMPLETE!")
        print("="*80)
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Check Redis connection
    print("\n🔍 Checking Redis connection...")
    if redis_client and redis_client.is_connected():
        print("✅ Redis connected")
    else:
        print("⚠️  Redis not connected - messages will be queued when Redis is available")
    
    # Run test
    result = test_dating_match()
    
    # Summary
    if result:
        print(f"\n📊 SUMMARY:")
        print(f"   Profile: {test_profile['name']}")
        print(f"   Waterloo Student: {'✅' if result['is_waterloo'] else '❌'}")
        print(f"   Estimated Stream: {result.get('estimated_stream', 'Unknown')}")
        print(f"   Same Stream: {'✅' if result.get('same_stream', False) else '❌'}")
        print(f"   Message Generated: {'✅' if result.get('message') else '❌'}")
        print(f"   Published to Redis: {'✅' if result.get('task_id') else '❌'}")

