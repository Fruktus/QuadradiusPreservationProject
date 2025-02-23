import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Tabs from "./orbs/components/tabs";

const tabs = [
  { label: "Interface", href: "/interface" },
  { label: "Game Play", href: "/gameplay" },
  { label: "Advanced Training", href: "/advanced" },
  { label: "Basic Training", href: "/basic" },
  { label: "Orbs", href: "/orbs" },
  { label: "Members", href: "/members" },
];

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Quadradius",
  description:
    "A restoration of the classic online strategy game Quadradius, featuring its gameplay mechanics and unique power-ups.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[var(--background)] text-[var(--text-primary)]`}
      >
        <div className="max-w-4xl mx-auto p-6">
          <h1 className="text-3xl font-bold mb-8 text-white">
            Quadradius Guide
          </h1>
          <Tabs tabs={tabs} />
          {children}
        </div>
      </body>
    </html>
  );
}
