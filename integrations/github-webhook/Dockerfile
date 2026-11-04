# Day 20: the GitHub webhook receiver as a container image.
# Build:  docker build -t github-webhook:day20 .
# Run:    docker run --rm -p 8000:8000 -e GITHUB_WEBHOOK_SECRET=... github-webhook:day20

FROM python:3.12-slim

# Python behaviour inside containers: no .pyc files, logs appear immediately (not buffered)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Dependencies first: this layer is cached and only rebuilt when requirements.txt changes
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2. Then the code (changes often, so it comes last)
COPY app ./app

# 3. Never run as root inside the container
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Docker marks the container "unhealthy" if /healthz stops answering
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

# --no-access-log: our own JSON "request finished" line replaces uvicorn's plain-text access log
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
