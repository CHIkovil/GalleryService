import logging

from pydantic import BaseModel
from src.Support.base_singleton import BaseSingleton
from src.Interfaces.db_store_interface import DBStoreInterface
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorCollection
from src.Errors.bad_method_kwargs_error import BadMethodKwargsError


LOGGER = logging.getLogger()


class MongoHandler(BaseSingleton, DBStoreInterface):

    def __init__(self, *, url: str,
                 db_name: str):
        self._url = url
        self._db_name = db_name

    def _get_client(self) -> AsyncIOMotorClient:
        return AsyncIOMotorClient(self._url)

    def _get_db(self):
        return self._get_client()[self._db_name]

    def _get_collection(self, *, coll_name: str) -> AsyncIOMotorCollection:
        return self._get_db()[coll_name]

    async def test_source(self) -> bool:
        result = False

        try:
            result = self._db_name in await self._get_client().list_database_names()

        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    async def get_data(self, **kwargs) -> [BaseModel]:
        result = None

        conditions = kwargs.get("conditions")
        coll_name = kwargs.get("coll_name")

        try:
            cursor = self._get_collection(coll_name=coll_name).find(conditions if conditions and isinstance(conditions, dict) else {})
            docs = await cursor.to_list(length=None)

            result = docs if len(docs) != 0 else None
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    async def set_data(self, **kwargs):
        data = kwargs.get("data")
        coll_name = kwargs.get("coll_name")

        try:
            if data:
                await self._get_collection(coll_name=coll_name).insert_many(data)
            else:
                raise BadMethodKwargsError("data")

        except Exception as error:
            LOGGER.error(error)
