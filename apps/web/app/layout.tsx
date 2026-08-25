import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Recon AI",
  description:
    "Reconcile bank statements against your general ledger, through chat.",
};

function Mark() {
  return (
    <span
      aria-hidden
      className="grid size-8 place-items-center rounded-lg bg-accent text-accent-foreground"
    >
      <svg viewBox="0 0 24 24" fill="none" className="size-4">
        <path
          d="M4 8h11m0 0-3-3m3 3-3 3M20 16H9m0 0 3-3m-3 3 3 3"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </span>
  );
}

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col">
        <header className="sticky top-0 z-10 border-b border-border bg-background/85 backdrop-blur">
          <div className="mx-auto flex w-full max-w-4xl items-center gap-3 px-5 py-3 sm:px-6">
            <Mark />
            <div className="flex flex-col leading-tight">
              <span className="text-sm font-semibold tracking-tight">
                Recon AI
              </span>
              <span className="text-xs text-muted">
                Bank statement reconciliation
              </span>
            </div>
          </div>
        </header>

        <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-5 py-6 sm:px-6 sm:py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
