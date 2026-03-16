# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Final Runtime
FROM python:3.11-slim
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn uvicorn

# Copy Python code (main.py, calculator.py)
COPY backend/ .

# Copy built frontend assets into 'static' directory within the app root
COPY --from=frontend-builder /app/frontend/dist ./static

# Ensure the static directory exists and is populated
RUN ls -la /app/static

# Set environment variables
ENV PORT=10000
EXPOSE 10000

# Start server
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:10000"]
