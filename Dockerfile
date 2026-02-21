FROM python:3.11-slim AS backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Frontend Build Stage ---
FROM node:18-slim AS frontend

WORKDIR /frontend-build

# Copy package files first for Docker layer caching
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --ignore-scripts || npm install

# Copy the ENTIRE frontend source directory
COPY frontend/ ./

# Remove node_modules if accidentally copied (safety net)
RUN rm -rf node_modules/.cache 2>/dev/null; true

# Run the production build
RUN npm run build

# Verify dist was created
RUN ls -la dist/ && echo "Frontend build successful!"

# --- Final Stage ---
FROM backend AS final

WORKDIR /app

# Copy application code
COPY . .

# Copy built frontend from the frontend stage
COPY --from=frontend /frontend-build/dist /app/frontend/dist

# Create non-root user and writable dirs
RUN useradd -m -u 1000 custos && \
    chown -R custos:custos /app && \
    mkdir -p /app/uploads && chown custos:custos /app/uploads
USER custos

# Expose port
EXPOSE 8000

# Run with gunicorn + uvicorn workers for production
CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
