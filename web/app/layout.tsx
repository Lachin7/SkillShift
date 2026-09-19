import type { Metadata } from "next";
import { Fraunces, IBM_Plex_Sans, Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-ui",
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-serif",
});

const ibmPlex = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-plex",
});

export const metadata: Metadata = {
  title: "SkillShift",
  description: "Skill = WHAT. Adapter = HOW HERE.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${outfit.variable} ${fraunces.variable} ${ibmPlex.variable}`}>
        {children}
      </body>
    </html>
  );
}
