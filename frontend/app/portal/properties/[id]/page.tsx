'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  MapPin,
  Bed,
  Bath,
  Maximize,
  Calendar,
  Home,
  FileText,
  Download,
} from 'lucide-react';

interface PropertyDetail {
  id: number;
  title: string;
  description?: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  price?: number;
  bedrooms?: number;
  bathrooms?: number;
  square_feet?: number;
  lot_size?: number;
  year_built?: number;
  property_type?: string;
  status?: string;
  access_level: string;
  relationship: string;
  can_view_price: boolean;
  contracts?: Array<{
    id: number;
    title: string;
    status: string;
    is_required: boolean;
    can_sign: boolean;
  }>;
}

export default function PropertyDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const [property, setProperty] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (params.id) {
      fetchProperty(params.id);
    }
  }, [params.id]);

  const fetchProperty = async (id: string) => {
    try {
      const token = localStorage.getItem('portal_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiUrl}/portal/properties/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        if (response.status === 403) {
          throw new Error('You do not have permission to view this property');
        }
        throw new Error('Failed to fetch property details');
      }

      const data = await response.json();
      setProperty(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading property details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
        <p className="text-red-800 mb-4">{error}</p>
        <Link
          href="/portal/properties"
          className="inline-flex items-center gap-2 text-red-700 hover:text-red-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Properties
        </Link>
      </div>
    );
  }

  if (!property) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Link
        href="/portal/properties"
        className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Properties
      </Link>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {/* Hero Image Placeholder */}
        <div className="h-80 bg-gradient-to-br from-blue-100 to-blue-200 relative">
          <div className="absolute inset-0 flex items-center justify-center">
            <Home className="w-24 h-24 text-blue-400" />
          </div>

          {/* Status Badge */}
          {property.status && (
            <div className="absolute top-6 right-6">
              <span className="px-4 py-2 bg-white/90 backdrop-blur rounded-full text-sm font-medium text-slate-700 capitalize">
                {property.status.replace(/_/g, ' ')}
              </span>
            </div>
          )}

          {/* Relationship Badge */}
          <div className="absolute bottom-6 left-6">
            <span className="px-4 py-2 bg-blue-600 text-white rounded-full text-sm font-medium capitalize">
              You are the {property.relationship}
            </span>
          </div>
        </div>

        {/* Property Info */}
        <div className="p-8">
          <h1 className="text-3xl font-bold text-slate-900 mb-2">{property.title}</h1>

          <div className="flex items-center gap-2 text-slate-600 mb-6">
            <MapPin className="w-5 h-5" />
            <span>
              {property.address}, {property.city}, {property.state} {property.zip_code}
            </span>
          </div>

          {/* Price */}
          {property.can_view_price && property.price && (
            <div className="mb-6">
              <span className="text-4xl font-bold text-slate-900">
                ${property.price.toLocaleString()}
              </span>
            </div>
          )}

          {/* Features Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {property.bedrooms !== null && property.bedrooms !== undefined && (
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg">
                <Bed className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="text-sm text-slate-600">Bedrooms</p>
                  <p className="font-semibold text-slate-900">{property.bedrooms}</p>
                </div>
              </div>
            )}
            {property.bathrooms !== null && property.bathrooms !== undefined && (
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg">
                <Bath className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="text-sm text-slate-600">Bathrooms</p>
                  <p className="font-semibold text-slate-900">{property.bathrooms}</p>
                </div>
              </div>
            )}
            {property.square_feet && (
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg">
                <Maximize className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="text-sm text-slate-600">Square Feet</p>
                  <p className="font-semibold text-slate-900">
                    {property.square_feet.toLocaleString()}
                  </p>
                </div>
              </div>
            )}
            {property.year_built && (
              <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg">
                <Calendar className="w-5 h-5 text-slate-600" />
                <div>
                  <p className="text-sm text-slate-600">Year Built</p>
                  <p className="font-semibold text-slate-900">{property.year_built}</p>
                </div>
              </div>
            )}
          </div>

          {/* Description */}
          {property.description && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-slate-900 mb-3">About This Property</h2>
              <p className="text-slate-600 leading-relaxed">{property.description}</p>
            </div>
          )}

          {/* Contracts Section */}
          {property.contracts && property.contracts.length > 0 && (
            <div>
              <h2 className="text-xl font-semibold text-slate-900 mb-4">Related Contracts</h2>
              <div className="space-y-3">
                {property.contracts.map((contract) => (
                  <div
                    key={contract.id}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200"
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-slate-600" />
                      <div>
                        <p className="font-medium text-slate-900">{contract.title}</p>
                        <p className="text-sm text-slate-600 capitalize">{contract.status.replace(/_/g, ' ')}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {contract.is_required && (
                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs rounded">Required</span>
                      )}
                      {contract.can_sign && contract.status === 'sent' && (
                        <Link
                          href={`/portal/contracts/${contract.id}`}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                        >
                          Sign Now
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
