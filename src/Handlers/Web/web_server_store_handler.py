import logging

from fastapi import APIRouter, Response
from fastapi.exceptions import HTTPException
from src.Api.Web.web_server_store_api import WebServerStoreApi
from src.Interfaces.db_store_interface import DBStoreInterface
from src.Interfaces.file_store_interface import FileStoreInterface
from src.Models.file_info_model import FileInfoModel
from src.Models.parsing_model import ParsingType

LOGGER = logging.getLogger()


class WebServerStoreHandler:
    ROUTER = APIRouter()
    FILE_HANDLER: FileStoreInterface = None
    DB_HANDLER: DBStoreInterface = None

    @staticmethod
    @ROUTER.get(WebServerStoreApi.info.on_type_value(type="{file_type}"))
    async def get_current_info(file_type: str) -> list[FileInfoModel]:
        try:

            if file_type not in ParsingType.set():
                raise HTTPException(status_code=422, detail=f"Not valid info for type - {file_type}")

            infos = await WebServerStoreHandler.DB_HANDLER.get_data(coll_name=f"{file_type}_{WebServerStoreApi.info._value_}")

            if infos:
                return [FileInfoModel(**info) for info in infos]
            else:
                raise HTTPException(status_code=404, detail=f"Not found info for type - {file_type}")
        except HTTPException:
            raise
        except Exception as error:
            LOGGER.error(error)
            raise HTTPException(status_code=500)

    @staticmethod
    @ROUTER.get(WebServerStoreApi.file.on_type_value(type="{file_type}"))
    async def get_file_data(uid: str, file_type: str) -> bytes:
        try:
            if file_type not in ParsingType.set():
                raise HTTPException(status_code=422, detail=f"Not valid file type - {file_type}")

            result = await WebServerStoreHandler.FILE_HANDLER.download_file(uid=uid, file_type=file_type)

            if result:
                _, data = result
                return Response(content=data)
            else:
                raise HTTPException(status_code=404, detail=f"Not found data for uid - {uid}")
        except HTTPException:
            raise
        except Exception as error:
            LOGGER.error(error)
            raise HTTPException(status_code=500)


    @staticmethod
    async def _resize_image(self):
        pass
