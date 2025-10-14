# pearnament

A basic TypeScript + Webpack + jQuery website setup.

## Features

- TypeScript for type-safe development
- Webpack for bundling and development server
- jQuery for DOM manipulation
- HTML template with modern styling

## Prerequisites

- Node.js (v14 or higher)
- npm (comes with Node.js)

## Installation

```bash
npm install
```

## Development

Start the development server with hot reload:

```bash
npm run dev
```

The development server will start at `http://localhost:8080` and automatically open in your browser.

## Build

Build the project for production:

```bash
npm run build
```

The output will be in the `dist/` directory. You can serve this directory with any static web server.

## Project Structure

```
pearnament/
├── src/
│   ├── index.ts        # Main TypeScript entry point
│   └── index.html      # HTML template
├── dist/               # Build output (generated)
├── webpack.config.js   # Webpack configuration
├── tsconfig.json       # TypeScript configuration
└── package.json        # Project dependencies and scripts
```

## License

Apache License 2.0
