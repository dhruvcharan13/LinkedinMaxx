import { useState } from 'react';
import { LinkedInFeedPanel } from './components/LinkedInFeedPanel';
import { AgenticControlPanel } from './components/AgenticControlPanel';

export default function App() {
  const [highlightedPostId, setHighlightedPostId] = useState<string | null>(null);

  return (
    <div className="h-screen flex bg-white">
      {/* Left Panel - LinkedIn Feed */}
      <div className="flex-1 overflow-hidden">
        <LinkedInFeedPanel highlightedPostId={highlightedPostId} />
      </div>

      {/* Right Panel - Agentic Control (300px) */}
      <div className="w-[300px] border-l border-gray-200">
        <AgenticControlPanel onHighlightPost={setHighlightedPostId} />
      </div>
    </div>
  );
}
