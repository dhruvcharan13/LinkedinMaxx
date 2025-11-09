import { useState, useEffect } from 'react';
import { AgentCard } from './AgentCard';
import { Clock, Settings } from 'lucide-react';
import { motion } from 'motion/react';
import { getPendingTasks, approveTask, rejectTask, type PendingTask } from '../services/api';
import { mockTasks, shouldUseMockData } from '../data/mockTasks';

interface AgentSuggestion {
  id: string;
  agentName: string;
  agentEmoji: string;
  type: 'post' | 'comment' | 'dm' | 'like';
  suggestion: string;
  targetPostId?: string;
  confidence: number;
  timestamp: Date;
  status: 'pending' | 'approved' | 'rejected' | 'executed';
}

// Convert PendingTask to AgentSuggestion format
function convertTaskToSuggestion(task: PendingTask): AgentSuggestion {
  return {
    id: task.task_id,
    agentName: task.agent_name,
    agentEmoji: task.agent_emoji,
    type: task.type === 'message' ? 'dm' : task.type, // Map 'message' to 'dm' for UI
    suggestion: task.content,
    targetPostId: task.url, // Use URL as target for now
    confidence: task.metadata.confidence || 85,
    timestamp: new Date(task.timestamp),
    status: task.status,
  };
}

// Development flag: Set to true to always use mock data for UI development
const FORCE_MOCK_DATA = true;

