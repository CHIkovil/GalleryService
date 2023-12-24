import logging
import io

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from src.Interfaces.db_store_interface import DBStoreInterface
from src.Interfaces.file_store_interface import FileStoreInterface
from asyncio import create_task, gather as aio_gather
from urllib.parse import urljoin
from uuid import uuid4
from validators import url as validate_url
from src.Api.Web.web_server_utils_api import WebServerUtilsApi
from aiohttp import ClientSession as AioClientSession
from bs4 import BeautifulSoup
from src.Models.file_data_model import FileDataModel
from src.Models.parsing_model import ParsingModel, ParsingType
from PIL import Image
from src.Setup.transformers_setup import TransformersSetup
from asyncio import to_thread as async_to_thread
from torch import device as torch_device
from torch.cuda import is_available as cuda_is_available

LOGGER = logging.getLogger()


class WebServerUtilsHandler:
    ROUTER = APIRouter()
    FILE_HANDLER: FileStoreInterface = None
    DB_HANDLER: DBStoreInterface = None
    TRANSFORMERS_SETUP: TransformersSetup = None

    @staticmethod
    @ROUTER.post(WebServerUtilsApi.parser.value())
    async def post_content_from_url(model: ParsingModel):
        try:
            if not validate_url(model.url):
                raise HTTPException(status_code=422, detail=f"Not valid url - {model.url}")

            if await WebServerUtilsHandler.DB_HANDLER.get_data(
                    conditions={"$and": [{"base_url": model.url}, {"type": model.type.value}]},
                    coll_name="parsing_info"):
                raise HTTPException(status_code=400,
                                    detail=f"Already exist {model.type.value} content from url - {model.url}")

            if model.type == ParsingType.images:
                result_count = await WebServerUtilsHandler._get_files_to_url(base_url=model.url,
                                                                             parsing_type=model.type.value,
                                                                             extract_type='img',
                                                                             not_valid_ends=["svg"],
                                                                             info_coll_name="images_info")

                return {"message": f"{result_count} files parsing for url - {model.url}"}

        except HTTPException:
            raise
        except Exception as error:
            LOGGER.error(error)
            raise HTTPException(status_code=500)

    @staticmethod
    async def _get_files_to_url(*,
                                base_url: str,
                                parsing_type: str,
                                extract_type: str,
                                not_valid_ends: list[str],
                                info_coll_name: str) -> int:
        result = None

        try:
            async with AioClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        urls = await WebServerUtilsHandler._extract_file_urls(html_content=html_content,
                                                                              base_url=base_url,
                                                                              type=extract_type,
                                                                              not_valid_ends=not_valid_ends)

                        parsing_uid = str(uuid4()).lower()

                        models = await aio_gather(
                            *[create_task(WebServerUtilsHandler._download_file(url=url, parsing_uid=parsing_uid)) for
                              url
                              in urls])

                        await WebServerUtilsHandler.FILE_HANDLER.upload_files(models=models, file_type=parsing_type)

                        await WebServerUtilsHandler.DB_HANDLER.set_data(
                            data=[model.dict(include={'uid', 'url', 'parsing_uid', 'description'}) for model
                                  in models], coll_name=info_coll_name)

                        await WebServerUtilsHandler.DB_HANDLER.set_data(
                            data=[{"uid": parsing_uid, "base_url": base_url, "type": parsing_type}],
                            coll_name="parsing_info")

                        result = len(models)
        except HTTPException:
            raise
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    @staticmethod
    async def _download_file(*, url: str, parsing_uid: str) -> FileDataModel or None:
        result = None

        try:
            async with AioClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.read()
                        description = await async_to_thread(WebServerUtilsHandler._generate_image_description,
                                                            data=data)

                        result = FileDataModel(uid=str(uuid4()).lower(),
                                               url=url,
                                               data=data,
                                               description=description,
                                               parsing_uid=parsing_uid)
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    @staticmethod
    async def _extract_file_urls(*, html_content, base_url, type: str, not_valid_ends: list[str]) -> [str]:
        result = None

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            files = soup.find_all(type)
            result = {urljoin(base_url, f['src']) for f in files if
                      not any(f['src'].endswith(e) for e in not_valid_ends)}
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result

    @staticmethod
    def _generate_image_description(*, data: bytes) -> [FileDataModel]:

        result = None

        try:
            image = Image.open(io.BytesIO(data))

            if image.mode != "RGB":
                image = image.convert(mode="RGB")

            device = torch_device("cuda" if cuda_is_available() else "cpu")
            img = WebServerUtilsHandler.TRANSFORMERS_SETUP.processor(image, return_tensors="pt").to(device)

            output = WebServerUtilsHandler.TRANSFORMERS_SETUP.model.generate(**img)

            result = WebServerUtilsHandler.TRANSFORMERS_SETUP.tokenizer.batch_decode(output, skip_special_tokens=True)[
                0]
        except Exception as error:
            LOGGER.error(error)
        finally:
            return result
