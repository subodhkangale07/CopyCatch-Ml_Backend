#############################################
# Stage 1: build stage (install deps + wheels)
#############################################
FROM python:3.11-slim as builder

# avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# system deps commonly needed for many wheels (add more if your libs need them)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    ca-certificates \
    curl \
    pkg-config \
    libglib2.0-0 \
    libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

# copy only dependency files first for caching
COPY requirements.txt ./requirements.txt

# upgrade pip and install into a separate directory to keep final image smaller
RUN python -m pip install --upgrade pip setuptools wheel \
 && python -m pip install --upgrade --target=/install -r requirements.txt

# copy the app source
COPY . /app

#############################################
# Stage 2: final runtime image (small)
#############################################
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PATH="/install/bin:${PATH}"
WORKDIR /app

# system runtime deps (keep minimal)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    libglib2.0-0 \
    libsm6 libxext6 libxrender1 \
 && rm -rf /var/lib/apt/lists/*

# copy installed packages from builder
COPY --from=builder /install /usr/local
# copy app source
COPY --from=builder /app /app

# create a non-root user (recommended)
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Render sets $PORT at runtime; we default to 8000 locally)
EXPOSE 8000

# Use $PORT if provided by the platform (Render/Railway set $PORT)
# Start command uses Gunicorn with Uvicorn workers
CMD ["sh", "-c", "exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4 -b 0.0.0.0:${PORT:-8000} --log-level info"]
