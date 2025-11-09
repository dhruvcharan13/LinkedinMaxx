import { PendingTask } from '../services/api';

/**
 * Mock data for agent cards
 * Used for frontend development and styling when backend is unavailable
 */

const now = new Date();
const oneMinuteAgo = new Date(now.getTime() - 1 * 60 * 1000);
const threeMinutesAgo = new Date(now.getTime() - 3 * 60 * 1000);
const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);
const fifteenMinutesAgo = new Date(now.getTime() - 15 * 60 * 1000);

export const mockTasks: PendingTask[] = [
  // Post Agent Suggestions
  {
    task_id: 'mock-post-1',
    type: 'post',
    content: 'Just wrapped up an incredible hackathon at Hack the Valley X! 🚀 Built an AI-powered data integration tool that helps teams streamline their workflows. The best part? Learning from incredible mentors and collaborating with passionate developers. Every hackathon teaches me something new about problem-solving and teamwork. #Hackathon #AI #TechCommunity',
    url: 'https://www.linkedin.com/feed',
    name: 'You',
    agent_name: 'Post Agent',
    agent_emoji: '🧠',
    metadata: {
      confidence: 92,
      classification: 'daily_post',
      action: 'post',
      context: 'Recent hackathon experience'
    },
    status: 'pending',
    timestamp: oneMinuteAgo.toISOString()
  },
  {
    task_id: 'mock-post-2',
    type: 'post',
    content: 'Reflecting on my co-op journey: Didn\'t get that dream position, but gained something even more valuable - resilience 💪 Every setback is a setup for a comeback! Learning to embrace rejection as redirection has been transformative. To all students navigating the job search - keep pushing, your opportunity is coming! #GrowthMindset #CareerJourney #CoOp',
    url: 'https://www.linkedin.com/feed',
    name: 'You',
    agent_name: 'Post Agent',
    agent_emoji: '🧠',
    metadata: {
      confidence: 87,
      classification: 'daily_post',
      action: 'post',
      context: 'Co-op reflection and motivation'
    },
    status: 'pending',
    timestamp: threeMinutesAgo.toISOString()
  },
  {
    task_id: 'mock-post-3',
    type: 'post',
    content: 'Excited to share that I\'ve been diving deep into LLM-assisted data mapping! Working on agentic data integration tools that combine the power of AI with human-in-the-loop validation. The intersection of AI and data engineering is where the magic happens. Would love to connect with others exploring this space! #AI #DataEngineering #MachineLearning',
    url: 'https://www.linkedin.com/feed',
    name: 'You',
    agent_name: 'Post Agent',
    agent_emoji: '🧠',
    metadata: {
      confidence: 95,
      classification: 'daily_post',
      action: 'post',
      context: 'Technical learning and expertise'
    },
    status: 'approved',
    timestamp: fiveMinutesAgo.toISOString()
  },

  // Messaging Agent Suggestions - Recruiters
  {
    task_id: 'mock-message-1',
    type: 'message',
    content: 'Hi Sarah! I came across your profile and was impressed by your work in talent acquisition at TechCorp. I\'m currently exploring opportunities in software engineering and would love to learn more about the team culture and upcoming roles. Would you be open to a quick chat?',
    url: 'https://www.linkedin.com/in/sarah-chen-recruiter',
    name: 'Sarah Chen',
    agent_name: 'Messaging Agent',
    agent_emoji: '💌',
    metadata: {
      confidence: 89,
      classification: 'recruiter',
      action: 'message',
      profile_type: 'recruiter'
    },
    status: 'pending',
    timestamp: tenMinutesAgo.toISOString()
  },
  {
    task_id: 'mock-message-2',
    type: 'message',
    content: 'Hello Michael! Noticed you\'re the Head of Talent at StartupXYZ. Your recent post about building inclusive engineering teams resonated with me. I\'d love to connect and potentially explore opportunities to contribute to your mission. Are you open to connecting?',
    url: 'https://www.linkedin.com/in/michael-johnson-talent',
    name: 'Michael Johnson',
    agent_name: 'Messaging Agent',
    agent_emoji: '💌',
    metadata: {
      confidence: 91,
      classification: 'recruiter',
      action: 'message',
      profile_type: 'recruiter'
    },
    status: 'pending',
    timestamp: fifteenMinutesAgo.toISOString()
  },

  // Messaging Agent Suggestions - Waterloo Students
  {
    task_id: 'mock-message-3',
    type: 'message',
    content: 'Hey Alex! Saw you\'re also a Waterloo student in CS. I noticed we have similar co-op experiences and interests in AI/ML. Would love to connect and chat about our experiences! Always great to network with fellow Waterloo students.',
    url: 'https://www.linkedin.com/in/alex-wong-waterloo',
    name: 'Alex Wong',
    agent_name: 'Dating Agent',
    agent_emoji: '🎯',
    metadata: {
      confidence: 88,
      classification: 'waterloo_student',
      action: 'message',
      profile_type: 'waterloo',
      co_op_match_score: 85
    },
    status: 'pending',
    timestamp: oneMinuteAgo.toISOString()
  },

  // Comment Agent Suggestions
  {
    task_id: 'mock-comment-1',
    type: 'comment',
    content: 'Huge congratulations on the DataWeave win at Hack the Valley X, Dhruv! Impressive work on agentic data integration. Loved reading about the LLM-assisted mapping and human-in-the-loop validation. Keep up the great work! 🎉',
    url: 'https://www.linkedin.com/posts/dhruv-charan-89b1b5194_huge-win-hack-the-valley-x-activity-7388746123936583680-EEdN',
    name: 'Dhruv Charan',
    agent_name: 'Comment Agent',
    agent_emoji: '💬',
    metadata: {
      confidence: 93,
      classification: 'engagement',
      action: 'comment',
      post_type: 'achievement'
    },
    status: 'pending',
    timestamp: threeMinutesAgo.toISOString()
  },
  {
    task_id: 'mock-comment-2',
    type: 'comment',
    content: 'Congrats on the feature launch! 🎉 The attention to detail really shows. Would love to hear more about your implementation process and any challenges you faced along the way.',
    url: 'https://www.linkedin.com/posts/jane-doe_feature-launch-activity-1234567890',
    name: 'Jane Doe',
    agent_name: 'Comment Agent',
    agent_emoji: '💬',
    metadata: {
      confidence: 90,
      classification: 'engagement',
      action: 'comment',
      post_type: 'product_launch'
    },
    status: 'approved',
    timestamp: fiveMinutesAgo.toISOString()
  },
  {
    task_id: 'mock-comment-3',
    type: 'comment',
    content: 'This resonates so much! The journey from rejection to growth is real. Thanks for sharing your perspective - it\'s exactly what I needed to hear today. Keep inspiring! 💪',
    url: 'https://www.linkedin.com/posts/john-smith_career-growth-activity-1234567891',
    name: 'John Smith',
    agent_name: 'Comment Agent',
    agent_emoji: '💬',
    metadata: {
      confidence: 86,
      classification: 'engagement',
      action: 'comment',
      post_type: 'motivational'
    },
    status: 'pending',
    timestamp: tenMinutesAgo.toISOString()
  },

  // Founder/Co-founder Message
  {
    task_id: 'mock-message-4',
    type: 'message',
    content: 'Hi David! I saw you\'re the co-founder of InnovateTech. Your vision for AI-driven solutions is inspiring. I\'m a software engineering student passionate about building impactful products. Would love to connect and learn about your journey as a founder!',
    url: 'https://www.linkedin.com/in/david-lee-founder',
    name: 'David Lee',
    agent_name: 'Messaging Agent',
    agent_emoji: '💌',
    metadata: {
      confidence: 85,
      classification: 'cofounder',
      action: 'message',
      profile_type: 'cofounder'
    },
    status: 'pending',
    timestamp: fifteenMinutesAgo.toISOString()
  }
];

/**
 * Get mock tasks filtered by status
 */
export function getMockTasks(status?: 'pending' | 'approved' | 'rejected'): PendingTask[] {
  if (status) {
    return mockTasks.filter(task => task.status === status);
  }
  return mockTasks;
}

/**
 * Check if we should use mock data
 * Set VITE_USE_MOCK_DATA=true in environment or check backend availability
 */
export function shouldUseMockData(): boolean {
  // Check environment variable first
  // Use a type-safe way to access env vars
  const useMockData = (import.meta as any).env?.VITE_USE_MOCK_DATA;
  if (useMockData === 'true' || useMockData === true) {
    return true;
  }
  
  // You can add backend health check here if needed
  // For now, we'll use a simple flag
  return false;
}

