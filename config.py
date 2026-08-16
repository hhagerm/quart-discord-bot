import os
from dotenv import load_dotenv

load_dotenv()

BOT_SERVICES = os.getenv("BOT_SERVICES", "true").lower() == "true"
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = int(os.getenv("POSTGRES_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER", "db_user")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret_password")
DB_NAME = os.getenv("POSTGRES_NAME", "doorbell_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=disable"