export function AgenticControlPanel() {
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [useMockData, setUseMockData] = useState(FORCE_MOCK_DATA);

  // Check if we should use mock data on mount
  useEffect(() => {
    // FORCE_MOCK_DATA flag for development - always use mock data
    if (FORCE_MOCK_DATA) {
      setUseMockData(true);
      const converted = mockTasks.map(convertTaskToSuggestion);
      setSuggestions(converted);
      setIsLoading(false);
      console.log('🚀 Using mock data for UI development');
      return;
    }

    // Check environment variable
    if (shouldUseMockData()) {
      setUseMockData(true);
      const converted = mockTasks.map(convertTaskToSuggestion);
      setSuggestions(converted);
      setIsLoading(false);
      return;
    }

    // Try to fetch from backend to check availability
    const checkBackend = async () => {
      try {
        // Try to fetch tasks (this will fail if backend is not running)
        const tasks = await getPendingTasks();
        
        // Backend is available
        setUseMockData(false);
        if (tasks.length > 0) {
          const converted = tasks.map(convertTaskToSuggestion);
          setSuggestions(converted);
        } else {
          // Backend is available but no tasks - use mock data for development
          console.warn('Backend returned no tasks, using mock data for development');
          setUseMockData(true);
          const converted = mockTasks.map(convertTaskToSuggestion);
          setSuggestions(converted);
        }
        setError(null);
      } catch (err) {
        // Backend not available - use mock data automatically
        console.warn('Backend not available, using mock data for styling');
        setUseMockData(true);
        const converted = mockTasks.map(convertTaskToSuggestion);
        setSuggestions(converted);
        setError(null); // Don't show error, just use mock data silently for better UX
      } finally {
        setIsLoading(false);
      }
    };

    checkBackend();
  }, []);

  // Poll for pending tasks every 2-3 seconds (only if not using mock data)
  useEffect(() => {
    if (useMockData) {
      // Use mock data immediately
      const converted = mockTasks.map(convertTaskToSuggestion);
      setSuggestions(converted);
      return;
    }

    const fetchTasks = async () => {
      try {
        const tasks = await getPendingTasks();
        const converted = tasks.map(convertTaskToSuggestion);
        setSuggestions(converted);
        setError(null);
      } catch (err) {
        console.error('Error fetching tasks:', err);
        // Fall back to mock data if backend fails
        setUseMockData(true);
        setError('Backend unavailable, using mock data');
        const converted = mockTasks.map(convertTaskToSuggestion);
        setSuggestions(converted);
      }
    };

    // Initial fetch
    fetchTasks();

    // Poll every 2 seconds
    const interval = setInterval(fetchTasks, 2000);

    return () => clearInterval(interval);
  }, [useMockData]);

  const handleApprove = async (id: string, editedContent?: string) => {
    if (useMockData) {
      // For mock data, just update status locally
      setSuggestions(prev =>
        prev.map(s =>
          s.id === id
            ? { ...s, status: 'approved' as const, suggestion: editedContent || s.suggestion }
            : s
        )
      );
      return;
    }

    try {
      const success = await approveTask(id, editedContent);
      if (success) {
        // Remove from local state (backend will remove from queue)
        setSuggestions(prev => prev.filter(s => s.id !== id));
      } else {
        setError('Failed to approve task');
      }
    } catch (err) {
      console.error('Error approving task:', err);
      setError('Failed to approve task');
    }
  };

  const handleReject = async (id: string) => {
    if (useMockData) {
      // For mock data, just update status locally
      setSuggestions(prev =>
        prev.map(s => (s.id === id ? { ...s, status: 'rejected' as const } : s))
      );
      return;
    }

    try {
      const success = await rejectTask(id);
      if (success) {
        // Remove from local state (backend will remove from queue)
        setSuggestions(prev => prev.filter(s => s.id !== id));
      } else {
        setError('Failed to reject task');
      }
    } catch (err) {
      console.error('Error rejecting task:', err);
      setError('Failed to reject task');
    }
  };

  const handleEdit = (id: string, newSuggestion: string) => {
    // Update local state immediately for better UX
    setSuggestions(prev =>
      prev.map(s => s.id === id ? { ...s, suggestion: newSuggestion } : s)
    );
  };

  const approvedActions = suggestions.filter(s => s.status === 'approved');
  const pendingCount = suggestions.filter(s => s.status === 'pending').length;

  return (
    <div className="h-full w-full bg-white flex flex-col">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-200 bg-[#0073b1]">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-4xl text-white font-bold">LinkedInGPT Dashboard</h2>
          <button className="p-1 hover:bg-white/10 rounded transition-colors">
            <Settings className="w-4 h-4 text-white" />
          </button>
        </div>
        <p className="text-xs text-white/80">
          {pendingCount} pending action{pendingCount !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Agent Cards */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {isLoading ? (
          <div className="text-center text-gray-500 py-8">
            Loading tasks...
          </div>
        ) : suggestions.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No pending tasks. Waiting for agents to generate tasks...
          </div>
        ) : (
          suggestions.map((suggestion, index) => (
            <AgentCard
              key={suggestion.id}
              suggestion={suggestion}
              onApprove={(editedContent) => handleApprove(suggestion.id, editedContent)}
              onReject={() => handleReject(suggestion.id)}
              onEdit={(newText) => handleEdit(suggestion.id, newText)}
              delay={index * 0.05}
            />
          ))
        )}
      </div>

      {/* Scheduled Queue */}
      {approvedActions.length > 0 && (
        <div className="border-t border-gray-200 bg-gray-50 p-3">
          <div className="flex items-center gap-1.5 mb-2.5">
            <Clock className="w-3.5 h-3.5 text-gray-600" />
            <span className="text-xs text-gray-700">Scheduled Queue</span>
          </div>
          <div className="space-y-2">
            {approvedActions.map((action, index) => (
              <div
                key={action.id}
                className="bg-white rounded-md border border-gray-200 p-2"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs text-gray-700">
                    {action.agentEmoji} {action.type.toUpperCase()}
                  </span>
                  <span className="text-xs text-gray-500">
                    ~{(index + 1) * 5}m
                  </span>
                </div>
                <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: '100%' }}
                    transition={{ duration: (index + 1) * 5 * 60, ease: 'linear' }}
                    className="h-full bg-[#0073b1]"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
