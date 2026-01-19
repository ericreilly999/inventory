# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY services/ui/package.json services/ui/package-lock.json* ./

# Install dependencies
RUN npm install --omit=dev

# Copy source code
COPY services/ui/ .

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