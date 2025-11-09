# Multi-stage build for React frontend
FROM node:20-alpine AS builder

WORKDIR /app

# Build arguments for Vite environment variables
ARG VITE_API_BASE_URL=
ARG VITE_DEFAULT_STORE_ID=0WcZ1MWEaFc1VftEBdLa

# Set environment variables for build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DEFAULT_STORE_ID=$VITE_DEFAULT_STORE_ID

# Copy package files
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build the application
RUN npm run build

# Production stage served via `serve`
FROM node:20-alpine

WORKDIR /app

# Install lightweight static file server
RUN npm install -g serve

# Copy built assets
COPY --from=builder /app/dist ./dist

# Expose configurable port (defaults to 80)
ENV PORT=3030
EXPOSE 3030

# Run static server accessible on all interfaces
CMD ["sh", "-c", "serve -s dist -l tcp://0.0.0.0:${PORT}"]

