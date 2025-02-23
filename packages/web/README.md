This is the web app for Quadradius manual. It is built with Next.js (react) and Tailwind
CSS.
It is utilizing server-side rendering (SSR) for performance and SEO.
It is completely static and can be deployed to any static site host and has nothing to do with the actual game server.

## Prerequisites

- Node.js (v18 or higher)
- npm (comes with Node.js)

## Development

Navigate to packages/web and run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Deployment

To run this on production, run:

```bash
npm run build
npm run start
```

the `build` command will create a production build in a folder `.next`
The `start` command will start the production server.
