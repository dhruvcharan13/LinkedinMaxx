import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { LinkedInPost } from './LinkedInPost';

interface Post {
  id: string;
  author: string;
  authorTitle: string;
  authorAvatar: string;
  content: string;
  timeAgo: string;
  likes: number;
  comments: number;
  shares: number;
  imageUrl?: string;
}

const MOCK_POSTS: Post[] = [
  {
    id: '1',
    author: 'Sarah Chen',
    authorTitle: 'Product Manager at Tech Corp',
    authorAvatar: 'https://i.pravatar.cc/150?img=1',
    content: 'Just shipped our biggest feature yet! 🚀 Proud of the team for pulling together and delivering an incredible user experience. #ProductManagement #TechLife',
    timeAgo: '2h ago',
    likes: 124,
    comments: 15,
    shares: 8,
  },
  {
    id: '2',
    author: 'Alex Thompson',
    authorTitle: 'Software Engineer | AI Enthusiast',
    authorAvatar: 'https://i.pravatar.cc/150?img=2',
    content: 'Didn\'t get the co-op position I applied for, but I learned so much through the interview process. Every rejection is a learning opportunity. Onwards and upwards! 💪 #GrowthMindset #CareerDevelopment',
    timeAgo: '4h ago',
    likes: 89,
    comments: 23,
    shares: 4,
  },
  {
    id: '3',
    author: 'Maria Rodriguez',
    authorTitle: 'Founder & CEO at StartupXYZ',
    authorAvatar: 'https://i.pravatar.cc/150?img=3',
    content: 'Excited to announce that we\'ve raised our Series A! 🎉 Thank you to all our investors, team members, and supporters who believed in our vision. Here\'s to the next chapter!',
    timeAgo: '6h ago',
    likes: 342,
    comments: 56,
    shares: 28,
  },
  {
    id: '4',
    author: 'James Wilson',
    authorTitle: 'Data Scientist at AnalyticsPro',
    authorAvatar: 'https://i.pravatar.cc/150?img=4',
    content: 'Just published a new article on machine learning best practices. Link in comments! Would love to hear your thoughts. #MachineLearning #DataScience',
    timeAgo: '8h ago',
    likes: 67,
    comments: 12,
    shares: 15,
  },
  {
    id: '5',
    author: 'Emily Zhang',
    authorTitle: 'UX Designer | Making the web beautiful',
    authorAvatar: 'https://i.pravatar.cc/150?img=5',
    content: 'Design isn\'t just about making things look pretty - it\'s about solving real problems for real people. Here are 5 principles I live by... 🎨✨',
    timeAgo: '10h ago',
    likes: 156,
    comments: 28,
    shares: 19,
  },
  {
    id: '6',
    author: 'David Park',
    authorTitle: 'Marketing Director at BrandCo',
    authorAvatar: 'https://i.pravatar.cc/150?img=6',
    content: 'The future of marketing is personalization. Here\'s how we increased conversion by 40% using AI-driven campaigns. Thread 🧵',
    timeAgo: '12h ago',
    likes: 203,
    comments: 34,
    shares: 22,
  },
];

interface LinkedInFeedPanelProps {
  highlightedPostId: string | null;
}

export function LinkedInFeedPanel({ highlightedPostId }: LinkedInFeedPanelProps) {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [autoScrolling, setAutoScrolling] = useState(true);

  // Simulate Playwright auto-scrolling
  useEffect(() => {
    if (!autoScrolling) return;

    const interval = setInterval(() => {
      setScrollProgress(prev => {
        const next = prev + 0.5;
        return next > 100 ? 0 : next;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [autoScrolling]);

  return (
    <div className="h-full flex flex-col bg-gray-100">
      {/* Playwright Browser Chrome */}
      <div className="bg-gray-800 text-white px-4 py-2.5 flex items-center gap-3">
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
        </div>
        <div className="flex-1 bg-gray-700 rounded-md px-3 py-1.5 flex items-center gap-2">
          <span className="text-gray-400 text-sm">🔒</span>
          <span className="text-gray-300 text-sm">linkedin.com/feed</span>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 bg-orange-600 rounded-md text-xs">
          <div className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></div>
          <span>Playwright</span>
        </div>
      </div>

      {/* Feed Header */}
      <div className="px-6 py-3.5 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm text-gray-900">LinkedIn Feed</h2>
            <p className="text-xs text-gray-500">Automated session</p>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-xs text-gray-600">Scrolling</span>
            </div>
            <button
              onClick={() => setAutoScrolling(!autoScrolling)}
              className="px-2.5 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-xs transition-colors"
            >
              {autoScrolling ? 'Pause' : 'Resume'}
            </button>
          </div>
        </div>
        
        {/* Scroll Progress Bar */}
        <div className="mt-2.5 h-1 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-[#0073b1]"
            style={{ width: `${scrollProgress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
      </div>

      {/* Feed Content */}
      <div className="flex-1 overflow-y-auto p-6 bg-white">
        <div className="max-w-2xl mx-auto space-y-3">
          <AnimatePresence>
            {MOCK_POSTS.map((post, index) => (
              <LinkedInPost
                key={post.id}
                post={post}
                isHighlighted={post.id === highlightedPostId}
                isFaded={highlightedPostId !== null && post.id !== highlightedPostId}
                delay={index * 0.1}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
