import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AEGNT-UNLTD | The Sovereign Strategist",
  description: "Tier 0 - Self-evolving cognitive hypervisor",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
