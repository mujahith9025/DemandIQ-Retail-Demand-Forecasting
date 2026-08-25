/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  // Use standalone only when explicitly building in Docker container
  output: process.env.DOCKER_BUILD === "true" ? "standalone" : undefined,
  async rewrites() {
    return [
      {
        source: "/api-backend/:path*",
        destination: `${(process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "")}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
