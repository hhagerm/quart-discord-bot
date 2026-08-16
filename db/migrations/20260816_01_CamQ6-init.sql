
-- step

CREATE TABLE IF NOT EXISTS devices (
    serial_number TEXT PRIMARY KEY,
    pairing_code TEXT NOT NULL DEFAULT 'CODE123',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    serial_number TEXT NOT NULL,
    channel_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    subscribed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (serial_number) REFERENCES devices (serial_number) ON DELETE CASCADE,
    CONSTRAINT unique_serial_guild UNIQUE(serial_number, guild_id)
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id TEXT PRIMARY KEY,
    serial_number TEXT NOT NULL,
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (serial_number) REFERENCES devices (serial_number) ON DELETE CASCADE
);

