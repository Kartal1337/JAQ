import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI SDR Assistant',
  description: 'Find leads, write personalized outreach, book meetings — on autopilot.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
