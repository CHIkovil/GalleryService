import asyncio
import logging
import sys

from src.Handlers.Minio.minio_handler import MinioHandler
from src.Handlers.Mongo.mongo_handler import MongoHandler
from src.Servers.web_server import WebServer
from miniopy_async import Minio as AsyncMinio
from src.Interfaces.db_store_interface import DBStoreInterface
from src.Interfaces.file_store_interface import FileStoreInterface
from pathlib import Path
from transformers import VisionEncoderDecoderModel, GPT2TokenizerFast, ViTImageProcessor
from src.Setup.transformers_setup import TransformersSetup
from torch import device as torch_device
from torch.cuda import is_available as cuda_is_available

from config import (
    UVICORN_SERVER_HOST,
    UVICORN_SERVER_PORT,
    STORE_NAME,
    MONGO_URL,
    MINIO_ENDPOINT,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY
)

LOGGER = logging.getLogger()

if not UVICORN_SERVER_HOST \
        or not UVICORN_SERVER_PORT \
        or not STORE_NAME \
        or not MONGO_URL \
        or not MINIO_ENDPOINT \
        or not MINIO_ACCESS_KEY \
        or not MINIO_SECRET_KEY:
    LOGGER.error("None value env")
    sys.exit(1)


def _setup_web_server(*,
                      db_handler: DBStoreInterface,
                      file_handler: FileStoreInterface,
                      transformers_setup: TransformersSetup) -> WebServer:
    return WebServer(host=UVICORN_SERVER_HOST,
                     port=int(UVICORN_SERVER_PORT),
                     db_handler=db_handler,
                     file_handler=file_handler,
                     transformers_setup=transformers_setup)


def _preload_transformers() -> TransformersSetup:
    path = Path("./src/Support/vit-gpt2-image-captioning")
    device = torch_device("cuda" if cuda_is_available() else "cpu")

    model = VisionEncoderDecoderModel.from_pretrained(path, local_files_only=True).to(device)
    tokenizer = GPT2TokenizerFast.from_pretrained(path, local_files_only=True)
    processor = ViTImageProcessor.from_pretrained(path, local_files_only=True)

    return TransformersSetup(model=model,
                             tokenizer=tokenizer,
                             processor=processor)


async def _setup_db_handler() -> DBStoreInterface:
    db_handler = MongoHandler(url=MONGO_URL,
                              db_name=STORE_NAME)

    if await db_handler.test_source():
        return db_handler
    else:
        LOGGER.error(f"Not connection to mongo url - {MONGO_URL} with db name - {STORE_NAME}")
        sys.exit(1)


async def _setup_file_handler() -> FileStoreInterface:
    client = AsyncMinio(endpoint=MINIO_ENDPOINT,
                        access_key=MINIO_ACCESS_KEY,
                        secret_key=MINIO_SECRET_KEY,
                        secure=False)

    file_handler = MinioHandler(client=client,
                                bucket_name=STORE_NAME)

    if await file_handler.test_source():
        return file_handler
    else:
        LOGGER.error(f"Not connection to minio endpoint - {MINIO_ENDPOINT} with bucket name - {STORE_NAME}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        if UVICORN_SERVER_PORT.isdigit():
            transformers_setup = _preload_transformers()

            db_handler = asyncio.run(_setup_db_handler())
            file_handler = asyncio.run(_setup_file_handler())
            server = _setup_web_server(file_handler=file_handler,
                                       db_handler=db_handler,
                                       transformers_setup=transformers_setup)

            server.start()
        else:
            LOGGER.error("Environ port env not digit")
    except Exception as error:
        LOGGER.error(error)
