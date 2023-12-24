import io
import logging

from aiohttp import ClientSession as AioClientSession
from asyncio import Task, create_task, gather as aio_gather
from src.Interfaces.file_store_interface import FileStoreInterface
from src.Support.base_singleton import BaseSingleton
from miniopy_async import Minio as AsyncMinio
from asyncio import Lock
from src.Errors.bad_method_kwargs_error import BadMethodKwargsError
from src.Models.file_data_model import FileDataModel
from src.Api.minio_image_handler_api import MinioImageHandlerApi
from src.Models.parsing_model import ParsingType

LOGGER = logging.getLogger()


class MinioHandler(BaseSingleton, FileStoreInterface):
    def __init__(self, *,
                 bucket_name: str,
                 client: AsyncMinio
                 ):
        self._client = client
        self._bucket_name = bucket_name
        self._lock = Lock()

    async def test_source(self) -> bool:
        result = False

        try:
            result = await self._client.bucket_exists(bucket_name=self._bucket_name)
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    async def download_files(self, **kwargs) -> [bytes]:
        result = {}

        uids: [str] = kwargs.get("uids")
        file_type: str = kwargs.get("file_type")

        try:
            if uids and file_type:
                async def on_callback(*, task: Task, results: dict):
                    content = task.result()

                    if isinstance(content, tuple):
                        if len(content) == 2:
                            async with self._lock:
                                results[content[0]] = content[1]

                tasks = []

                for uid in uids:
                    task = create_task(self.download_file(uid=uid, file_type=file_type))
                    task.add_done_callback(lambda t: create_task(on_callback(task=t, results=result)))
                    tasks.append(task)

                await aio_gather(*tasks)
            else:
                raise BadMethodKwargsError("uids")
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    @staticmethod
    async def _on_object_name(*, uid: str, file_type: str):
        result = None

        if file_type == ParsingType.images.value:
            result = MinioImageHandlerApi.prefix.value + "\\" + f"{uid}{MinioImageHandlerApi.ext.value}"

        return result

    async def download_file(self, **kwargs):
        result = None

        uid: str = kwargs.get("uid")
        file_type: str = kwargs.get("file_type")

        try:
            if uid and file_type:
                object_name = await self._on_object_name(uid=uid, file_type=file_type)

                async with AioClientSession() as session:
                    response = await self._client.get_object(bucket_name=self._bucket_name,
                                                             object_name=object_name,
                                                             session=session)

                    content = await response.read()

                    result = uid, content
            else:
                raise BadMethodKwargsError("uid", "file_type")

        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    async def upload_files(self, **kwargs):
        models: [FileDataModel] = kwargs.get("models")
        file_type: str = kwargs.get("file_type")

        try:
            if models and file_type:
                tasks = []

                for model in models:
                    object_name = await self._on_object_name(uid=model.uid, file_type=file_type)
                    task = create_task(self._client.put_object(bucket_name=self._bucket_name,
                                                               object_name=object_name,
                                                               data=io.BytesIO(model.data),
                                                               length=len(model.data)))

                    tasks.append(task)

                await aio_gather(*tasks)
            else:
                raise BadMethodKwargsError("models", "file_type")

        except Exception as error:
            LOGGER.error(error)
