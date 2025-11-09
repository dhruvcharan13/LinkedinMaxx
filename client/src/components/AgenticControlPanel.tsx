import { useState } from 'react';
import { AgentCard } from './AgentCard';
import { Clock, Settings } from 'lucide-react';
import { motion } from 'motion/react';

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

const MOCK_SUGGESTIONS: AgentSuggestion[] = [
  {
    id: 'suggestion-1',
    agentName: 'Post Agent',
    agentEmoji: '🧠',
    type: 'post',
    suggestion: 'Didn\'t get the co-op, but gained resilience 💪 Every setback is a setup for a comeback! #GrowthMindset #CareerJourney',
    confidence: 87,
    timestamp: new Date(),
    status: 'pending',
  },
  {
    id: 'suggestion-2',
    agentName: 'Comment Agent',
    agentEmoji: '💬',
    type: 'comment',
    suggestion: 'Congrats on the feature launch! 🎉 The attention to detail really shows.',
    targetPostId: '1',
    confidence: 92,
    timestamp: new Date(Date.now() - 5 * 60000),
    status: 'pending',
  },
  {
    id: 'suggestion-3',
    agentName: 'Engagement Agent',
    agentEmoji: '👍',
    type: 'like',
    suggestion: 'Like post about AI and productivity from Sarah Chen',
    targetPostId: '2',
    confidence: 95,
    timestamp: new Date(Date.now() - 10 * 60000),
    status: 'pending',
  },
  {
    id: 'suggestion-4',
    agentName: 'Comment Agent',
    agentEmoji: '💬',
    type: 'comment',
    suggestion: 'This resonates! Would love to hear more about your implementation.',
    targetPostId: '6',
    confidence: 85,
    timestamp: new Date(Date.now() - 20 * 60000),
    status: 'approved',
  },
];

export function AgenticControlPanel() {
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>(MOCK_SUGGESTIONS);

  const handleApprove = (id: string) => {
    setSuggestions(prev =>
      prev.map(s => s.id === id ? { ...s, status: 'approved' as const } : s)
    );
  };

  const handleReject = (id: string) => {
    setSuggestions(prev =>
      prev.map(s => s.id === id ? { ...s, status: 'rejected' as const } : s)
    );
  };

  const handleEdit = (id: string, newSuggestion: string) => {
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
          <h2 className="text-sm text-white font-semibold">LinkedInGPT Dashboard</h2>
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
        {suggestions.map((suggestion, index) => (
          <AgentCard
            key={suggestion.id}
            suggestion={suggestion}
            onApprove={() => handleApprove(suggestion.id)}
            onReject={() => handleReject(suggestion.id)}
            onEdit={(newText) => handleEdit(suggestion.id, newText)}
            delay={index * 0.05}
          />
        ))}
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
