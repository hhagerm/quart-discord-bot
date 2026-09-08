import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "captures")


DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER", "db_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret_password")
DB_NAME = os.getenv("POSTGRES_DB", "doorbell_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"

TEST_DB_HOST = os.getenv("TEST_HOST", "localhost")
TEST_DB_PORT = int(os.getenv("TEST_PORT", 5433))
TEST_DB_USER = os.getenv("TEST_USER", "test_user")
TEST_DB_PASSWORD = os.getenv("TEST_PASSWORD", "secret_password")
TEST_DB_NAME = os.getenv("TEST_DB", "test_doorbell")

TEST_DATABASE_URL = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@localhost:{TEST_DB_PORT}/{TEST_DB_NAME}?sslmode=disable"

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST", "localhost")
TEST_REDIS_PORT = int(os.getenv("TEST_REDIS_PORT", 6380))

MAX_PAYLOAD_SIZE = 5 * 1024 * 1024