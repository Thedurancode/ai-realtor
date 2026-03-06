'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function PortalLoginPage() {
  const router = useRouter();

  useEffect(() => {
    // Auth disabled for development - redirect straight to dashboard
    router.replace('/portal/dashboard');
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <p className="text-white">Redirecting to dashboard...</p>
    </div>
  );
}
