'use client'

import { Property } from '@/store/useAgentStore'
import { useEffect, useState } from 'react'

interface PropertyDetailViewProps {
  property: Property
  onClose: () => void
}

export const PropertyDetailView: React.FC<PropertyDetailViewProps> = ({ property, onClose }) => {
  const [isVisible, setIsVisible] = useState(false)
  const [currentPhotoIndex, setCurrentPhotoIndex] = useState(0)

  const zillow = property.zillow_enrichment
  const skipTrace = property.skip_traces?.[0] // Get the most recent skip trace
  const photos = zillow?.photos || []

  useEffect(() => {
    // Trigger animation after mount
    setTimeout(() => setIsVisible(true), 50)
  }, [])

  useEffect(() => {
    // Auto-advance photos every 5 seconds
    if (photos.length > 1) {
      const interval = setInterval(() => {
        setCurrentPhotoIndex((prev) => (prev + 1) % photos.length)
      }, 5000)
      return () => clearInterval(interval)
    }
  }, [photos.length])

  const nextPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev + 1) % photos.length)
  }

  const prevPhoto = () => {
    setCurrentPhotoIndex((prev) => (prev - 1 + photos.length) % photos.length)
  }

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm transition-opacity duration-500 overflow-y-auto ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      onClick={onClose}
    >
      <div
        className={`relative w-full max-w-7xl mx-8 my-8 bg-gradient-to-br from-news-blue via-primary to-news-blue border-4 border-secondary rounded-2xl shadow-2xl shadow-secondary/50 transition-all duration-500 ${
          isVisible ? 'scale-100 translate-y-0' : 'scale-95 translate-y-8'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with LIVE badge */}
        <div className="bg-gradient-to-r from-secondary to-news-orange p-6 rounded-t-xl border-b-4 border-news-cyan">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-white text-secondary px-4 py-2 rounded-lg font-black text-sm uppercase flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-secondary animate-flash" />
                FEATURED PROPERTY
              </div>
              <span className="text-white text-2xl font-bold">#{property.id}</span>
              {zillow?.zpid && (
                <span className="text-white/70 text-lg">ZPID: {zillow.zpid}</span>
              )}
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-news-cyan text-3xl font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Main Content - Scrollable */}
        <div className="max-h-[calc(100vh-200px)] overflow-y-auto p-8 space-y-8">
          {/* Photo Gallery */}
          {photos.length > 0 && (
            <div className="relative w-full h-96 bg-black rounded-xl overflow-hidden border-4 border-white/20">
              <img
                src={photos[currentPhotoIndex]}
                alt={`Property photo ${currentPhotoIndex + 1}`}
                className="w-full h-full object-cover"
              />

              {/* Photo Navigation */}
              {photos.length > 1 && (
                <>
                  <button
                    onClick={prevPhoto}
                    className="absolute left-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full text-2xl transition-all"
                  >
                    ←
                  </button>
                  <button
                    onClick={nextPhoto}
                    className="absolute right-4 top-1/2 -translate-y-1/2 bg-black/50 hover:bg-black/70 text-white p-3 rounded-full text-2xl transition-all"
                  >
                    →
                  </button>
                  <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-black/70 px-4 py-2 rounded-full text-white font-bold">
                    {currentPhotoIndex + 1} / {photos.length}
                  </div>
                </>
              )}

              {/* View on Zillow */}
              {zillow?.zillow_url && (
                <a
                  href={zillow.zillow_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute top-4 right-4 bg-accent hover:bg-accent/80 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2 transition-all"
                >
                  🏠 View on Zillow
                </a>
              )}
            </div>
          )}

          {/* Property Header */}
          <div>
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h1 className="text-5xl font-black text-white mb-3 leading-tight">
                  {property.address}
                </h1>
                <p className="text-2xl text-gray-300">
                  {property.city}, {property.state} {property.zip_code}
                </p>
              </div>
              <div className="text-right">
                <div className="text-6xl font-black text-accent mb-2">
                  ${property.price.toLocaleString()}
                </div>
                {zillow?.zestimate && (
                  <div className="text-xl text-news-cyan mb-2">
                    Zestimate: ${zillow.zestimate.toLocaleString()}
                  </div>
                )}
                {zillow?.rent_zestimate && (
                  <div className="text-lg text-gray-400 mb-2">
                    Rent Est: ${zillow.rent_zestimate.toLocaleString()}/mo
                  </div>
                )}
                <div className="inline-block bg-primary text-white px-4 py-2 rounded-lg text-xl font-bold uppercase">
                  {property.status}
                </div>
              </div>
            </div>
          </div>

          {/* Property Details Grid */}
          <div className="grid grid-cols-4 gap-6">
            <div className="bg-white/10 backdrop-blur border-2 border-white/20 rounded-xl p-6 text-center hover:border-secondary transition-all">
              <div className="text-5xl mb-3">🛏️</div>
              <div className="text-4xl font-black text-white mb-2">
                {property.bedrooms || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 uppercase font-bold">Bedrooms</div>
            </div>

            <div className="bg-white/10 backdrop-blur border-2 border-white/20 rounded-xl p-6 text-center hover:border-secondary transition-all">
              <div className="text-5xl mb-3">🛁</div>
              <div className="text-4xl font-black text-white mb-2">
                {property.bathrooms || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 uppercase font-bold">Bathrooms</div>
            </div>

            <div className="bg-white/10 backdrop-blur border-2 border-white/20 rounded-xl p-6 text-center hover:border-secondary transition-all">
              <div className="text-5xl mb-3">📐</div>
              <div className="text-4xl font-black text-white mb-2">
                {(zillow?.living_area || property.square_feet)?.toLocaleString() || 'N/A'}
              </div>
              <div className="text-sm text-gray-400 uppercase font-bold">Living Area</div>
            </div>

            <div className="bg-white/10 backdrop-blur border-2 border-white/20 rounded-xl p-6 text-center hover:border-secondary transition-all">
              <div className="text-5xl mb-3">🏡</div>
              <div className="text-3xl font-black text-white mb-2">
                {zillow?.home_type || property.property_type || 'House'}
              </div>
              <div className="text-sm text-gray-400 uppercase font-bold">Type</div>
            </div>
          </div>

          {/* Zillow Enrichment Data */}
          {zillow && (
            <div className="grid grid-cols-2 gap-6">
              {/* Property Facts */}
              <div className="bg-white/5 border border-white/20 rounded-xl p-6">
                <h3 className="text-2xl font-bold text-news-cyan mb-4 uppercase flex items-center gap-2">
                  📊 Property Facts
                </h3>
                <div className="space-y-3">
                  {zillow.lot_size && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Lot Size:</span>
                      <span className="text-white font-semibold">
                        {zillow.lot_size.toLocaleString()} {zillow.lot_area_units || 'sqft'}
                      </span>
                    </div>
                  )}
                  {zillow.year_built && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Year Built:</span>
                      <span className="text-white font-semibold">{zillow.year_built}</span>
                    </div>
                  )}
                  {zillow.home_status && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Status:</span>
                      <span className="text-white font-semibold capitalize">{zillow.home_status}</span>
                    </div>
                  )}
                  {zillow.days_on_zillow !== undefined && zillow.days_on_zillow !== null && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Days on Zillow:</span>
                      <span className="text-white font-semibold">{zillow.days_on_zillow}</span>
                    </div>
                  )}
                  {zillow.page_view_count !== undefined && zillow.page_view_count !== null && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Page Views:</span>
                      <span className="text-white font-semibold">{zillow.page_view_count.toLocaleString()}</span>
                    </div>
                  )}
                  {zillow.favorite_count !== undefined && zillow.favorite_count !== null && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Favorites:</span>
                      <span className="text-white font-semibold">{zillow.favorite_count}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Tax Information */}
              <div className="bg-white/5 border border-white/20 rounded-xl p-6">
                <h3 className="text-2xl font-bold text-news-cyan mb-4 uppercase flex items-center gap-2">
                  💰 Tax Information
                </h3>
                <div className="space-y-3">
                  {zillow.annual_tax_amount && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Annual Tax:</span>
                      <span className="text-white font-semibold">${zillow.annual_tax_amount.toLocaleString()}</span>
                    </div>
                  )}
                  {zillow.property_tax_rate && (
                    <div className="flex justify-between text-lg">
                      <span className="text-gray-400">Tax Rate:</span>
                      <span className="text-white font-semibold">{(zillow.property_tax_rate * 100).toFixed(2)}%</span>
                    </div>
                  )}
                </div>

                {zillow.tax_history && zillow.tax_history.length > 0 && (
                  <>
                    <h4 className="text-lg font-bold text-white mt-4 mb-2">Tax History</h4>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {zillow.tax_history.slice(0, 5).map((tax: any, idx: number) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="text-gray-400">{tax.year || tax.time}:</span>
                          <span className="text-white">${tax.amount?.toLocaleString() || tax.taxPaid?.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Description */}
          {(zillow?.description || property.description) && (
            <div className="bg-white/5 border border-white/20 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-news-cyan mb-3 uppercase">Description</h3>
              <p className="text-xl text-gray-300 leading-relaxed">
                {zillow?.description || property.description}
              </p>
            </div>
          )}

          {/* Schools */}
          {zillow?.schools && zillow.schools.length > 0 && (
            <div className="bg-white/5 border border-white/20 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-news-cyan mb-4 uppercase flex items-center gap-2">
                🎓 Nearby Schools
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {zillow.schools.slice(0, 5).map((school: any, idx: number) => (
                  <div key={idx} className="bg-white/5 border border-white/10 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="text-lg font-bold text-white">{school.name}</div>
                        <div className="text-sm text-gray-400">
                          {school.grades} • {school.level} • {school.distance?.toFixed(1)} mi
                        </div>
                      </div>
                      {school.rating && (
                        <div className="bg-accent text-white px-3 py-1 rounded-full font-bold">
                          ⭐ {school.rating}/10
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price History */}
          {zillow?.price_history && zillow.price_history.length > 0 && (
            <div className="bg-white/5 border border-white/20 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-news-cyan mb-4 uppercase flex items-center gap-2">
                📈 Price History
              </h3>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {zillow.price_history.slice(0, 10).map((history: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center border-b border-white/10 pb-2">
                    <div>
                      <div className="text-white font-semibold">{history.event || history.type}</div>
                      <div className="text-sm text-gray-400">
                        {new Date(history.date || history.time).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="text-accent font-bold text-lg">
                      ${history.price?.toLocaleString() || history.priceChangeRate?.toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Skip Trace / Owner Information */}
          {skipTrace && (
            <div className="bg-gradient-to-r from-news-orange/20 to-secondary/20 border-2 border-secondary rounded-xl p-6">
              <h3 className="text-2xl font-bold text-secondary mb-4 uppercase flex items-center gap-2">
                👤 Owner Information
              </h3>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-bold text-white mb-3">Contact Details</h4>
                  <div className="space-y-2">
                    {skipTrace.owner_name && (
                      <div className="text-lg">
                        <span className="text-gray-400">Name: </span>
                        <span className="text-white font-semibold">{skipTrace.owner_name}</span>
                      </div>
                    )}
                    {skipTrace.phone_numbers && skipTrace.phone_numbers.length > 0 && (
                      <div>
                        <div className="text-gray-400 mb-1">Phone Numbers:</div>
                        {skipTrace.phone_numbers.map((phone: any, idx: number) => (
                          <div key={idx} className="text-white ml-4">
                            📞 {phone.number || phone} {phone.type && `(${phone.type})`}
                          </div>
                        ))}
                      </div>
                    )}
                    {skipTrace.emails && skipTrace.emails.length > 0 && (
                      <div>
                        <div className="text-gray-400 mb-1">Emails:</div>
                        {skipTrace.emails.map((email: any, idx: number) => (
                          <div key={idx} className="text-white ml-4">
                            ✉️ {email.email || email}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  <h4 className="text-lg font-bold text-white mb-3">Mailing Address</h4>
                  {skipTrace.mailing_address ? (
                    <div className="text-white space-y-1">
                      <div>{skipTrace.mailing_address}</div>
                      <div>
                        {skipTrace.mailing_city}, {skipTrace.mailing_state} {skipTrace.mailing_zip}
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-400 italic">Same as property address</div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Property Timeline */}
          <div className="bg-white/5 border border-white/20 rounded-xl p-6">
            <h3 className="text-2xl font-bold text-news-cyan mb-4 uppercase">Timeline</h3>
            <div className="space-y-3">
              {property.created_at && (
                <div className="flex items-center justify-between text-lg">
                  <span className="text-gray-400">Listed:</span>
                  <span className="text-white font-semibold">
                    {new Date(property.created_at).toLocaleString()}
                  </span>
                </div>
              )}
              {property.updated_at && (
                <div className="flex items-center justify-between text-lg">
                  <span className="text-gray-400">Last Updated:</span>
                  <span className="text-white font-semibold">
                    {new Date(property.updated_at).toLocaleString()}
                  </span>
                </div>
              )}
              {zillow?.created_at && (
                <div className="flex items-center justify-between text-lg">
                  <span className="text-gray-400">Zillow Enriched:</span>
                  <span className="text-white font-semibold">
                    {new Date(zillow.created_at).toLocaleString()}
                  </span>
                </div>
              )}
              {skipTrace?.created_at && (
                <div className="flex items-center justify-between text-lg">
                  <span className="text-gray-400">Skip Traced:</span>
                  <span className="text-white font-semibold">
                    {new Date(skipTrace.created_at).toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gradient-to-r from-news-blue to-primary p-4 rounded-b-xl border-t-2 border-white/20">
          <p className="text-center text-sm text-gray-400">
            Press ESC or click outside to close • Property ID: #{property.id}
            {zillow && ' • Enhanced with Zillow Data'}
            {skipTrace && ' • Owner Contact Available'}
          </p>
        </div>
      </div>
    </div>
  )
}
