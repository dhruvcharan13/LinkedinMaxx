"""
Redis client for Playwright to consume and publish tasks.
Handles communication with backend agents via Redis queues.
"""

import redis
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class PlaywrightRedisClient:
    """Redis client for Playwright automation."""
    
    def __init__(self):
        """Initialize Redis client."""
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            print(f"✅ Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print(f"   Make sure Redis is running: docker run -d -p 6379:6379 redis:alpine")
            raise
    
    def get_post_instruction(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get next post instruction from queue (blocking).
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking, returns immediately)
            
        Returns:
            Instruction dict or None if timeout or no tasks
        """
        try:
            if timeout == 0:
                # Non-blocking: use RPOP instead of BRPOP
                instruction_json = self.client.rpop("playwright:post")
                if instruction_json:
                    data = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in data:
                        return data["instruction"]
                    return data
                return None
            else:
                # Blocking: use BRPOP with timeout
                data = self.client.brpop("playwright:post", timeout=timeout)
                if data:
                    _, instruction_json = data
                    parsed = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in parsed:
                        return parsed["instruction"]
                    return parsed
                return None
        except redis.TimeoutError:
            return None
        except Exception as e:
            print(f"⚠️  Error getting post instruction: {e}")
            return None
    
    def get_message_instruction(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get next message instruction from queue (blocking).
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking, returns immediately)
            
        Returns:
            Instruction dict or None if timeout or no tasks
        """
        try:
            if timeout == 0:
                # Non-blocking: use RPOP instead of BRPOP
                instruction_json = self.client.rpop("playwright:message")
                if instruction_json:
                    data = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in data:
                        return data["instruction"]
                    return data
                return None
            else:
                # Blocking: use BRPOP with timeout
                data = self.client.brpop("playwright:message", timeout=timeout)
                if data:
                    _, instruction_json = data
                    parsed = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in parsed:
                        return parsed["instruction"]
                    return parsed
                return None
        except redis.TimeoutError:
            return None
        except Exception as e:
            print(f"⚠️  Error getting message instruction: {e}")
            return None
    
    def get_comment_instruction(self, timeout: int = 1) -> Optional[Dict[str, Any]]:
        """
        Get next comment instruction from queue (blocking).
        
        Args:
            timeout: Timeout in seconds (0 = non-blocking, returns immediately)
            
        Returns:
            Instruction dict or None if timeout or no tasks
        """
        try:
            if timeout == 0:
                # Non-blocking: use RPOP instead of BRPOP
                instruction_json = self.client.rpop("playwright:comment")
                if instruction_json:
                    data = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in data:
                        return data["instruction"]
                    return data
                return None
            else:
                # Blocking: use BRPOP with timeout
                data = self.client.brpop("playwright:comment", timeout=timeout)
                if data:
                    _, instruction_json = data
                    parsed = json.loads(instruction_json)
                    # Backend wraps instruction in a structure, extract the actual instruction
                    if "instruction" in parsed:
                        return parsed["instruction"]
                    return parsed
                return None
        except redis.TimeoutError:
            return None
        except Exception as e:
            print(f"⚠️  Error getting comment instruction: {e}")
            return None
    
    def publish_scraped_profile(self, profile_url: str, profile_data: Dict[str, Any]):
        """
        Publish scraped profile to Redis queue for backend agents.
        
        Args:
            profile_url: LinkedIn profile URL
            profile_data: Profile data dictionary (must include 'type' field)
        """
        try:
            # Wrap in the format expected by backend workflow
            task_id = f"profiles:scraped:{datetime.now().isoformat()}"
            instruction_data = {
                "task_id": task_id,
                "queue": "profiles:scraped",
                "instruction": {
                    "profile_url": profile_url,
                    "profile_data": profile_data,
                    "timestamp": datetime.now().isoformat()
                },
                "status": "pending"
            }
            self.client.lpush("profiles:scraped", json.dumps(instruction_data))
            print(f"📤 Published scraped profile: {profile_data.get('name', 'Unknown')} ({profile_data.get('type', 'unknown')})")
        except Exception as e:
            print(f"⚠️  Error publishing scraped profile: {e}")
    
    def publish_scraped_post(self, post_url: str, post_data: Dict[str, Any]):
        """
        Publish scraped post to Redis queue for backend agents.
        
        Args:
            post_url: LinkedIn post URL
            post_data: Post data dictionary
        """
        try:
            # Wrap in the format expected by backend workflow
            task_id = f"posts:scraped:{datetime.now().isoformat()}"
            instruction_data = {
                "task_id": task_id,
                "queue": "posts:scraped",
                "instruction": {
                    "post_url": post_url,
                    "post_data": post_data,
                    "timestamp": datetime.now().isoformat()
                },
                "status": "pending"
            }
            self.client.lpush("posts:scraped", json.dumps(instruction_data))
            print(f"📤 Published scraped post: {post_data.get('author', 'Unknown')}")
        except Exception as e:
            print(f"⚠️  Error publishing scraped post: {e}")
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            self.client.ping()
            return True
        except:
            return False


