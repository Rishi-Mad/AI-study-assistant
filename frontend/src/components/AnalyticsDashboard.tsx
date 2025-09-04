import { useState, useEffect } from "react";
import { cn } from "../lib/utils";
import { 
  BookOpen, 
  HelpCircle, 
  Clock, 
  Target,
  Award,
  BarChart3
} from "lucide-react";

interface AnalyticsData {
  totalSessions: number;
  totalCards: number;
  totalQuizzes: number;
  totalQuestions: number;
  averageAccuracy: number;
  studyStreak: number;
  totalStudyTime: number;
  weeklyProgress: Array<{
    date: string;
    cards: number;
    quizzes: number;
    accuracy: number;
  }>;
  subjectBreakdown: Array<{
    subject: string;
    count: number;
    accuracy: number;
  }>;
  recentActivity: Array<{
    type: string;
    timestamp: string;
    description: string;
  }>;
}

interface AnalyticsDashboardProps {
  sessionId?: string;
}

export default function AnalyticsDashboard({ sessionId }: AnalyticsDashboardProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'all'>('week');

  useEffect(() => {
    // Simulate fetching analytics data
    // In a real app, this would fetch from the backend
    const mockData: AnalyticsData = {
      totalSessions: 12,
      totalCards: 156,
      totalQuizzes: 8,
      totalQuestions: 45,
      averageAccuracy: 0.78,
      studyStreak: 7,
      totalStudyTime: 1240, // minutes
      weeklyProgress: [
        { date: '2024-01-15', cards: 12, quizzes: 1, accuracy: 0.75 },
        { date: '2024-01-16', cards: 18, quizzes: 2, accuracy: 0.82 },
        { date: '2024-01-17', cards: 15, quizzes: 1, accuracy: 0.79 },
        { date: '2024-01-18', cards: 22, quizzes: 3, accuracy: 0.85 },
        { date: '2024-01-19', cards: 20, quizzes: 2, accuracy: 0.88 },
        { date: '2024-01-20', cards: 16, quizzes: 1, accuracy: 0.76 },
        { date: '2024-01-21', cards: 14, quizzes: 2, accuracy: 0.81 },
      ],
      subjectBreakdown: [
        { subject: 'Mathematics', count: 45, accuracy: 0.82 },
        { subject: 'Science', count: 38, accuracy: 0.75 },
        { subject: 'History', count: 28, accuracy: 0.79 },
        { subject: 'Literature', count: 25, accuracy: 0.85 },
        { subject: 'General', count: 20, accuracy: 0.73 },
      ],
      recentActivity: [
        { type: 'flashcard', timestamp: '2024-01-21T10:30:00Z', description: 'Reviewed 15 flashcards on Mathematics' },
        { type: 'quiz', timestamp: '2024-01-21T09:15:00Z', description: 'Completed quiz on Physics with 85% accuracy' },
        { type: 'flashcard', timestamp: '2024-01-20T16:45:00Z', description: 'Generated 20 new flashcards from study material' },
        { type: 'quiz', timestamp: '2024-01-20T14:20:00Z', description: 'Took practice quiz on Chemistry' },
        { type: 'flashcard', timestamp: '2024-01-19T11:10:00Z', description: 'Reviewed 18 flashcards on History' },
      ]
    };

    setTimeout(() => {
      setAnalytics(mockData);
      setLoading(false);
    }, 1000);
  }, [sessionId, timeRange]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  if (!analytics) {
    return (
      <div className="text-center py-12">
        <BarChart3 className="h-12 w-12 text-white/40 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-white mb-2">No Analytics Data</h3>
        <p className="text-white/60">Start studying to see your progress here</p>
      </div>
    );
  }

  const formatTime = (minutes: number) => {
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    });
  };

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-end">
        <div className="flex bg-white/10 rounded-lg p-1">
          {(['week', 'month', 'all'] as const).map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={cn(
                "px-3 py-1 rounded text-sm font-medium transition-colors",
                timeRange === range
                  ? "bg-white text-slate-900"
                  : "text-white/80 hover:text-white"
              )}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <BookOpen className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{analytics.totalCards}</div>
              <div className="text-sm text-white/60">Flashcards</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-500/20 rounded-lg">
              <HelpCircle className="h-5 w-5 text-green-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{analytics.totalQuizzes}</div>
              <div className="text-sm text-white/60">Quizzes</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Target className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{(analytics.averageAccuracy * 100).toFixed(0)}%</div>
              <div className="text-sm text-white/60">Accuracy</div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-orange-500/20 rounded-lg">
              <Award className="h-5 w-5 text-orange-400" />
            </div>
            <div>
              <div className="text-2xl font-bold text-white">{analytics.studyStreak}</div>
              <div className="text-sm text-white/60">Day Streak</div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Progress */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Weekly Progress</h3>
          <div className="space-y-3">
            {analytics.weeklyProgress.map((day, i) => (
              <div key={i} className="flex items-center justify-between">
                <div className="text-sm text-white/80">{formatDate(day.date)}</div>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <BookOpen className="h-3 w-3 text-blue-400" />
                    <span className="text-xs text-white/60">{day.cards}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <HelpCircle className="h-3 w-3 text-green-400" />
                    <span className="text-xs text-white/60">{day.quizzes}</span>
                  </div>
                  <div className="text-xs text-white/60">
                    {(day.accuracy * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Subject Breakdown */}
        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Subject Performance</h3>
          <div className="space-y-3">
            {analytics.subjectBreakdown.map((subject, i) => (
              <div key={i} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white/80">{subject.subject}</span>
                  <span className="text-sm text-white/60">
                    {subject.count} items • {(subject.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-white/10 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${subject.accuracy * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Activity</h3>
        <div className="space-y-3">
          {analytics.recentActivity.map((activity, i) => (
            <div key={i} className="flex items-center space-x-3 p-3 bg-white/5 rounded-lg">
              <div className={cn(
                "p-2 rounded-lg",
                activity.type === 'flashcard' ? "bg-blue-500/20" : "bg-green-500/20"
              )}>
                {activity.type === 'flashcard' ? (
                  <BookOpen className="h-4 w-4 text-blue-400" />
                ) : (
                  <HelpCircle className="h-4 w-4 text-green-400" />
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm text-white">{activity.description}</p>
                <p className="text-xs text-white/60">
                  {new Date(activity.timestamp).toLocaleString()}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Study Time Summary */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Total Study Time</h3>
            <p className="text-3xl font-bold text-white mt-2">{formatTime(analytics.totalStudyTime)}</p>
          </div>
          <div className="p-4 bg-primary-500/20 rounded-lg">
            <Clock className="h-8 w-8 text-primary-400" />
          </div>
        </div>
      </div>
    </div>
  );
}