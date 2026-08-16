# Quart & Discord.py Backend Service

An asynchronous backend service combining a Quart web application served via Hypercorn and an integrated discord.py bot instance, orchestrated via Docker Compose with a PostgreSQL database.

This repository serves as the backend  for my [ESP Doorbell project](https://github.com/maxovina/esp_cam_module).

## Architecture

* **API:** Quart application running on Hypercorn, handling web endpoints and request processing.
* **Bot:** Asynchronous discord.py bot utilizing modular cogs.
* **Database:** PostgreSQL instance managed with custom migration scripts.
* **Orchestration:** Multi-container deployment using Docker and Docker Compose.


## Getting Started

1. Clone the repository:
   ```bash
   git clone [https://github.com/maxovina/quart-discord-bot.git](https://github.com/maxovina/quart-discord-bot.git)
   cd quart-discord-bot
   ```

2. Duplicate the environment template to create your local configuration file:
    ```bash
    cp .env.example .env
    ```

3. Build and start the containers using Docker Compose:
    ```bash
    docker compose up --build
    ```
