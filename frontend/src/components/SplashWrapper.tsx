'use client';

import { useState, useCallback, useEffect } from 'react';
import SplashScreen from './SplashScreen';
import { resetSessionId } from '@/lib/session';

export default function SplashWrapper({ children }: { children: React.ReactNode }) {
  const [splashDone, setSplashDone] = useState<boolean>(false);

  useEffect(() => {
    const handleLeave = () => resetSessionId();
    window.addEventListener('pagehide', handleLeave);
    return () => window.removeEventListener('pagehide', handleLeave);
  }, []);

  const handleComplete = useCallback(() => {
    setSplashDone(true);
  }, []);

  return (
    <>
      {!splashDone && <SplashScreen onComplete={handleComplete} />}
      <div
        style={{
          opacity: splashDone ? 1 : 0,
          transition: 'opacity 0.5s ease-in-out',
        }}
      >
        {children}
      </div>
    </>
  );
}
