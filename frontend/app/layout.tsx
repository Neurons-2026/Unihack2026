import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "10min AI Daily",
  description: "Stay current in 10 minutes",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
