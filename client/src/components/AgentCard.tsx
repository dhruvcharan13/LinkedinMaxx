import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Check, X, Edit2, CheckCircle, XCircle } from 'lucide-react';

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
  owner?: string; // Owner of the post/profile
  url?: string; // URL of the post/profile
}

interface AgentCardProps {
  suggestion: AgentSuggestion;
  onApprove: (editedContent?: string) => void;
  onReject: () => void;
  onEdit: (newText: string) => void;
  delay: number;
}

export function AgentCard({ 
  suggestion, 
  onApprove, 
  onReject, 
  onEdit,
  delay 
}: AgentCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(suggestion.suggestion);

  // Update editText when suggestion changes
  useEffect(() => {
    setEditText(suggestion.suggestion);
  }, [suggestion.suggestion]);

  const handleApproveWithEdit = () => {
    // Always pass edited content to onApprove (even if unchanged)
    onApprove(editText);
    setIsEditing(false);
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'from-green-500 to-green-600';
    if (confidence >= 75) return 'from-yellow-500 to-orange-500';
    return 'from-orange-500 to-red-500';
  };

  const getConfidenceTextColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600';
    if (confidence >= 75) return 'text-yellow-600';
    return 'text-orange-600';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay }}
      className="border border-gray-200 rounded-md p-3 bg-white hover:border-gray-300 transition-colors"
    >
      {/* Card Header */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-900 font-semibold">{suggestion.agentName}</span>
        </div>
        <span className={`text-xs ${getConfidenceTextColor(suggestion.confidence)}`}>
          {suggestion.confidence}%
        </span>
      </div>

      {/* Confidence Meter */}
      <div className="mb-2.5">
        <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${suggestion.confidence}%` }}
            transition={{ duration: 0.5, delay: delay + 0.2 }}
            className={`h-full bg-gradient-to-r ${getConfidenceColor(suggestion.confidence)}`}
          />
        </div>
      </div>

      {/* Owner and URL Information */}
      {((suggestion.owner && suggestion.owner.trim()) || (suggestion.url && suggestion.url.trim())) && (
        <div className="mb-2.5 space-y-1 text-xs text-gray-600">
          {suggestion.owner && suggestion.owner.trim() && (
            <div className="flex items-center gap-1">
              <span className="font-medium text-gray-700">Owner:</span>
              <span>{suggestion.owner}</span>
            </div>
          )}
          {suggestion.url && suggestion.url.trim() && (
            <div className="flex items-start gap-1">
              <span className="font-medium text-gray-700 whitespace-nowrap">URL:</span>
              <a 
                href={suggestion.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline break-all text-xs"
                title={suggestion.url}
              >
                {suggestion.url.length > 50 
                  ? `${suggestion.url.substring(0, 50)}...` 
                  : suggestion.url}
              </a>
            </div>
          )}
        </div>
      )}

      {/* Suggestion Content */}
      <div className="mb-2.5">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              className="w-full p-2 border border-gray-300 rounded-md text-xs resize-none focus:outline-none focus:ring-2 focus:ring-[#0073b1] focus:border-transparent"
              rows={3}
            />
            <div className="flex gap-2">
              <button
                onClick={handleApproveWithEdit}
                className="flex-1 px-3 py-1.5 bg-green-500 text-white rounded-md text-xs hover:bg-green-600 transition-colors"
              >
                Save & Approve
              </button>
              <button
                onClick={() => {
                  setIsEditing(false);
                  setEditText(suggestion.suggestion);
                }}
                className="flex-1 px-3 py-1.5 bg-gray-100 text-gray-700 rounded-md text-xs hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <p className="text-xs text-gray-700 leading-relaxed">
            {suggestion.suggestion}
          </p>
        )}
      </div>

      {/* Action Buttons */}
      {suggestion.status === 'pending' && !isEditing && (
        <div className="flex gap-2 mb-2">
          <button
            onClick={() => onApprove()}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-green-500 text-white rounded-md text-xs hover:bg-green-600 transition-colors"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve</span>
          </button>
          <button
            onClick={onReject}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-red-500 text-white rounded-md text-xs hover:bg-red-600 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
            <span>Reject</span>
          </button>
          <button
            onClick={() => setIsEditing(true)}
            className="px-3 py-2 bg-gray-100 text-gray-700 rounded-md text-xs hover:bg-gray-200 transition-colors"
          >
            <Edit2 className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Status Log */}
      <div className="text-xs">
        {suggestion.status === 'pending' && !isEditing && (
          <span className="text-orange-600 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-orange-600 rounded-full"></span>
            Pending
          </span>
        )}
        {suggestion.status === 'approved' && (
          <div className="flex items-center gap-1.5 text-green-600">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Approved</span>
          </div>
        )}
        {suggestion.status === 'rejected' && (
          <div className="flex items-center gap-1.5 text-red-600">
            <XCircle className="w-3.5 h-3.5" />
            <span>Rejected</span>
          </div>
        )}
      </div>
    </motion.div>
  );
}
