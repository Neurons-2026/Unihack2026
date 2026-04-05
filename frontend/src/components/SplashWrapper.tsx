'use client';

import { useState, useCallback, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import SplashScreen from './SplashScreen';
import { resetSessionId, getStoredUser } from '@/lib/session';

export default function SplashWrapper({ children }: { children: React.ReactNode }) {
  const [splashDone, setSplashDone] = useState<boolean>(false);
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    const handleLeave = () => resetSessionId();
    window.addEventListener('pagehide', handleLeave);
    return () => window.removeEventListener('pagehide', handleLeave);
  }, []);

  const handleComplete = useCallback(() => {
    setSplashDone(true);
    if (pathname !== '/login' && !getStoredUser()) {
      router.replace('/login');
    }
  }, [pathname, router]);

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
