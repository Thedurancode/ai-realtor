'use client';

import { useState, useEffect, useRef } from 'react';
import { CastButton, CastController, useCast } from '@/hooks/useCast';

export default function CastControls() {
  const {
    isCasting,
    castDevice,
    availableDevices,
    startCast,
    stopCast,
    isSupported
  } = useCast();

  const [showMenu, setShowMenu] = useState(false);

  if (!isSupported) {
    return null;
  }

  return (
    <div className="fixed top-6 right-6 z-50">
      <div className="relative">
        {/* Cast Button */}
        <button
          onClick={() => setShowMenu(!showMenu)}
          className={`
            p-4 rounded-full shadow-2xl transition-all duration-300
            ${isCasting
              ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white animate-pulse'
              : 'bg-white/90 backdrop-blur-sm text-gray-800 hover:bg-white'
            }
          `}
          title={isCasting ? 'Connected to ' + castDevice?.name : 'Cast to device'}
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
            {isCasting ? (
              // Connected icon
              <path d="M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 14H3V5h18v12z"/>
            ) : (
              // Cast icon
              <path d="M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 14H3V5h18v12zM4 12c0-4.42 3.58-8 8-8v2c-3.31 0-6 2.69-6 6H4zm3.52 0c0-2.48 2.02-4.5 4.5-4.5v2c-1.38 0-2.5 1.12-2.5 2.5H7.52zM19 12h-2c0-2.48-2.02-4.5-4.5-4.5v-2c3.31 0 6 2.69 6 6z"/>
            )}
          </svg>
        </button>

        {/* Device Menu */}
        {showMenu && (
          <div className="absolute right-0 mt-2 w-80 bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-200 p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-900">Cast to Device</h3>
              <button
                onClick={() => setShowMenu(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {isCasting ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                  <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  <div className="flex-1">
                    <p className="font-semibold text-green-900">{castDevice?.name}</p>
                    <p className="text-sm text-green-700">Connected</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    stopCast();
                    setShowMenu(false);
                  }}
                  className="w-full py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-semibold transition-colors"
                >
                  Disconnect
                </button>
              </div>
            ) : (
              <div className="space-y-2">
                <p className="text-sm text-gray-600 mb-3">Select a device to cast to:</p>
                {availableDevices.length === 0 ? (
                  <p className="text-gray-500 text-sm">No devices available. Make sure your Chromecast or AirPlay device is on the same network.</p>
                ) : (
                  availableDevices.map((device) => (
                    <button
                      key={device.id}
                      onClick={() => {
                        startCast(device);
                        setShowMenu(false);
                      }}
                      className="w-full flex items-center gap-3 p-3 hover:bg-gray-100 rounded-lg transition-colors text-left"
                    >
                      <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white">
                        {device.type === 'chromecast' ? '📺' : '📱'}
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold text-gray-900">{device.name}</p>
                        <p className="text-sm text-gray-500">{device.type}</p>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}

            {/* Instructions */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                💡 Tip: For best quality, use Chrome/Edge for Chromecast or Safari for AirPlay
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
