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
    
    def queue_message_instruction(self, profile_url: str, message: str, action: str = "send_message", name: str = None):
        """Queue a message instruction for Playwright.
        
        Format matches test_profile.json: {"profile_url": "...", "name": "...", "message": "..."}
        """
        queue_name = "playwright:message"
        instruction = {
            "profile_url": profile_url,
            "name": name or "LinkedIn User",  # Default name if not provided
            "message": message,
            "action": action,  # "send_message" or "connect_only"
            "timestamp": datetime.now().isoformat()
        }
        return self.publish_instruction(queue_name, instruction)
    
    def queue_comment_instruction(self, post_url: str, comment_text: str):
        """Queue a comment instruction for Playwright.
        
        Format: {"post_url": "...", "comment": "..."}
        """
        queue_name = "playwright:comment"
        instruction = {
            "post_url": post_url,
            "comment": comment_text,
            "timestamp": datetime.now().isoformat()
        }
        return self.publish_instruction(queue_name, instruction)
    
    def queue_pending_task(self, task_data: Dict[str, Any]) -> str:
        """Queue a task for frontend approval.
        
        Args:
            task_data: Task data including type, content, url, name, etc.
            
        Returns:
            Task ID
        """
        queue_name = "tasks:pending_approval"
        task_id = f"{queue_name}:{datetime.now().isoformat()}"
        
        task = {
            "task_id": task_id,
            "type": task_data.get("type"),  # "post", "message", "comment"
            "content": task_data.get("content"),  # Message text, post text, comment text
            "url": task_data.get("url"),  # Profile URL or post URL
            "name": task_data.get("name"),  # Person name
            "agent_name": task_data.get("agent_name", "Unknown Agent"),
            "agent_emoji": task_data.get("agent_emoji", "🤖"),
            "metadata": task_data.get("metadata", {}),  # Confidence, classification, etc.
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        
        if not self.client:
            self._connect()
        if not self.client:
            raise RuntimeError(f"Redis client not connected. Start Redis with: docker run -d -p 6379:6379 redis:alpine")
        
        # Publish to Redis queue
        self.client.lpush(queue_name, json.dumps(task))
        
        # Also store in a hash for retrieval
        self.client.hset(f"{queue_name}:tasks", task_id, json.dumps(task))
        
        logger.info(f"Queued pending task: {task_id}")
        feedback.data_published(queue_name, "pending_task", task)
        return task_id
    
    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks for frontend approval.
        
        Returns:
            List of pending tasks
        """
        if not self.client:
            self._connect()
        if not self.client:
            return []
        
        queue_name = "tasks:pending_approval"
        # Get all tasks from the queue (without popping)
        tasks = []
        queue_length = self.client.llen(queue_name)
        
        if queue_length > 0:
            # Get all items from the queue
            items = self.client.lrange(queue_name, 0, -1)
            for item in items:
                try:
                    task = json.loads(item)
                    if task.get("status") == "pending":
                        tasks.append(task)
                except json.JSONDecodeError:
                    continue
        
        return tasks
    
    def approve_task(self, task_id: str, edited_content: Optional[str] = None) -> bool:
        """Approve a task and move it to execution queue.
        
        Args:
            task_id: Task ID to approve
            edited_content: Optional edited content
            
        Returns:
            True if approved successfully
        """
        if not self.client:
            self._connect()
        if not self.client:
            return False
        
        queue_name = "tasks:pending_approval"
        
        # Get task from hash
        task_json = self.client.hget(f"{queue_name}:tasks", task_id)
        if not task_json:
            return False
        
        task = json.loads(task_json)
        
        # Update content if edited
        if edited_content:
            task["content"] = edited_content
        
        # Update status
        task["status"] = "approved"
        task["approved_at"] = datetime.now().isoformat()
        
        # Update in hash
        self.client.hset(f"{queue_name}:tasks", task_id, json.dumps(task))
        
        # Publish to execution queue based on type
        task_type = task.get("type")
        content = edited_content or task.get("content", "")
        url = task.get("url", "")
        name = task.get("name", "LinkedIn User")
        
        if task_type == "post":
            # Publish to playwright:post
            self.queue_post_instruction(content, task.get("metadata", {}))
        elif task_type == "message":
            # Publish to playwright:message
            action = task.get("metadata", {}).get("action", "send_message")
            self.queue_message_instruction(url, content, action, name)
        elif task_type == "comment":
            # Publish to playwright:comment
            self.queue_comment_instruction(url, content)
        
        # Remove from pending queue (find and remove)
        items = self.client.lrange(queue_name, 0, -1)
        for item in items:
            try:
                item_task = json.loads(item)
                if item_task.get("task_id") == task_id:
                    self.client.lrem(queue_name, 1, item)
                    break
            except json.JSONDecodeError:
                continue
        
        logger.info(f"Approved task: {task_id}")
        return True
    
    def reject_task(self, task_id: str) -> bool:
        """Reject a task.
        
        Args:
            task_id: Task ID to reject
            
        Returns:
            True if rejected successfully
        """
        if not self.client:
            self._connect()
        if not self.client:
            return False
        
        queue_name = "tasks:pending_approval"
        
        # Get task from hash
        task_json = self.client.hget(f"{queue_name}:tasks", task_id)
        if not task_json:
            return False
        
        task = json.loads(task_json)
        task["status"] = "rejected"
        task["rejected_at"] = datetime.now().isoformat()
        
        # Update in hash
        self.client.hset(f"{queue_name}:tasks", task_id, json.dumps(task))
        
        # Remove from pending queue
        items = self.client.lrange(queue_name, 0, -1)
        for item in items:
            try:
                item_task = json.loads(item)
                if item_task.get("task_id") == task_id:
                    self.client.lrem(queue_name, 1, item)
                    break
            except json.JSONDecodeError:
                continue
        
        logger.info(f"Rejected task: {task_id}")
        return True
    
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

