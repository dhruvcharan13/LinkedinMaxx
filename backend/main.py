"""
LinkedInMaxx Main Orchestration Service
Coordinates agents and handles the automation workflow.
"""

import asyncio
import signal
import sys
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from utils.logger import feedback, logger
from utils.redis_client import redis_client
from agents.daily_post_agent import DailyPostAgent
from agents.messaging_agent import MessagingAgent
from agents.dating_agent import DatingAgent
from agents.comment_agent import CommentAgent

load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="LinkedInMaxx Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
is_running = False
orchestration_task: Optional[asyncio.Task] = None

# Initialize agents
daily_post_agent = DailyPostAgent()
messaging_agent = MessagingAgent()
dating_agent = DatingAgent(user_stream=os.getenv("USER_STREAM", "1A"))
comment_agent = CommentAgent()


# Request models
class StartScrollingRequest(BaseModel):
    """Request to start scrolling and processing."""
    generate_daily_post: bool = True
    context: Optional[str] = None


class StopScrollingRequest(BaseModel):
    """Request to stop scrolling."""
    pass


class ProfileData(BaseModel):
    """Profile data from scraping."""
    url: str
    bio: Optional[str] = None
    experience: Optional[str] = None
    education: Optional[str] = None
    type: Optional[str] = None  # Pre-classified type from Patchright


class TaskApprovalRequest(BaseModel):
    """Request to approve a task."""
    task_id: str
    edited_content: Optional[str] = None  # Optional edited content


class TaskRejectionRequest(BaseModel):
    """Request to reject a task."""
    task_id: str


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "redis_connected": redis_client.is_connected(),
        "is_running": is_running,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/start-scrolling")
