FROM python:3.13-slim-trixie
LABEL authors="LukSand00"

ARG SOURCE_PATH="music/library"
ARG DOWNLOAD_DIR="music/tmp"
ARG DATABASE_PATH="data/database"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
RUN groupadd -r pythonBot && \
    useradd -r -g pythonBot -m -s /bin/bash pythonBot

COPY --chown=pythonBot:pythonBot . .

RUN uv sync
WORKDIR /app/bot
RUN mkdir -p ${SOURCE_PATH} && \
    mkdir -p ${DOWNLOAD_DIR} && \
    chown -R pythonBot:pythonBot .

USER pythonBot
ENTRYPOINT ["uv", "run", "main.py"]