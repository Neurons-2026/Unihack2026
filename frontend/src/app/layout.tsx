import type { Metadata, Viewport } from 'next';
import SplashWrapper from '@/components/SplashWrapper';
import './globals.css';

export const metadata: Metadata = { title: '10min AI Daily' };
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  userScalable: false,
  themeColor: '#111111',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#111111] text-white antialiased">
        <SplashWrapper>{children}</SplashWrapper>
      </body>
    </html>
  );
}