async def start_scrolling(request: StartScrollingRequest):
    """Start the scrolling and processing workflow."""
    global is_running, orchestration_task
    
    if is_running:
        raise HTTPException(status_code=400, detail="Scrolling is already running")
    
    is_running = True
    feedback.agent_action("Orchestrator", "Starting LinkedInMaxx workflow...")
    
    # Start orchestration task
    orchestration_task = asyncio.create_task(orchestrate_workflow(request))
    
    return {
        "status": "started",
        "message": "LinkedInMaxx workflow started",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/stop-scrolling")
async def stop_scrolling():
    """Stop the scrolling and processing workflow."""
    global is_running, orchestration_task
    
    if not is_running:
        raise HTTPException(status_code=400, detail="Scrolling is not running")
    
    is_running = False
    
    if orchestration_task:
        orchestration_task.cancel()
        try:
            await orchestration_task
        except asyncio.CancelledError:
            pass
    
    feedback.agent_action("Orchestrator", "Stopped LinkedInMaxx workflow")
    
    return {
        "status": "stopped",
        "message": "LinkedInMaxx workflow stopped",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/generate-daily-post")
async def generate_daily_post(context: Optional[str] = None):
    """Generate and queue a daily post."""
    try:
        feedback.agent_action("API", "Generating daily post via API...")
        task_id = daily_post_agent.generate_and_publish(context)
        return {
            "status": "success",
            "task_id": task_id,
            "message": "Daily post generated and queued"
        }
    except Exception as e:
        feedback.error("Failed to generate daily post", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/process-profile")
async def process_profile(profile: ProfileData):
    """Process a single profile through the messaging and dating agents."""
    try:
        profile_data = {
            "url": profile.url,
            "bio": profile.bio or "",
            "experience": profile.experience or "",
            "education": profile.education or "",
            "type": profile.type or ""  # Include type from Patchright
        }
        
        # Check if profile has pre-classified type
        profile_type = profile_data.get("type", "").lower()
        
        if profile_type == "waterloo":
            # Skip messaging agent, go directly to dating agent
            dating_result = dating_agent.process_waterloo_student(profile.url, profile_data)
            result = {
                "profile_url": profile.url,
                "classification": {
                    "category": "waterloo_student",
                    "confidence": 1.0,
                    "reasoning": "Pre-classified by Patchright"
                },
                "action": "route_to_dating_agent",
                "dating_agent_result": dating_result,
                "processed_at": datetime.now().isoformat()
            }
        else:
            # Process through messaging agent
            result = messaging_agent.process_profile(profile.url, profile_data)
            
            # If routed to dating agent, process it
            if result.get("action") == "route_to_dating_agent":
                dating_result = dating_agent.process_waterloo_student(profile.url, profile_data)
                result["dating_agent_result"] = dating_result
        
        return {
            "status": "success",
            "result": result
        }
    except Exception as e:
        feedback.error("Failed to process profile", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue-stats")
async def queue_stats():
    """Get queue statistics."""
    return {
        "playwright_post": redis_client.get_queue_length("playwright:post"),
        "playwright_message": redis_client.get_queue_length("playwright:message"),
        "profiles_scraped": redis_client.get_queue_length("profiles:scraped"),
        "pending_approval": redis_client.get_queue_length("tasks:pending_approval"),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/tasks/pending")
async def get_pending_tasks():
    """Get all pending tasks for frontend approval."""
    try:
        tasks = redis_client.get_pending_tasks()
        return {
            "status": "success",
            "tasks": tasks,
            "count": len(tasks),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        feedback.error("Failed to get pending tasks", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/approve")
async def approve_task(request: TaskApprovalRequest):
    """Approve a task and publish it to execution queue."""
    try:
        success = redis_client.approve_task(request.task_id, request.edited_content)
        if success:
            return {
                "status": "success",
                "message": "Task approved and queued for execution",
                "task_id": request.task_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        feedback.error("Failed to approve task", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/reject")
async def reject_task(request: TaskRejectionRequest):
    """Reject a task."""
    try:
        success = redis_client.reject_task(request.task_id)
        if success:
            return {
                "status": "success",
                "message": "Task rejected",
                "task_id": request.task_id,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Task not found")
    except Exception as e:
        feedback.error("Failed to reject task", e)
        raise HTTPException(status_code=500, detail=str(e))


# Orchestration logic
async def orchestrate_workflow(request: StartScrollingRequest):
    """Main orchestration workflow."""
    global is_running
    
    try:
        feedback.agent_action("Orchestrator", "Workflow started", 
                            f"Generate daily post: {request.generate_daily_post}")
        
        # Step 1: Generate daily post (if requested)
        if request.generate_daily_post:
            try:
                feedback.agent_action("Orchestrator", "Step 1: Generating daily post...")
                daily_post_agent.generate_and_publish(request.context)
                await asyncio.sleep(1)  # Brief pause
            except Exception as e:
                feedback.error("Daily post generation failed", e)
                logger.error(f"Error generating daily post: {e}")
        
        # Step 2: Process scraped profiles and posts from queues
        feedback.agent_action("Orchestrator", "Step 2: Starting profile and post processing loop...")
        
        while is_running:
            # Process scraped profiles
            profile_instruction = redis_client.get_instruction("profiles:scraped")
            
            if profile_instruction:
                try:
                    profile_data = profile_instruction.get("instruction", {}).get("profile_data", {})
                    profile_url = profile_instruction.get("instruction", {}).get("profile_url", "")
                    
                    if profile_url and profile_data:
                        profile_name = profile_data.get("name", "Unknown")
                        profile_type = profile_data.get("type", "").lower()
                        feedback.agent_action("Orchestrator", f"Processing profile: {profile_name} ({profile_type or 'unknown'})")
                        
                        try:
                            # Check if profile already has a type from Patchright
                            if profile_type == "waterloo":
                                # Skip messaging agent, go directly to dating agent
                                feedback.agent_action("Orchestrator", f"Profile {profile_name} pre-classified as Waterloo, routing to Dating Agent")
                                # Process with dating agent (this will queue tasks)
                                result = dating_agent.process_waterloo_student(profile_url, profile_data)
                                feedback.agent_action("Orchestrator", f"✅ Dating agent processed {profile_name}: {result.get('action', 'unknown')}")
                                
                            elif profile_type == "recruiter":
                                # Process as recruiter (this will queue tasks)
                                feedback.agent_action("Orchestrator", f"Profile {profile_name} pre-classified as Recruiter, processing with Messaging Agent")
                                result = messaging_agent.process_profile(profile_url, profile_data)
                                feedback.agent_action("Orchestrator", f"✅ Messaging agent processed {profile_name}: {result.get('action', 'unknown')}")
                                
                            elif profile_type in ["cofounder", "co-founder", "founder"]:
                                # Process as co-founder (this will queue tasks)
                                feedback.agent_action("Orchestrator", f"Profile {profile_name} pre-classified as Co-founder, processing with Messaging Agent")
                                result = messaging_agent.process_profile(profile_url, profile_data)
                                feedback.agent_action("Orchestrator", f"✅ Messaging agent processed {profile_name}: {result.get('action', 'unknown')}")
                                
                            else:
                                # Process through messaging agent (will classify if no type)
                                feedback.agent_action("Orchestrator", f"Profile {profile_name} has no pre-classification, processing with Messaging Agent")
                                result = messaging_agent.process_profile(profile_url, profile_data)
                                
                                # If routed to dating agent, process it
                                if result.get("action") == "route_to_dating_agent":
                                    feedback.agent_action("Orchestrator", f"Messaging agent routed {profile_name} to Dating Agent")
                                    dating_result = dating_agent.process_waterloo_student(profile_url, profile_data)
                                    result["dating_agent_result"] = dating_result
                                    feedback.agent_action("Orchestrator", f"✅ Dating agent processed {profile_name}: {dating_result.get('action', 'unknown')}")
                                else:
                                    feedback.agent_action("Orchestrator", f"✅ Messaging agent processed {profile_name}: {result.get('action', 'unknown')}")
                            
                            # Log the result (including task_id if one was created)
                            task_id = result.get("task_id") or result.get("dating_agent_result", {}).get("task_id")
                            if task_id:
                                logger.info(f"✅ Profile {profile_name} processed successfully. Task ID: {task_id}")
                            else:
                                logger.info(f"✅ Profile {profile_name} processed: {result.get('action', 'unknown')} (no task queued)")
                                
                        except Exception as e:
                            feedback.error(f"Error processing profile {profile_name}", e)
                            logger.error(f"Error processing profile {profile_url}: {e}")
                            import traceback
                            logger.error(traceback.format_exc())
                    
                except Exception as e:
                    feedback.error("Error processing profile", e)
                    logger.error(f"Error processing profile: {e}")
            
            # Process scraped posts for comments
            post_instruction = redis_client.get_instruction("posts:scraped")
            
            if post_instruction:
                try:
                    post_data = post_instruction.get("instruction", {}).get("post_data", {})
                    post_url = post_instruction.get("instruction", {}).get("post_url", "")
                    
                    if post_url and post_data:
                        feedback.agent_action("Orchestrator", f"Processing post: {post_url[:50]}...")
                        
                        # Process post with comment agent
                        result = comment_agent.process_post(post_url, post_data)
                        
                        logger.info(f"Post processed: {result}")
                    
                except Exception as e:
                    feedback.error("Error processing post", e)
                    logger.error(f"Error processing post: {e}")
            
            # Brief sleep to avoid tight loop
            await asyncio.sleep(0.5)
        
        feedback.agent_action("Orchestrator", "Workflow stopped")
        
    except asyncio.CancelledError:
        feedback.agent_action("Orchestrator", "Workflow cancelled")
        is_running = False
    except Exception as e:
        feedback.error("Workflow error", e)
        logger.error(f"Workflow error: {e}")
        is_running = False


# Signal handlers for graceful shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals."""
    global is_running
    feedback.agent_action("System", "Shutting down...")
    is_running = False
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    # Don't auto-start workflow - let orchestrator trigger it
    # The workflow will start when orchestrator calls /api/start-scrolling
    feedback.agent_action("System", "Backend startup complete")
    logger.info("✅ Backend started - workflow will start when orchestrator triggers it")


if __name__ == "__main__":
    port = int(os.getenv("BACKEND_PORT", 8000))
    
    feedback.agent_action("System", f"Starting LinkedInMaxx backend on port {port}")
    logger.info(f"🚀 LinkedInMaxx Backend starting on http://localhost:{port}")
    logger.info(f"📡 API docs available at http://localhost:{port}/docs")
    logger.info(f"📝 Workflow will start when orchestrator triggers post generation")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )

