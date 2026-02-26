'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Eye,
  ExternalLink,
  Pen,
} from 'lucide-react';

interface Contract {
  id: number;
  title: string;
  property_id: number;
  status: string;
  is_required: boolean;
  can_sign: boolean;
  created_at: string;
  docuseal_signing_url?: string;
}

export default function PortalContractsPage() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      const token = localStorage.getItem('portal_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiUrl}/portal/contracts`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch contracts');
      }

      const data = await response.json();
      setContracts(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'sent':
      case 'pending_signature':
        return <Pen className="w-5 h-5 text-yellow-600" />;
      default:
        return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'sent':
      case 'pending_signature':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading contracts...</p>
        </div>
      </div>
    );
  }

  // Separate contracts: needs attention vs others
  const needsAction = contracts.filter((c) => c.can_sign && c.status === 'sent');
  const otherContracts = contracts.filter((c) => !needsAction.includes(c));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">My Contracts</h1>
        <p className="text-slate-600 mt-1">
          {contracts.length} {contracts.length === 1 ? 'contract' : 'contracts'} shared with you
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      )}

      {contracts.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No contracts yet</h3>
          <p className="text-slate-600">
            Your agent will share contracts with you here when they're ready.
          </p>
        </div>
      ) : (
        <>
          {/* Contracts Requiring Action */}
          {needsAction.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-yellow-800 mb-4 flex items-center gap-2">
                <AlertCircle className="w-5 h-5" />
                Action Required ({needsAction.length})
              </h2>
              <div className="space-y-4">
                {needsAction.map((contract) => (
                  <ContractCard key={contract.id} contract={contract} priority />
                ))}
              </div>
            </div>
          )}

          {/* Other Contracts */}
          {otherContracts.length > 0 && (
            <div>
              <h2 className="text-lg font-semibold text-slate-800 mb-4">
                All Contracts
              </h2>
              <div className="space-y-4">
                {otherContracts.map((contract) => (
                  <ContractCard key={contract.id} contract={contract} />
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ContractCard({ contract, priority = false }: { contract: Contract; priority?: boolean }) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'sent':
      case 'pending_signature':
        return <Pen className="w-5 h-5 text-yellow-600" />;
      default:
        return <Clock className="w-5 h-5 text-slate-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'sent':
      case 'pending_signature':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <div
      className={`bg-white rounded-xl shadow-sm border p-6 transition-all ${
        priority
          ? 'border-yellow-300 bg-yellow-50/50'
          : 'border-slate-200'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-start gap-4">
            <div
              className={`p-3 rounded-full ${
                priority ? 'bg-yellow-100' : 'bg-slate-100'
              }`}
            >
              {getStatusIcon(contract.status)}
            </div>
            <div className="flex-1">
              <h3 className="font-semibold text-lg text-slate-900">{contract.title}</h3>
              <p className="text-sm text-slate-600 mt-1">
                Property ID: {contract.property_id}
              </p>
              <div className="flex items-center gap-3 mt-3">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(
                    contract.status
                  )}`}
                >
                  {contract.status.replace(/_/g, ' ')}
                </span>
                {contract.is_required && (
                  <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium">
                    Required
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 ml-4">
          {contract.can_sign && contract.docuseal_signing_url ? (
            <a
              href={contract.docuseal_signing_url}
              target="_blank"
              rel="noopener noreferrer"
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                priority
                  ? 'bg-yellow-600 hover:bg-yellow-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              <Pen className="w-4 h-4" />
              {contract.status === 'completed' ? 'View' : 'Sign'}
            </a>
          ) : (
            <Link
              href={`/portal/contracts/${contract.id}`}
              className="flex items-center gap-2 px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-lg text-sm font-medium transition-colors"
            >
              <Eye className="w-4 h-4" />
              View
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
