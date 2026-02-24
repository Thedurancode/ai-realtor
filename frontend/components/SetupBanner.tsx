'use client';

import { useEffect, useState } from 'react';
import { Settings, AlertTriangle, X } from 'lucide-react';
import Link from 'next/link';

interface SetupStatus {
  configured: boolean;
  missing_required: string[];
}

export default function SetupBanner() {
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [dismissed, setDismissed] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const response = await fetch('/api/setup/status');
      const data = await response.json();

      // Ensure data has the expected structure
      setSetupStatus({
        configured: data?.configured || false,
        missing_required: data?.missing_required || []
      });
    } catch (error) {
      console.error('Failed to check setup status:', error);
      // Set default values on error to prevent crashes
      setSetupStatus({
        configured: false,
        missing_required: []
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading || !setupStatus || setupStatus.configured || dismissed) {
    return null;
  }

  const missingCount = setupStatus.missing_required?.length || 0;

  return (
    <div className="bg-gradient-to-r from-orange-500 to-red-600 text-white px-6 py-4 shadow-lg">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-4">
          <AlertTriangle className="w-6 h-6 flex-shrink-0" />
          <div>
            <p className="font-semibold text-lg">
              Setup Required
            </p>
            <p className="text-sm opacity-90">
              {missingCount} required API key{missingCount !== 1 ? 's are' : ' is'} missing
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/setup"
            className="px-4 py-2 bg-white text-orange-600 rounded-lg font-semibold hover:bg-orange-50 transition flex items-center gap-2"
          >
            <Settings className="w-4 h-4" />
            Complete Setup
          </Link>

          <button
            onClick={() => setDismissed(true)}
            className="p-2 hover:bg-white/10 rounded-lg transition"
            aria-label="Dismiss"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
