import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Recon AI",
  description:
    "Reconcile bank statements against your general ledger, through chat.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">
        <header className="border-b border-border">
          <div className="mx-auto flex w-full max-w-4xl items-baseline gap-3 px-6 py-4">
            <span className="font-semibold tracking-tight">Recon AI</span>
            <span className="text-sm text-muted">
              Bank statement reconciliation
            </span>
          </div>
        </header>
        <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
