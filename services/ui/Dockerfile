# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files first for better caching
COPY services/ui/package*.json ./

# Install all dependencies (needed for build)
RUN npm install

# Copy all source files
COPY services/ui/public ./public
COPY services/ui/src ./src
COPY services/ui/tsconfig.json ./

# Build the application
ENV REACT_APP_API_URL=""
RUN npm run build

# Production stage
FROM nginx:alpine

# Set environment variables
ENV SERVICE_NAME=ui-service \
    SERVICE_PORT=80

# Install curl for health checks
RUN apk add --no-cache curl

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY services/ui/nginx.conf /etc/nginx/conf.d/default.conf

# Create log directory
RUN mkdir -p /var/log/nginx && chown -R nginx:nginx /var/log/nginx

# Expose port
EXPOSE 80

# Health check with better endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1

# Start nginx with proper logging
CMD ["nginx", "-g", "daemon off;"]