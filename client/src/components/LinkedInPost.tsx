import { motion } from 'motion/react';
import { ThumbsUp, MessageCircle, Share2, MoreHorizontal } from 'lucide-react';

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

interface LinkedInPostProps {
  post: Post;
  isHighlighted: boolean;
  isFaded: boolean;
  delay: number;
}

export function LinkedInPost({ post, isHighlighted, isFaded, delay }: LinkedInPostProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ 
        opacity: isFaded ? 0.3 : 1, 
        y: 0,
        scale: isHighlighted ? 1.01 : 1,
      }}
      transition={{ duration: 0.3, delay }}
      className={`bg-white rounded-md border ${
        isHighlighted 
          ? 'border-[#0073b1] shadow-md ring-2 ring-[#0073b1] ring-opacity-30' 
          : 'border-gray-200 shadow-sm'
      } overflow-hidden`}
    >
      {/* Post Header */}
      <div className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex gap-3">
            <img
              src={post.authorAvatar}
              alt={post.author}
              className="w-12 h-12 rounded-full"
            />
            <div>
              <h3 className="text-gray-900">{post.author}</h3>
              <p className="text-gray-600 text-sm">{post.authorTitle}</p>
              <p className="text-gray-500 text-sm">{post.timeAgo}</p>
            </div>
          </div>
          <button className="text-gray-500 hover:text-gray-700 p-1">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>

        {/* Post Content */}
        <div className="mt-3">
          <p className="text-gray-800 whitespace-pre-wrap">{post.content}</p>
        </div>
      </div>

      {/* Post Actions */}
      <div className="border-t border-gray-200 px-4 py-2">
        <div className="flex items-center justify-between text-gray-600 text-sm mb-2">
          <span>{post.likes} likes</span>
          <span>{post.comments} comments · {post.shares} shares</span>
        </div>
        <div className="flex items-center justify-around border-t border-gray-100 pt-2">
          <button className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-gray-50 rounded-md transition-colors text-sm">
            <ThumbsUp className="w-4 h-4" />
            <span>Like</span>
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-gray-50 rounded-md transition-colors text-sm">
            <MessageCircle className="w-4 h-4" />
            <span>Comment</span>
          </button>
          <button className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-gray-50 rounded-md transition-colors text-sm">
            <Share2 className="w-4 h-4" />
            <span>Share</span>
          </button>
        </div>
      </div>

      {/* Highlight Indicator */}
      {isHighlighted && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-[#0073b1] text-white px-3 py-2 text-xs flex items-center gap-2"
        >
          <span className="w-1.5 h-1.5 bg-white rounded-full animate-pulse"></span>
          <span>Agent targeting</span>
        </motion.div>
      )}
    </motion.div>
  );
}
