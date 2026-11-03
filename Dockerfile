# NASA Space Fire AI System - Production Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Ensure output is unbuffered
ENV PYTHONUNBUFFERED=1
ENV PORT=8500
ENV DEPLOY_ENV=production

# Copy application files
COPY . /app

# Expose server port
EXPOSE 8500

# Start server
CMD ["python", "server.py"]
