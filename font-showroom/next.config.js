/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      { protocol: 'https', hostname: 'assets.booth.pm' },
      { protocol: 'https', hostname: 'booth.pximg.net' },
      { protocol: 'https', hostname: '*.public.blob.vercel-storage.com' },
      { protocol: 'https', hostname: 'cdn.vercel.io' },
    ],
  },
}

module.exports = nextConfig
