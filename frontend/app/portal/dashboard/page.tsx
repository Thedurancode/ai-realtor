'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Building2,
  FileText,
  TrendingUp,
  Calendar,
  ArrowRight,
} from 'lucide-react';

interface DashboardStats {
  totalProperties: number;
  activeContracts: number;
  pendingActions: number;
  recentActivity: number;
}

export default function PortalDashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalProperties: 0,
    activeContracts: 0,
    pendingActions: 0,
    recentActivity: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('portal_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      // Fetch properties and contracts in parallel
      const [propertiesRes, contractsRes] = await Promise.all([
        fetch(`${apiUrl}/portal/properties`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${apiUrl}/portal/contracts`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      const properties = await propertiesRes.json();
      const contracts = await contractsRes.json();

      setStats({
        totalProperties: properties.length || 0,
        activeContracts: contracts.filter((c: any) => c.status !== 'completed').length || 0,
        pendingActions: contracts.filter((c: any) => c.can_sign && c.status === 'sent').length || 0,
        recentActivity: 5, // Placeholder
      });
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'View Properties',
      description: 'See all your properties',
      icon: Building2,
      href: '/portal/properties',
      color: 'bg-blue-500',
    },
    {
      title: 'My Contracts',
      description: 'Review and sign documents',
      icon: FileText,
      href: '/portal/contracts',
      color: 'bg-green-500',
    },
    {
      title: 'Activity History',
      description: 'Track your recent actions',
      icon: Clock,
      href: '/portal/activity',
      color: 'bg-purple-500',
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-1">Welcome to your real estate portal</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Properties"
          value={stats.totalProperties}
          icon={Building2}
          color="bg-blue-500"
          trend="+0 this month"
        />
        <StatCard
          title="Active Contracts"
          value={stats.activeContracts}
          icon={FileText}
          color="bg-green-500"
          trend="Awaiting action"
        />
        <StatCard
          title="Pending Signatures"
          value={stats.pendingActions}
          icon={Calendar}
          color="bg-yellow-500"
          trend="Needs attention"
        />
        <StatCard
          title="Recent Activity"
          value={stats.recentActivity}
          icon={TrendingUp}
          color="bg-purple-500"
          trend="Last 7 days"
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-slate-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <Link
                key={action.title}
                href={action.href}
                className="bg-white rounded-xl p-6 shadow-sm border border-slate-200 hover:shadow-md hover:border-blue-300 transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-sm text-slate-600 mt-1">{action.description}</p>
                  </div>
                  <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Pending Actions Alert */}
      {stats.pendingActions > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6">
          <div className="flex items-start gap-4">
            <div className="bg-yellow-100 rounded-full p-2">
              <Calendar className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-800">You have {stats.pendingActions} document(s) to sign</h3>
              <p className="text-yellow-700 mt-1">
                Please review and sign your contracts to keep your transaction moving forward.
              </p>
              <Link
                href="/portal/contracts"
                className="inline-flex items-center gap-2 mt-3 text-yellow-800 hover:text-yellow-900 font-medium"
              >
                View Contracts
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  icon: Icon,
  color,
  trend,
}: {
  title: string;
  value: number;
  icon: any;
  color: string;
  trend: string;
}) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-slate-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-slate-600">{title}</p>
          <p className="text-3xl font-bold text-slate-900 mt-2">{value}</p>
          <p className="text-xs text-slate-500 mt-1">{trend}</p>
        </div>
        <div className={`${color} rounded-full p-3`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );
}
