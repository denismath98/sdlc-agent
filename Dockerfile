FROM python:3.11-slim

WORKDIR /app

# system deps for git (agent needs it), plus build basics
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# copy project
COPY . /app

# install python deps
RUN python -m pip install --upgrade pip \
    && pip install . \
    && pip install black pytest

# entrypoint wrapper
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV REPO_PATH=/repo
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/entrypoint.sh"]