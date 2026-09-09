import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MediAssist | Secure clinical knowledge",
  description: "Role-aware hospital knowledge assistant",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
