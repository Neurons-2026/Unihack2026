import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "10min AI Daily",
  description: "Swipe AI updates, build a 10-minute briefing",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50 text-slate-900">
        <div className="mx-auto max-w-5xl px-4 py-8 lg:px-8">{children}</div>
      </body>
    </html>
  );
}
