"""
Test script for LinkedInMaxx agents.
Tests each agent individually with sample data.
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from utils.logger import feedback, logger
from utils.redis_client import redis_client
from agents.daily_post_agent import DailyPostAgent
from agents.messaging_agent import MessagingAgent
from agents.dating_agent import DatingAgent


def test_redis_connection():
    """Test Redis connection."""
    print("\n" + "="*60)
    print("TEST 1: Redis Connection")
    print("="*60)
    try:
        if redis_client.is_connected():
            print("✅ Redis connected successfully")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False


def test_daily_post_agent():
    """Test Daily Post Agent."""
    print("\n" + "="*60)
    print("TEST 2: Daily Post Agent")
    print("="*60)
    try:
        agent = DailyPostAgent()
        
        # Test post generation
        context = "Just finished building an AI agent system for LinkedIn automation at a hackathon!"
        result = agent.generate_post(context)
        
        print(f"✅ Post generated: {len(result['content'])} characters")
        print(f"\nGenerated Post:\n{result['content']}\n")
        
        # Test publishing (this will publish to Redis)
        task_id = agent.publish_post(result['content'], result['metadata'])
        print(f"✅ Post published to queue with task ID: {task_id}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_messaging_agent():
    """Test Messaging Agent."""
    print("\n" + "="*60)
    print("TEST 3: Messaging Agent - Classification")
    print("="*60)
    try:
        agent = MessagingAgent()
        
        # Test recruiter profile
        recruiter_profile = {
            "url": "https://linkedin.com/in/test-recruiter",
            "bio": "Talent Acquisition Specialist at Google. Helping connect great talent with amazing opportunities.",
            "experience": "Talent Acquisition at Google (2020-present), Recruiter at Microsoft (2018-2020)",
            "education": "University of Toronto - Human Resources"
        }
        
        result = agent.process_profile(recruiter_profile["url"], recruiter_profile)
        print(f"✅ Profile classified as: {result['classification']['category']}")
        print(f"✅ Action: {result['action']}")
        if result.get('message'):
            print(f"✅ Message generated: {result['message'][:100]}...")
        
        # Test co-founder profile
        print("\n" + "-"*60)
        cofounder_profile = {
            "url": "https://linkedin.com/in/test-cofounder",
            "bio": "Co-founder and CEO at TechStartup. Building the future of AI.",
            "experience": "Co-founder at TechStartup (2022-present), Software Engineer at Amazon (2020-2022)",
            "education": "Stanford University - Computer Science"
        }
        
        result = agent.process_profile(cofounder_profile["url"], cofounder_profile)
        print(f"✅ Profile classified as: {result['classification']['category']}")
        print(f"✅ Action: {result['action']}")
        if result.get('message'):
            print(f"✅ Message generated: {result['message'][:100]}...")
        
        # Test Waterloo student profile
        print("\n" + "-"*60)
        waterloo_profile = {
            "url": "https://linkedin.com/in/test-waterloo",
            "bio": "Software Engineering student at University of Waterloo | Co-op at Google",
            "experience": "Software Engineering Intern at Google (Fall 2024), Software Developer at Shopify (Spring 2024)",
            "education": "University of Waterloo - Software Engineering"
        }
        
        result = agent.process_profile(waterloo_profile["url"], waterloo_profile)
        print(f"✅ Profile classified as: {result['classification']['category']}")
        print(f"✅ Action: {result['action']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dating_agent():
    """Test Dating Agent."""
    print("\n" + "="*60)
    print("TEST 4: Dating Agent")
    print("="*60)
    try:
        agent = DatingAgent(user_stream="1A")
        
        # Test Waterloo student in same stream
        waterloo_profile = {
            "url": "https://linkedin.com/in/test-waterloo-1a",
            "bio": "Software Engineering student at University of Waterloo | Co-op at Google | Stream 1A",
            "experience": "Software Engineering Intern at Google (Fall 2024), Software Developer at Shopify (Spring 2024)",
            "education": "University of Waterloo - Software Engineering"
        }
        
        result = agent.process_waterloo_student(waterloo_profile["url"], waterloo_profile)
        print(f"✅ Is Waterloo: {result['is_waterloo']}")
        print(f"✅ Estimated stream: {result['estimated_stream']}")
        print(f"✅ Same stream: {result.get('same_stream', False)}")
        print(f"✅ Action: {result['action']}")
        if result.get('message'):
            print(f"✅ Pickup line: {result['message']}")
        
        # Test Waterloo student in different stream
        print("\n" + "-"*60)
        waterloo_profile_2b = {
            "url": "https://linkedin.com/in/test-waterloo-2b",
            "bio": "Computer Science student at University of Waterloo | Co-op at Microsoft",
            "experience": "Software Engineering Intern at Microsoft (Summer 2024), Software Developer at Amazon (Fall 2023)",
            "education": "University of Waterloo - Computer Science"
        }
        
        result = agent.process_waterloo_student(waterloo_profile_2b["url"], waterloo_profile_2b)
        print(f"✅ Is Waterloo: {result['is_waterloo']}")
        print(f"✅ Estimated stream: {result['estimated_stream']}")
        print(f"✅ Same stream: {result.get('same_stream', False)}")
        print(f"✅ Action: {result['action']}")
        
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_workflow():
    """Test full workflow: Post → Profile → Messaging → Dating."""
    print("\n" + "="*60)
    print("TEST 5: Full Workflow")
    print("="*60)
    try:
        # 1. Generate daily post
        print("\n1. Generating daily post...")
        post_agent = DailyPostAgent()
        post_result = post_agent.generate_and_publish("Hackathon project: LinkedInMaxx automation system")
        print(f"✅ Daily post published: {post_result}")
        
        # 2. Process Waterloo student profile
        print("\n2. Processing Waterloo student profile...")
        messaging_agent = MessagingAgent()
        dating_agent = DatingAgent(user_stream="1A")
        
        profile = {
            "url": "https://linkedin.com/in/test-full-workflow",
            "bio": "Software Engineering student at University of Waterloo | Stream 1A",
            "experience": "Co-op at Google (Fall 2024), Intern at Shopify (Spring 2024)",
            "education": "University of Waterloo - Software Engineering"
        }
        
        # Classify
        msg_result = messaging_agent.process_profile(profile["url"], profile)
        print(f"✅ Classified as: {msg_result['classification']['category']}")
        
        # If Waterloo student, process with dating agent
        if msg_result.get('action') == 'route_to_dating_agent':
            dating_result = dating_agent.process_waterloo_student(profile["url"], profile)
            print(f"✅ Dating agent processed: {dating_result['action']}")
            if dating_result.get('message'):
                print(f"✅ Pickup line: {dating_result['message']}")
        
        print("\n✅ Full workflow test completed!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LINKEDINMAXX AGENT TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Redis Connection", test_redis_connection()))
    results.append(("Daily Post Agent", test_daily_post_agent()))
    results.append(("Messaging Agent", test_messaging_agent()))
    results.append(("Dating Agent", test_dating_agent()))
    results.append(("Full Workflow", test_full_workflow()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️  Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()

