### Discord py MusicBot (self-hosted) - IN PROGRESS
A way to self-host instance of discord musicbot, which handles local music or youtube by using yt-dlp.

### Features
-   Automatically generates sqlite database based on chosen music catalog.
-   Separate queues for different discord servers.
-   Additional player functionalities eg. pause, resume, clear queue.
-   Containerized - Quick local or remote setup.

### Requirements
#### Run with Docker
-   Docker
-   Docker Compose (TODO)

#### Development requirements
-   python >=3.12
-   uv
-   FFMPEG

### Usage
``TODO: Description of usage with docker compose, filling env variables etc``

### Development
To run project make sure you meet requirements. If you meet them create new ``.env`` file in ``./bot`` directory and fill it as described in ``.env-example``. Use ``uv sync`` command and finally run project with ``uv run ./main.py`` in ``./bot`` directory.

