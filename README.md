# Quart & Discord.py Backend Service

An asynchronous backend service that receives image events over HTTP and delivers them as Discord notifications. A Quart application served via Hypercorn handles ingest, a separate discord.py bot handles delivery, and the two are decoupled by a Redis queue. Orchestrated via Docker Compose with a PostgreSQL database.

Originally built as the backend for my [ESP Doorbell project](https://github.com/maxovina/esp_cam_module). The hardware side is no longer maintained, but any HTTP client that sends a JPEG with the required headers works as a producer.

![Tests](https://github.com/hhagerm/quart-discord-bot/actions/workflows/test.yml/badge.svg)

## Architecture

* **API:** Quart application running on Hypercorn. Validates headers and API key, authorises the device, deduplicates the event, stores the image and enqueues a notification job. Never talks to Discord itself.
* **Bot:** Asynchronous discord.py bot utilizing modular cogs. Consumes the queue and sends embeds, and serves the `/subscribe` and `/unsubscribe` slash commands.
* **Queue:** Redis list sitting between the two. Discord rate limits and outages can't slow down or fail a device upload, since delivery happens outside the request.
* **Idempotency:** Events carry an `Event-ID` enforced as a primary key, so retries from a device on bad Wi-Fi never produce duplicate notifications.
* **Database:** PostgreSQL instance managed with yoyo migrations, applied by a one-shot container that the API and bot both wait on.
* **Error handling:** Custom exception types translated into HTTP error responses.
* **Orchestration:** Multi-container deployment using Docker and Docker Compose.

## Testing

Covers the API layer (request validation, HTTP responses), service layer (orchestration logic), database layer (integration tests against a real PostgreSQL container), queue layer (integration tests against a real Redis container) and storage layer. Test services run on their own ports so they never touch development data. Runs automatically on every push via GitHub Actions.

## Getting Started

> **Note:** This service expects requests from the companion [ESP Doorbell hardware](https://github.com/maxovina/esp_cam_module). The API and bot will run without it, but you won't receive live doorbell events unless the ESP device is present.

1. Clone the repository:
```bash
   git clone https://github.com/hhagerm/quart-discord-bot.git
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
