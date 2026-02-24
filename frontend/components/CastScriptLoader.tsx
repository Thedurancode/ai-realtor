'use client';

import { useEffect } from 'react';

export function CastScriptLoader() {
  useEffect(() => {
    // Load Google Cast SDK
    if (typeof window !== 'undefined' && !document.querySelector('#cast-sdk')) {
      const script = document.createElement('script');
      script.id = 'cast-sdk';
      script.src = 'https://www.gstatic.com/cv/js/sender/v1/cast_sender.js?loadCastFramework=1';
      script.async = true;
      document.body.appendChild(script);
    }

    // Initialize Cast when SDK loads
    window['__onGCastApiAvailable'] = function(isAvailable: boolean) {
      if (isAvailable) {
        console.log('Google Cast API available');
        initializeCast();
      }
    };

    function initializeCast() {
      if (typeof (window as any).chrome?.cast !== 'undefined') {
        // Set up Cast framework
        console.log('Cast framework initialized');
      }
    }
  }, []);

  return null;
}
