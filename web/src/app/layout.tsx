import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Press_Start_2P, VT323, Silkscreen } from "next/font/google";
import "./globals.css";
import Tabs from "../components/tabs";
import bgImage from "../assets/qr-bg.jpg";

const tabs = [
  { label: "Game Play", href: "/gameplay" },
  { label: "Interface", href: "/interface" },
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

// Pixelated font options
const pressStart2P = Press_Start_2P({
  weight: "400",
  variable: "--font-press-start",
  subsets: ["latin"],
});

const vt323 = VT323({
  weight: "400",
  variable: "--font-vt323",
  subsets: ["latin"],
});

const silkscreen = Silkscreen({
  weight: ["400", "700"],
  variable: "--font-silkscreen",
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
        className={`${geistSans.variable} ${geistMono.variable} ${pressStart2P.variable} ${vt323.variable} 
        ${silkscreen.variable} antialiased bg-[var(--background)] text-[var(--text-primary)]`}
      >
        <div className="max-w-4xl mx-auto p-6 pt-0">
          <div
            className="bg-cover bg-center mb-6 p-6 pb-0"
            style={{ backgroundImage: `url(${bgImage.src})` }}
          >
            <h1 className="text-3xl mb-8 pixel-text">Quadradius Guide</h1>
            <Tabs tabs={tabs} />
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
