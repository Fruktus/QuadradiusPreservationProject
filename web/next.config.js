/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NEXT_OUTPUT === 'export' ? 'export' : 'server', // Render the website statically if export mode specified
};

module.exports = nextConfig; 
