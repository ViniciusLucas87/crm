import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import { TelephonyProvider } from "@/lib/telephony-context";
import { ToastProvider } from "@/components/ui/toast";
import { GlobalCallBar } from "@/components/telephony/global-call-bar";
import { DiagnosticsPanel } from "@/components/telephony/diagnostics-panel";
import { PostCallQueue } from "@/components/transcription/postcall-queue";
import { VersionCompatibilityCheck } from "@/components/dev/version-compatibility-check";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrainsMono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Pacific North Systems OS",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
        <body className="bg-slate-950 text-slate-100 antialiased">
          <TelephonyProvider>
            <ToastProvider>
              <GlobalCallBar />
              <DiagnosticsPanel />
              <PostCallQueue />
              <VersionCompatibilityCheck />
              {children}
            </ToastProvider>
          </TelephonyProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
