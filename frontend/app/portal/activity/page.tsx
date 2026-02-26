'use client';

import { useEffect, useState } from 'react';
import {
  Clock,
  Eye,
  FileText,
  Home,
  User,
  Check,
  X,
  Calendar,
} from 'lucide-react';

interface Activity {
  id: number;
  action: string;
  resource_type?: string;
  resource_id?: number;
  metadata?: string;
  created_at: string;
}

export default function PortalActivityPage() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchActivity();
  }, []);

  const fetchActivity = async () => {
    try {
      const token = localStorage.getItem('portal_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiUrl}/portal/activity?limit=50`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch activity');
      }

      const data = await response.json();
      setActivities(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'login':
        return <Check className="w-5 h-5 text-green-600" />;
      case 'view_property':
        return <Home className="w-5 h-5 text-blue-600" />;
      case 'view_contract':
      case 'sign_contract':
        return <FileText className="w-5 h-5 text-purple-600" />;
      case 'view_properties':
      case 'view_contracts':
        return <Eye className="w-5 h-5 text-slate-600" />;
      default:
        return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };

  const getActionLabel = (action: string) => {
    return action
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading activity...</p>
        </div>
      </div>
    );
  }

  // Group activities by date
  const groupedActivities: Record<string, Activity[]> = {};
  activities.forEach((activity) => {
    const date = new Date(activity.created_at).toLocaleDateString();
    if (!groupedActivities[date]) {
      groupedActivities[date] = [];
    }
    groupedActivities[date].push(activity);
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Activity History</h1>
        <p className="text-slate-600 mt-1">Track your recent actions and interactions</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      )}

      {activities.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Clock className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No activity yet</h3>
          <p className="text-slate-600">
            Your activity will appear here as you use the portal.
          </p>
        </div>
      ) : (
        <div className="max-w-3xl">
          {Object.entries(groupedActivities).map(([date, dayActivities]) => (
            <div key={date} className="mb-8">
              <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-4">
                {date === new Date().toLocaleDateString() ? 'Today' : date}
              </h3>
              <div className="space-y-3">
                {dayActivities.map((activity) => (
                  <div
                    key={activity.id}
                    className="bg-white rounded-lg shadow-sm border border-slate-200 p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start gap-4">
                      <div className="p-2 bg-slate-100 rounded-full">
                        {getActionIcon(activity.action)}
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">
                          {getActionLabel(activity.action)}
                        </p>
                        {activity.resource_type && activity.resource_id && (
                          <p className="text-sm text-slate-600 mt-1">
                            {activity.resource_type} #{activity.resource_id}
                          </p>
                        )}
                        <p className="text-xs text-slate-500 mt-2 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(activity.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
