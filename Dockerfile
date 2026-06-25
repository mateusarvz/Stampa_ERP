# Multi-stage: build → runtime
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_NAME=Stampa_SaaS \
    HOME=/home/appuser

# Install tkinter + X11 libs for GUI support
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-tk \
    x11-apps \
    libx11-6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy Python deps from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy project
COPY --chown=appuser:appuser . .

# Data volume mount point
RUN mkdir -p /data && chown -R appuser:appuser /data

USER appuser

# Add .local to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# X11 socket (if using X11 forwarding)
VOLUME ["/tmp/.X11-unix"]

# Data volume
VOLUME ["/data"]

# Entrypoint
COPY --chown=appuser:appuser entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gui"]
