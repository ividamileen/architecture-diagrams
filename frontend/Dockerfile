FROM node:18-alpine

# Create non-root user
RUN addgroup -S appuser && adduser -S appuser -G appuser

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run the application
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "3000"]
