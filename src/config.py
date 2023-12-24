import logging
import os

from dotenv import load_dotenv

LOGGER = logging.getLogger()

if not load_dotenv():
    LOGGER.error("Not found .env file")

UVICORN_SERVER_HOST = os.environ.get("UVICORN_SERVER_HOST")
UVICORN_SERVER_PORT = os.environ.get("UVICORN_SERVER_PORT")

STORE_NAME = os.environ.get("STORE_NAME")

MONGO_URL = os.environ.get("MONGO_URL")

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY")
