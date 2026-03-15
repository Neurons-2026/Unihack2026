'use client';

import { useState, useCallback } from 'react';
import SplashScreen from './SplashScreen';

export default function SplashWrapper({ children }: { children: React.ReactNode }) {
  const [splashDone, setSplashDone] = useState<boolean>(false);

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
