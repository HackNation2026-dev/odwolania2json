import type { Metadata } from "next";
import type { ReactNode } from "react";
import { AppShell } from "@/components/organisms/AppShell";
import { Providers } from "@/lib/providers";
import { themeInitScript } from "@/lib/theme/theme";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: { default: "Odwołania2JSON", template: "%s · Odwołania2JSON" },
  description: "PDF → JSON z dowodami (dane demonstracyjne)",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pl" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
