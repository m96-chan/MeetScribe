# MeetScribe Dockerfile - Multi-stage build for optimized image size
# Stage 1: Builder
FROM python:3.11-alpine AS builder

LABEL maintainer="MeetScribe Contributors"
LABEL description="Multi-source AI Meeting Pipeline Framework"

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    linux-headers \
    ffmpeg \
    ffmpeg-dev

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-alpine

# Install runtime dependencies only
RUN apk add --no-cache \
    ffmpeg \
    libstdc++

# Create non-root user for security
RUN addgroup -g 1000 meetscribe && \
    adduser -D -u 1000 -G meetscribe meetscribe

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY --chown=meetscribe:meetscribe . .

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MEETSCRIBE_WORKING_DIR=/app/meetings

# Create meetings directory with proper permissions
RUN mkdir -p /app/meetings && \
    chown -R meetscribe:meetscribe /app/meetings

# Switch to non-root user
USER meetscribe

# Install meetscribe package
RUN pip install --no-cache-dir -e .

# Volume for meeting data persistence
VOLUME ["/app/meetings"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import meetscribe; print('OK')" || exit 1

# Default command
ENTRYPOINT ["meetscribe"]
CMD ["--help"]
