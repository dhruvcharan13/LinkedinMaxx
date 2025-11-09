/**
 * API client for LinkedInMaxx backend
 * Handles communication with FastAPI backend for task management
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface PendingTask {
  task_id: string;
  type: 'post' | 'message' | 'comment';
  content: string;
  url: string;
  name: string;
  agent_name: string;
  agent_emoji: string;
  metadata: {
    confidence?: number;
    classification?: string;
    action?: string;
    [key: string]: any;
  };
  status: 'pending' | 'approved' | 'rejected';
  timestamp: string;
}

export interface TaskApprovalRequest {
  task_id: string;
  edited_content?: string;
}

export interface TaskRejectionRequest {
  task_id: string;
}

export interface ApiResponse<T> {
  status: 'success' | 'error';
  data?: T;
  message?: string;
  error?: string;
}

/**
 * Get all pending tasks from the backend
 */
export async function getPendingTasks(): Promise<PendingTask[]> {
  const response = await fetch(`${API_BASE_URL}/api/tasks/pending`);
  if (!response.ok) {
    throw new Error(`Failed to fetch pending tasks: ${response.statusText} (${response.status})`);
  }
  const data = await response.json();
  return data.tasks || [];
}

/**
 * Approve a task
 */
export async function approveTask(
  taskId: string,
  editedContent?: string
): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks/approve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
        edited_content: editedContent,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to approve task: ${response.statusText}`);
    }
    const data = await response.json();
    return data.status === 'success';
  } catch (error) {
    console.error('Error approving task:', error);
    return false;
  }
}

/**
 * Reject a task
 */
export async function rejectTask(taskId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/tasks/reject`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        task_id: taskId,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to reject task: ${response.statusText}`);
    }
    const data = await response.json();
    return data.status === 'success';
  } catch (error) {
    console.error('Error rejecting task:', error);
    return false;
  }
}

/**
 * Get queue statistics
 */
export async function getQueueStats() {
  try {
    const response = await fetch(`${API_BASE_URL}/api/queue-stats`);
    if (!response.ok) {
      throw new Error(`Failed to fetch queue stats: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching queue stats:', error);
    return null;
  }
}

