'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  Building2,
  MapPin,
  Bed,
  Bath,
  Maximize,
  Home,
  Eye,
  FileText,
  Search,
} from 'lucide-react';

interface Property {
  id: number;
  property_id: number;
  access_level: string;
  relationship: string;
  can_view_price: boolean;
  can_sign_contracts: boolean;
  property: {
    id: number;
    title: string;
    address: string;
    city: string;
    state: string;
    zip_code: string;
    bedrooms?: number;
    bathrooms?: number;
    square_feet?: number;
    property_type?: string;
    status?: string;
    price?: number;
  };
  identifier: string; // Human-readable address for display
}

export default function PortalPropertiesPage() {
  const [properties, setProperties] = useState<Property[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchProperties();
  }, []);

  const fetchProperties = async () => {
    try {
      const token = localStorage.getItem('portal_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${apiUrl}/portal/properties`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch properties');
      }

      const data = await response.json();
      setProperties(data.map((p: any) => ({
        ...p,
        identifier: p.property ? `${p.property.address}, ${p.property.city}, ${p.property.state}` : '',
      })));
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
          <p className="text-slate-600">Loading properties...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">My Properties</h1>
          <p className="text-slate-600 mt-1">
            {properties.length} {properties.length === 1 ? 'property' : 'properties'} shared with you
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input
            type="text"
            placeholder="Search by address or city..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      )}

      {properties.length === 0 ? (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
          <Building2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-slate-900 mb-2">No properties yet</h3>
          <p className="text-slate-600">
            Your real estate agent will share properties with you here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {properties.map((item) => (
            <PropertyCard key={item.id} property={item} />
          ))}
        </div>
      )}
    </div>
  );
}

function PropertyCard({ property }: { property: Property }) {
  const prop = property.property;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow">
      {/* Property Image Placeholder */}
      <div className="h-48 bg-gradient-to-br from-blue-100 to-blue-200 relative">
        <div className="absolute inset-0 flex items-center justify-center">
          <Home className="w-16 h-16 text-blue-400" />
        </div>

        {/* Status Badge */}
        {prop.status && (
          <div className="absolute top-4 right-4">
            <span className="px-3 py-1 bg-white/90 backdrop-blur rounded-full text-xs font-medium text-slate-700 capitalize">
              {prop.status.replace(/_/g, ' ')}
            </span>
          </div>
        )}

        {/* Relationship Badge */}
        <div className="absolute bottom-4 left-4">
          <span className="px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-medium capitalize">
            {property.relationship}
          </span>
        </div>
      </div>

      {/* Property Details */}
      <div className="p-5">
        <h3 className="font-semibold text-lg text-slate-900 mb-1">{prop.title}</h3>
        <div className="flex items-start gap-2 text-slate-600 mb-4">
          <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
          <span className="text-sm">
            {prop.address}, {prop.city}, {prop.state} {prop.zip_code}
          </span>
        </div>

        {/* Features */}
        <div className="flex items-center gap-4 text-sm text-slate-600 mb-4">
          {prop.bedrooms !== null && prop.bedrooms !== undefined && (
            <div className="flex items-center gap-1">
              <Bed className="w-4 h-4" />
              <span>{prop.bedrooms} bed</span>
            </div>
          )}
          {prop.bathrooms !== null && prop.bathrooms !== undefined && (
            <div className="flex items-center gap-1">
              <Bath className="w-4 h-4" />
              <span>{prop.bathrooms} bath</span>
            </div>
          )}
          {prop.square_feet && (
            <div className="flex items-center gap-1">
              <Maximize className="w-4 h-4" />
              <span>{prop.square_feet.toLocaleString()} sqft</span>
            </div>
          )}
        </div>

        {/* Price (if visible) */}
        {property.can_view_price && prop.price && (
          <div className="mb-4">
            <span className="text-2xl font-bold text-slate-900">
              ${prop.price.toLocaleString()}
            </span>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2 pt-4 border-t border-slate-100">
          <Link
            href={`/portal/properties/${property.property_id}`}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Eye className="w-4 h-4" />
            View Details
          </Link>
          {property.can_sign_contracts && (
            <Link
              href="/portal/contracts"
              className="flex items-center justify-center gap-2 px-4 py-2 border border-slate-200 hover:bg-slate-50 rounded-lg text-sm font-medium transition-colors"
            >
              <FileText className="w-4 h-4" />
              Contracts
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
