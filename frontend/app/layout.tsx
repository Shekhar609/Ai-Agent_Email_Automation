import "./globals.css";

import { Toaster } from "sonner";

import Providers from "./providers";

export const metadata = {
  title: "Email Automation",
  description: "AI email assistant",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}
