# config.py
import os
from dotenv import load_dotenv

load_dotenv()


def require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def build_db_url(user: str, password: str, host: str, port: int, name: str) -> str:
    return f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=disable"


BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "captures")

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER", "db_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret_password")
DB_NAME = os.getenv("POSTGRES_DB", "doorbell_db")
DATABASE_URL = build_db_url(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

TEST_DB_PORT = int(os.getenv("TEST_PORT", 5433))
TEST_DB_USER = os.getenv("TEST_USER", "test_user")
TEST_DB_PASSWORD = os.getenv("TEST_PASSWORD", "secret_password")
TEST_DB_NAME = os.getenv("TEST_DB", "test_doorbell")
TEST_DATABASE_URL = build_db_url(TEST_DB_USER, TEST_DB_PASSWORD, "localhost", TEST_DB_PORT, TEST_DB_NAME)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.getenv("TEST_REDIS_PORT", 6380))

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024