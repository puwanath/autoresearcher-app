import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "AutoResearch",
  description: "Autonomous competitor & market research agent",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="th">
      <body className="min-h-screen">
        <header className="glass sticky top-0 z-50 border-b border-black/5">
          <nav className="mx-auto flex h-12 max-w-6xl items-center justify-between px-6">
            <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold tracking-tight">
              <span className="grid h-6 w-6 place-items-center rounded-md bg-ink text-[11px] text-white"></span>
              AutoResearch
            </Link>
            <div className="flex items-center gap-6 text-[13px] text-ink-2">
              <Link href="/" className="hover:text-ink">วิจัยใหม่</Link>
              <Link href="/#history" className="hover:text-ink">ประวัติ</Link>
              <a href="http://localhost:8010/docs" target="_blank" rel="noreferrer" className="hover:text-ink">API</a>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-6xl px-6 pb-24">{children}</main>
        <footer className="border-t border-line-2 py-8 text-center text-[12px] text-ink-3">
          AutoResearch Agent · Puwanath Baibua
        </footer>
      </body>
    </html>
  );
}
