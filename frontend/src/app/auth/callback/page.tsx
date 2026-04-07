'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getSupabase } from '@/lib/supabase';
import { useAppStore } from '@/lib/store';

export default function AuthCallback() {
  const router = useRouter();
  const login = useAppStore((s) => s.login);

  useEffect(() => {
    const supabase = getSupabase();
    const code = new URLSearchParams(window.location.search).get('code');

    const finish = (session: import('@supabase/supabase-js').Session | null) => {
      if (session?.user) {
        login({
          userId: session.user.id,
          username: session.user.user_metadata?.full_name
            ?? session.user.email?.split('@')[0]
            ?? 'user',
        });
        router.replace('/');
      } else {
        router.replace('/login');
      }
    };

    if (code) {
      supabase.auth.exchangeCodeForSession(code).then(({ data }) => finish(data.session));
    } else {
      supabase.auth.getSession().then(({ data: { session } }) => finish(session));
    }
  }, [login, router]);

  return (
    <div className="min-h-screen bg-[#111111] flex items-center justify-center">
      <p className="text-[#888] text-sm">Signing you in…</p>
    </div>
  );
}
