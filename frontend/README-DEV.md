# Frontend Development Guide

## Quick Start

### Option 1: Simple Development (Recommended)

From the project root directory:

```bash
./run-frontend-dev.sh
```

Or manually:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:3030

### Option 2: Docker Development

From the project root:

```bash
docker-compose -f docker-compose.frontend-dev.yml up
```

### Option 3: Production Build

```bash
cd frontend
npm run build
npm run preview
```

## Environment Variables

Copy `env.example` to `.env` and adjust as needed:

```bash
cp env.example .env
```

Key variables:
- `VITE_API_BASE_URL`: Backend API URL (default: http://localhost:8000)
- `VITE_DEFAULT_STORE_ID`: Default store ID for development

## Troubleshooting

### Blank Screen Issues

1. Check browser console for errors (F12)
2. Verify backend is running at http://localhost:8000
3. Check network tab for failed API calls
4. Clear browser cache and localStorage
5. Ensure `.env` file exists with correct values

### Common Fixes

1. **API Connection Issues**: Make sure backend is running
2. **Routing Issues**: We use BrowserRouter, ensure your server handles SPA routing
3. **Build Issues**: Delete `node_modules` and `package-lock.json`, then reinstall

### Development Tips

- The app uses Vite for fast HMR (Hot Module Replacement)
- Changes to `.tsx` files will auto-reload
- API proxy is configured in `vite.config.ts` for development
- Error boundaries will catch and display React errors

## Architecture

- **React 19** with TypeScript
- **React Router** for navigation
- **Recharts** for data visualization
- **Axios** for API calls
- **Vite** for build tooling
