/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    API_BASE_URL: process.env.API_BASE_URL || 'https://leadharvester.duckdns.org/api/v1',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_BASE_URL || 'https://leadharvester.duckdns.org/api/v1'}/:path*`,
      },
    ]
  },
}

module.exports = nextConfig
