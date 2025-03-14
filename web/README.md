# Quadradius Web App
This is the web app for Quadradius. It is built with Next.js (react) and Tailwind CSS.
It is utilizing server-side rendering (SSR) for performance and SEO.
It is completely static and can be deployed to any static site host and has nothing to do with the actual game server.

## Prerequisites

- Node.js (v20 or higher)
- npm (comes with Node.js)

## Development

Navigate to web and install packages (this needs to happen only once)

```bash
cd web
npm install
```

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.
The project uses hot-reload, meaning that (most) changes you will make in the code will be reflected in the browser.

## Deployment

To export the project for production run

```bash
npm run export
```
