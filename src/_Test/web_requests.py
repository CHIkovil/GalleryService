import asyncio

from miniopy_async.deleteobjects import DeleteObject
from motor.motor_asyncio import AsyncIOMotorClient
from miniopy_async import Minio as AsyncMinio
from aiohttp import ClientSession as AioClientSession
from src.Models.parsing_model import ParsingModel, ParsingType
from pydantic import BaseModel
from src.config import (MINIO_ENDPOINT,
                        MINIO_ACCESS_KEY,
                        MINIO_SECRET_KEY,
                        STORE_NAME,
                        MONGO_URL)


async def _post_new_content(*, url: str, model: BaseModel):
    async with AioClientSession() as session:
        async with session.post(url=url, json=model.model_dump()) as response:
            return await response.text()


async def _get_current_info(*, url: str):
    async with AioClientSession() as session:
        async with session.get(url=url) as response:
            return await response.json()


async def _download_dile(*, url: str):
    async with AioClientSession() as session:
        async with session.get(url=url) as response:
            return await response.read()


async def _clean_minio():
    minio_client = AsyncMinio(endpoint=MINIO_ENDPOINT,
                              access_key=MINIO_ACCESS_KEY,
                              secret_key=MINIO_SECRET_KEY,
                              secure=False)

    delete_object_list = map(
        lambda x: DeleteObject(x.object_name),
        await minio_client.list_objects(bucket_name=STORE_NAME,
                                        recursive=True),
    )

    await minio_client.remove_objects(bucket_name=STORE_NAME, delete_object_list=delete_object_list)


async def _clean_mongo():
    client = AsyncIOMotorClient(MONGO_URL)

    db = client[STORE_NAME]

    colls = await db.list_collection_names()

    for coll in colls:
        await db.drop_collection(coll)
        await db.create_collection(coll)


async def _run():

    await _clean_minio()
    await _clean_mongo()

    model = ParsingModel(url="https://www.drweb.ru/",
                         type=ParsingType.images)

    print(await _post_new_content(url="http://localhost:8888/api/utils/parser", model=model))

    data = await _get_current_info(url="http://localhost:8888/api/store/info/images")
    print(data)

    uid = data[0]['uid']
    data = await _download_dile(url=f"http://localhost:8888/api/store/images/{uid}")
    print(bytearray(data)[:20])


if __name__ == "__main__":
    asyncio.run(_run())
