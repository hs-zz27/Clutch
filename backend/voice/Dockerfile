# Clutch Voice Crisis Mode worker.
# Build from the backend/ directory:
#   docker build -f voice/Dockerfile -t clutch-voice .
# Run (pass the worker's .env):
#   docker run --env-file .env clutch-voice
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-voice.txt ./
RUN pip install --no-cache-dir -r requirements-voice.txt

# The worker imports the `voice` package and talks to the API over HTTP, so the
# package itself is all we need to copy in.
COPY voice ./voice

# Bake the Silero VAD weights into the image so cold starts don't stall on a
# first-run download.
RUN python -m voice.agent download-files

CMD ["python", "-m", "voice.agent", "start"]
