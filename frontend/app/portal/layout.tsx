'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Home,
  Building2,
  FileText,
  Clock,
  LogOut,
  User,
  Menu,
  X,
} from 'lucide-react';

export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('portal_token');
    const userData = localStorage.getItem('portal_user');

    if (!token || !userData) {
      router.push('/portal/login');
      return;
    }

    try {
      setUser(JSON.parse(userData));
    } catch {
      router.push('/portal/login');
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('portal_token');
    localStorage.removeItem('portal_user');
    router.push('/portal/login');
  };

  const navigation = [
    { name: 'Dashboard', href: '/portal/dashboard', icon: Home },
    { name: 'Properties', href: '/portal/properties', icon: Building2 },
    { name: 'Contracts', href: '/portal/contracts', icon: FileText },
    { name: 'Activity', href: '/portal/activity', icon: Clock },
  ];

  // Don't show layout for login/register pages
  if (pathname === '/portal/login' || pathname === '/portal/register') {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-0 left-0 z-50 h-full w-64 bg-slate-900 text-white transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:translate-x-0
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-slate-700">
            <h1 className="text-xl font-bold">AI Realtor</h1>
            <button
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden text-slate-400 hover:text-white"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* User Info */}
          {user && (
            <div className="p-4 border-b border-slate-700">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center">
                  <User className="w-5 h-5" />
                </div>
                <div>
                  <p className="font-medium">{user.full_name}</p>
                  <p className="text-sm text-slate-400 capitalize">{user.client_type}</p>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`
                    flex items-center gap-3 px-4 py-3 rounded-lg transition-colors
                    ${isActive ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'}
                  `}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-4 border-t border-slate-700">
            <button
              onClick={handleLogout}
              className="flex items-center gap-3 px-4 py-3 w-full text-left text-slate-300 hover:bg-slate-800 rounded-lg transition-colors"
            >
              <LogOut className="w-5 h-5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Bar */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
          <div className="flex items-center justify-between px-4 lg:px-8 h-16">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden text-slate-600 hover:text-slate-900"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex items-center gap-4">
              <div className="text-sm text-slate-600">
                Welcome back, <span className="font-medium text-slate-900">{user?.full_name}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
