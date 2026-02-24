'use client';

import { useState, useEffect } from 'react';

interface Device {
  id: string;
  name: string;
  type: 'chromecast' | 'airplay';
}

export default function CastButton() {
  const [isCasting, setIsCasting] = useState(false);
  const [currentDevice, setCurrentDevice] = useState<Device | null>(null);
  const [showMenu, setShowMenu] = useState(false);
  const [chromecastSupported, setChromecastSupported] = useState(false);
  const [airplaySupported, setAirplaySupported] = useState(false);

  useEffect(() => {
    // Check for Chromecast support
    if (typeof window !== 'undefined') {
      setChromecastSupported('chrome' in window || 'chromecast' in window);

      // Check for AirPlay support
      const video = document.createElement('video');
      // @ts-ignore
      setAirplaySupported('webkitShowPlaybackTargetPicker' in video);
    }
  }, []);

  const startChromecast = async () => {
    try {
      // Use the browser's native Cast picker
      // @ts-ignore
      if (navigator.presentation && navigator.presentation.request) {
        // @ts-ignore
        await navigator.presentation.defaultRequest.start();
        setIsCasting(true);
        setCurrentDevice({ id: 'chromecast', name: 'Chromecast', type: 'chromecast' });
      }
      // Fallback: Use Google Cast SDK if available
      else if ((window as any).chrome?.cast?.requestSession) {
        // @ts-ignore
        const session = await (window as any).chrome.cast.requestSession((session: any) => {
          setIsCasting(true);
          setCurrentDevice({ id: session.id, name: session.friendlyName, type: 'chromecast' });
        }, (error: any) => {
          console.error('Cast error:', error);
        });
      }
      else {
        // Manual instruction
        alert('Click the Cast button in your browser toolbar (three dots → Cast)');
        window.open('https://support.google.com/chromecast/answer/2979359', '_blank');
      }
    } catch (error) {
      console.error('Chromecast error:', error);
    }
  };

  const startAirPlay = async () => {
    try {
      // Create a video element for AirPlay
      let video = document.querySelector('video') as HTMLVideoElement;
      if (!video) {
        video = document.createElement('video');
        video.style.display = 'none';
        document.body.appendChild(video);
      }

      // @ts-ignore - Use WebKit's native AirPlay picker
      if (video.webkitShowPlaybackTargetPicker) {
        video.webkitShowPlaybackTargetPicker();

        // Listen for connection
        // @ts-ignore
        video.addEventListener('webkitcurrentplaybacktargetiswirelesschanged', (event: any) => {
          // @ts-ignore
          if (video.webkitCurrentPlaybackTargetIsWireless) {
            setIsCasting(true);
            setCurrentDevice({ id: 'airplay', name: 'AirPlay Device', type: 'airplay' });
          } else {
            setIsCasting(false);
            setCurrentDevice(null);
          }
        });
      }
    } catch (error) {
      console.error('AirPlay error:', error);
      alert('Make sure you\'re using Safari on macOS/iOS');
    }
  };

  const stopCast = () => {
    // Stop fullscreen
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }

    setIsCasting(false);
    setCurrentDevice(null);

    // Stop AirPlay if active
    const video = document.querySelector('video') as HTMLVideoElement;
    if (video) {
      // @ts-ignore
      if (video.webkitCurrentPlaybackTargetIsWireless) {
        // @ts-ignore
        video.webkitSetPlaybackTarget(null);
      }
    }
  };

  if (!chromecastSupported && !airplaySupported) {
    return null;
  }

  return (
    <div className="fixed top-6 right-6 z-50">
      <div className="relative">
        {/* Cast Button */}
        {!isCasting ? (
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-4 bg-white/90 backdrop-blur-sm rounded-full shadow-2xl hover:bg-white hover:scale-110 transition-all duration-300"
            title="Cast to TV"
          >
            <svg className="w-6 h-6 text-gray-800" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 14H3V5h18v12zM4 12c0-4.42 3.58-8 8-8v2c-3.31 0-6 2.69-6 6H4zm3.52 0c0-2.48 2.02-4.5 4.5-4.5v2c-1.38 0-2.5 1.12-2.5 2.5H7.52zM19 12h-2c0-2.48-2.02-4.5-4.5-4.5v-2c3.31 0 6 2.69 6 6z"/>
            </svg>
          </button>
        ) : (
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full shadow-2xl animate-pulse"
            title={`Connected to ${currentDevice?.name}`}
          >
            <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21 3H3c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h5v2h8v-2h5c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 14H3V5h18v12z"/>
            </svg>
          </button>
        )}

        {/* Device Menu */}
        {showMenu && (
          <>
            <div
              className="fixed inset-0 z-0"
              onClick={() => setShowMenu(false)}
            />
            <div className="absolute right-0 mt-2 w-80 bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-200 p-4 z-10">
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
                      <p className="font-semibold text-green-900">{currentDevice?.name}</p>
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
                <div className="space-y-3">
                  <p className="text-sm text-gray-600 mb-3">Choose a casting method:</p>

                  {chromecastSupported && (
                    <button
                      onClick={() => {
                        startChromecast();
                        setShowMenu(false);
                      }}
                      className="w-full flex items-center gap-3 p-4 hover:bg-gray-100 rounded-lg transition-colors text-left border-2 border-gray-200 hover:border-blue-500"
                    >
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-700 rounded-xl flex items-center justify-center text-white text-2xl">
                        📺
                      </div>
                      <div className="flex-1">
                        <p className="font-bold text-gray-900">Chromecast</p>
                        <p className="text-sm text-gray-500">Google Cast devices</p>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  )}

                  {airplaySupported && (
                    <button
                      onClick={() => {
                        startAirPlay();
                        setShowMenu(false);
                      }}
                      className="w-full flex items-center gap-3 p-4 hover:bg-gray-100 rounded-lg transition-colors text-left border-2 border-gray-200 hover:border-gray-800"
                    >
                      <div className="w-12 h-12 bg-gradient-to-br from-gray-800 to-gray-900 rounded-xl flex items-center justify-center text-white text-2xl">
                        📱
                      </div>
                      <div className="flex-1">
                        <p className="font-bold text-gray-900">AirPlay</p>
                        <p className="text-sm text-gray-500">Apple TV & AirPlay devices</p>
                      </div>
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  )}

                  {!chromecastSupported && !airplaySupported && (
                    <p className="text-gray-500 text-sm text-center py-4">
                      No casting support detected. Use Chrome for Chromecast or Safari for AirPlay.
                    </p>
                  )}
                </div>
              )}

              {/* Instructions */}
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-xs text-gray-500">
                  💡 <strong>Tip:</strong> Clicking will open your browser's built-in device picker with all available devices
                </p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
