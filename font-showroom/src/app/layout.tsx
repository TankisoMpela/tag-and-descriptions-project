import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Font Studio — インディペンデント書体",
  description:
    "変な・かわいい・ノスタルジック・遊び心のあるプロジェクトのためのインディペンデントフォント。BOOTHショップで公開中。",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
