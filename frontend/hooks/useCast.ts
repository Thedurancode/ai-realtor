'use client';

import { useState, useEffect, useCallback } from 'react';

interface CastDevice {
  id: string;
  name: string;
  type: 'chromecast' | 'airplay';
}

interface CastContext {
  isCasting: boolean;
  castDevice?: CastDevice;
  availableDevices: CastDevice[];
  startCast: (device: CastDevice) => void;
  stopCast: () => void;
  isSupported: boolean;
}

export function useCast(): CastContext {
  const [isCasting, setIsCasting] = useState(false);
  const [castDevice, setCastDevice] = useState<CastDevice | undefined>();
  const [availableDevices, setAvailableDevices] = useState<CastDevice[]>([]);
  const [isSupported, setIsSupported] = useState(false);

  // Check for Chromecast support
  useEffect(() => {
    // Check if Google Cast SDK is available
    const checkChromecast = () => {
      if (typeof window !== 'undefined' && (window as any).chrome) {
        // @ts-ignore - chrome.cast is not in the standard types
        if ((window as any).chrome?.cast?.isAvailable) {
          return true;
        }
      }
      return false;
    };

    // Check for AirPlay support (Safari/WebKit)
    const checkAirPlay = () => {
      if (typeof window !== 'undefined') {
        // @ts-ignore - webkitPresentationMode is not in standard types
        if ((window as any).WebKitPlaybackTargetAvailabilityEvent) {
          return true;
        }
      }
      return false;
    };

    const supported = checkChromecast() || checkAirPlay();
    setIsSupported(supported);

    if (supported) {
      scanForDevices();
    }
  }, []);

  const scanForDevices = useCallback(async () => {
    const devices: CastDevice[] = [];
    const scanned = new Set<string>();

    // Scan for Chromecast devices using mDNS/Browser
    try {
      // Try to use Google Cast API for real device discovery
      if (typeof window !== 'undefined' && (window as any).chrome?.cast?.isAvailable) {
        // Request device list
        await new Promise<void>((resolve, reject) => {
          // @ts-ignore
          const sessionRequest = new (window as any).chrome.cast.SessionRequest(
            process.env.NEXT_PUBLIC_CHROMECAST_APP_ID || 'DEFAULT',
            [window as any].chrome.cast.media.DEFAULT_MEDIA_SUPPORTED
          );

          // @ts-ignore
          const apiConfig = new (window as any).chrome.cast.ApiConfig(
            sessionRequest,
            (session: any) => {
              // Session started - device was found
              console.log('Chromecast session:', session);
              resolve();
            },
            (error: any) => {
              console.error('Chromecast error:', error);
              reject(error);
            },
            'default_sender_id'
          );

          // @ts-ignore
          (window as any).chrome.cast.initialize(apiConfig, () => {
            // Successfully initialized - now get device list
            // @ts-ignore
            if ((window as any).chrome.cast?.requestSession) {
              devices.push({
                id: 'chromecast-device',
                name: 'Chromecast Device',
                type: 'chromecast'
              });
              scanned.add('chromecast');
            }
            resolve();
          }, (error: any) => {
            console.log('Cast init error:', error);
            resolve();
          });
        });
      }
    } catch (error) {
      console.log('Chromecast scan error:', error);
    }

    // Scan for AirPlay devices using WebKit API
    try {
      if (typeof window !== 'undefined' && 'WebKitPlaybackTargetAvailabilityEvent' in window) {
        // Find video element or create hidden one
        let video = document.querySelector('video') as HTMLVideoElement;
        if (!video) {
          video = document.createElement('video');
          video.style.display = 'none';
          document.body.appendChild(video);
        }

        // Listen for AirPlay availability
        const checkAirPlay = () => {
          return new Promise<void>((resolve) => {
            // @ts-ignore
            video.addEventListener('webkitplaybacktargetavailabilitychanged', ((event: any) => {
              if (event.availability === 'available') {
                devices.push({
                  id: 'airplay-device',
                  name: 'AirPlay Receiver',
                  type: 'airplay'
                });
                scanned.add('airplay');
                resolve();
              } else {
                resolve();
              }
            }), { once: true });

            // Trigger the check
            // @ts-ignore
            if (video.webkitShowPlaybackTargetPicker) {
              // Don't actually show it, just trigger the check
              setTimeout(resolve, 1000);
            } else {
              resolve();
            }
          });
        };

        await checkAirPlay();
      }
    } catch (error) {
      console.log('AirPlay scan error:', error);
    }

    // Scan local network using fetch (limited CORS support)
    try {
      // Try common Chromecast local ports
      const chromecastPorts = [8008, 8009];
      for (const port of chromecastPorts) {
        try {
          // This will fail due to CORS, but the error tells us if something is listening
          await fetch(`http://localhost:${port}`, { mode: 'no-cors' });
          // If we got here without error, something responded
          if (!scanned.has('chromecast')) {
            devices.push({
              id: `chromecast-${port}`,
              name: `Chromecast (Port ${port})`,
              type: 'chromecast'
            });
            scanned.add('chromecast');
          }
        } catch (e) {
          // Expected to fail due to CORS
        }
      }
    } catch (error) {
      console.log('Local network scan error:', error);
    }

    setAvailableDevices(devices);
  }, []);

  const startCast = useCallback((device: CastDevice) => {
    if (device.type === 'chromecast') {
      startChromecast(device);
    } else if (device.type === 'airplay') {
      startAirPlay(device);
    }
  }, []);

  const stopCast = useCallback(() => {
    // Stop casting
    setIsCasting(false);
    setCastDevice(undefined);

    // Exit fullscreen if active
    if (document.fullscreenElement) {
      document.exitFullscreen();
    }
  }, []);

  const startChromecast = useCallback((device: CastDevice) => {
    try {
      // Request fullscreen for Chromecast
      document.documentElement.requestFullscreen();

      // Enter casting mode
      setIsCasting(true);
      setCastDevice(device);

      // Notify user
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('Casting Started', {
          body: `Now casting to ${device.name}`,
          icon: '/cast-icon.png'
        });
      }

      // Initialize Google Cast session
      if (typeof window !== 'undefined' && (window as any).chrome?.cast) {
        // @ts-ignore
        const sessionRequest = new (window as any).chrome.cast.SessionRequest(
          'YOUR_APP_ID', // Replace with your Chromecast App ID
          [window as any].chrome.cast.media.DEFAULT_MEDIA_SUPPORTED
        );

        // @ts-ignore
        const apiConfig = new (window as any).chrome.cast.ApiConfig(
          sessionRequest,
          (session: any) => {
            console.log('Cast session started:', session);
          },
          (error: any) => {
            console.error('Cast error:', error);
            stopCast();
          }
        );

        // @ts-ignore
        (window as any).chrome.cast.initialize(apiConfig);
      }
    } catch (error) {
      console.error('Failed to start Chromecast:', error);
      stopCast();
    }
  }, [stopCast]);

  const startAirPlay = useCallback((device: CastDevice) => {
    try {
      // Check for AirPlay support
      const video = document.querySelector('video');
      if (!video) {
        // If no video element, cast the entire page
        document.documentElement.requestFullscreen();
      } else {
        // @ts-ignore - webkitShowPlaybackTargetPicker is not in standard types
        if (video.webkitShowPlaybackTargetPicker) {
          video.webkitShowPlaybackTargetPicker();
        }
      }

      setIsCasting(true);
      setCastDevice(device);

      // Listen for AirPlay events
      if (video) {
        // @ts-ignore
        video.addEventListener('webkitplaybacktargetavailabilitychanged', (event: any) => {
          if (event.availability === 'available') {
            console.log('AirPlay available');
          }
        });

        // @ts-ignore
        video.addEventListener('webkitcurrentplaybacktargetiswirelesschanged', (event: any) => {
          setIsCasting(event.target.webkitCurrentPlaybackTargetIsWireless);
        });
      }

      // Notify user
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('AirPlay Started', {
          body: `Now streaming to ${device.name}`,
          icon: '/cast-icon.png'
        });
      }
    } catch (error) {
      console.error('Failed to start AirPlay:', error);
      stopCast();
    }
  }, [stopCast]);

  // Request notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  return {
    isCasting,
    castDevice,
    availableDevices,
    startCast,
    stopCast,
    isSupported
  };
}
