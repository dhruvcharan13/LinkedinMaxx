"""
Redis client for task queues and agent memory.
Handles publishing instructions for Playwright and storing agent state.
"""

import redis
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv
from utils.logger import feedback, logger

load_dotenv()


class RedisClient:
    """Redis client for LinkedInMaxx backend."""
    
    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "localhost")
        self.port = int(os.getenv("REDIS_PORT", 6379))
        self.db = int(os.getenv("REDIS_DB", 0))
        self.client: Optional[redis.Redis] = None
        self._connect()
    
    def _connect(self):
        """Connect to Redis server."""
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
            logger.info(f"✅ Connected to Redis at {self.host}:{self.port}")
            feedback.agent_action("Redis", f"Connected to {self.host}:{self.port}")
        except (redis.ConnectionError, ConnectionRefusedError) as e:
            logger.warning(f"⚠️  Redis not available at {self.host}:{self.port} - {e}")
            logger.warning("Redis will retry connection when used. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
            self.client = None
            # Don't raise - allow lazy connection
    
    def publish_instruction(self, queue_name: str, instruction: Dict[str, Any]) -> str:
        """
        Publish instruction for Playwright to consume.
        
        Args:
            queue_name: Name of the queue (e.g., 'playwright:post', 'playwright:message')
            instruction: Instruction data to publish
            
        Returns:
            Task ID
        """
        if not self.client:
            self._connect()
        if not self.client:
            raise RuntimeError(f"Redis client not connected. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        
        task_id = f"{queue_name}:{datetime.now().isoformat()}"
        instruction_data = {
            "task_id": task_id,
            "queue": queue_name,
            "instruction": instruction,
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        # Publish to Redis queue
        self.client.lpush(queue_name, json.dumps(instruction_data))
        
        # Also store in a hash for retrieval
        self.client.hset(f"{queue_name}:tasks", task_id, json.dumps(instruction_data))
        
        # Display feedback
        feedback.data_published(queue_name, instruction.get("action", "instruction"), instruction)
        feedback.instruction_for_playwright(instruction.get("action", "unknown"), instruction)
        
        logger.info(f"Published instruction to {queue_name}: {task_id}")
        return task_id
    
    def get_instruction(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """
        Get next instruction from queue (blocking pop).
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Instruction data or None if queue is empty
        """
        if not self.client:
            self._connect()
        if not self.client:
            raise RuntimeError(f"Redis client not connected. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        
        # Blocking pop (waits up to 1 second)
        result = self.client.brpop(queue_name, timeout=1)
        if result:
            _, data = result
            instruction = json.loads(data)
            feedback.data_extracted(queue_name, "instruction")
            return instruction
        return None
    
    def set_agent_memory(self, agent_name: str, key: str, value: Any, ttl: Optional[int] = None):
        """Store agent memory in Redis."""
        if not self.client:
            self._connect()
        if not self.client:
            raise RuntimeError(f"Redis client not connected. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        
        memory_key = f"agent:{agent_name}:{key}"
        self.client.set(memory_key, json.dumps(value))
        if ttl:
            self.client.expire(memory_key, ttl)
        
        logger.debug(f"Stored memory for {agent_name}:{key}")
    
    def get_agent_memory(self, agent_name: str, key: str) -> Optional[Any]:
        """Retrieve agent memory from Redis."""
        if not self.client:
            self._connect()
        if not self.client:
            raise RuntimeError(f"Redis client not connected. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        
        memory_key = f"agent:{agent_name}:{key}"
        data = self.client.get(memory_key)
        if data:
            return json.loads(data)
        return None
    
    def queue_profile_for_processing(self, profile_url: str, profile_data: Dict[str, Any]):
        """Queue a scraped profile for messaging agent processing."""
        queue_name = "profiles:scraped"
        instruction = {
            "action": "process_profile",
            "profile_url": profile_url,
            "profile_data": profile_data,
            "timestamp": datetime.now().isoformat()
        }
        return self.publish_instruction(queue_name, instruction)
    
    def queue_post_instruction(self, post_content: str, metadata: Optional[Dict[str, Any]] = None):
        """Queue a post instruction for Playwright."""
        queue_name = "playwright:post"
        instruction = {
            "action": "publish_post",
            "content": post_content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        return self.publish_instruction(queue_name, instruction)
    
    def queue_message_instruction(self, profile_url: str, message: str, action: str = "send_message"):
        """Queue a message instruction for Playwright."""
        queue_name = "playwright:message"
        instruction = {
            "action": action,  # "send_message" or "connect_only"
            "profile_url": profile_url,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        return self.publish_instruction(queue_name, instruction)
    
    def get_queue_length(self, queue_name: str) -> int:
        """Get the length of a queue."""
        if not self.client:
            return 0
        return self.client.llen(queue_name)
    
    def is_connected(self) -> bool:
        """Check if Redis is connected."""
        try:
            if self.client:
                self.client.ping()
                return True
        except:
            pass
        return False


# Global Redis client instance (lazy initialization)
_redis_client_instance = None

def get_redis_client():
    """Get or create Redis client instance."""
    global _redis_client_instance
    if _redis_client_instance is None:
        _redis_client_instance = RedisClient()
    return _redis_client_instance

# Create instance, but allow import even if Redis is down
try:
    redis_client = get_redis_client()
except Exception as e:
    # Allow import to succeed even if Redis is not available
    # Connection will be retried when actually used
    import logging
    logging.warning(f"Redis not available during import: {e}")
    redis_client = None

