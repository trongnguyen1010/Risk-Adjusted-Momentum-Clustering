import type { NextConfig } from "next";
const nextConfig: NextConfig = {
  poweredByHeader: false,
  distDir: process.env.DELTA_BUILD_DIR || ".next",
  async rewrites() {
    return [
      {
        source: "/api/v2/:path*",
        destination: `${process.env.DELTA_API_URL || "http://127.0.0.1:8010"}/api/v2/:path*`,
      },
    ];
  },
};
export default nextConfig;
