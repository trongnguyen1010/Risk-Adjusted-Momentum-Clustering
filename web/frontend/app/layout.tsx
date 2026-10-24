import type { Metadata } from "next";
import { Suspense } from "react";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/600.css";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Shell } from "@/components/shell";
export const metadata: Metadata = {
  title: "DELTA Intelligence · Nghiên cứu cổ phiếu Việt Nam",
  description:
    "Khám phá cấu trúc cổ phiếu Việt Nam qua các mô hình phân cụm thị trường, tài chính và kết hợp đã lưu.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="vi">
      <body>
        <a className="skip-link" href="#main-content">
          Chuyển đến nội dung nghiên cứu
        </a>
        <Providers>
          <Shell>
            <Suspense
              fallback={
                <div className="page-loading">
                  Đang mở không gian nghiên cứu…
                </div>
              }
            >
              {children}
            </Suspense>
          </Shell>
        </Providers>
      </body>
    </html>
  );
}
