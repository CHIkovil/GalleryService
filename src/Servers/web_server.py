from src.Support.base_singleton import BaseSingleton
from uvicorn import (Config as UvConfig, Server as UvServer)
from fastapi import FastAPI
from src.Handlers.Web.web_server_store_handler import WebServerStoreHandler
from src.Handlers.Web.web_server_utils_handler import WebServerUtilsHandler
from src.Interfaces.db_store_interface import DBStoreInterface
from src.Interfaces.file_store_interface import FileStoreInterface
from src.Setup.transformers_setup import TransformersSetup


class WebServer(BaseSingleton,
                WebServerStoreHandler,
                WebServerUtilsHandler):
    def __init__(self, *, host: str,
                 port: int,
                 db_handler: DBStoreInterface,
                 file_handler: FileStoreInterface,
                 transformers_setup: TransformersSetup):
        self._host = host
        self._port = port
        self._app = FastAPI()
        self._setup(db_handler=db_handler,
                    file_handler=file_handler,
                    transformers_setup=transformers_setup)

    def _setup(self, *,
               db_handler: DBStoreInterface,
               file_handler: FileStoreInterface,
               transformers_setup: TransformersSetup):
        for cls in self.__class__.__mro__:
            if cls.__name__.endswith("Handler"):
                self._app.include_router(cls.ROUTER)
                cls.TRANSFORMERS_SETUP = transformers_setup
                cls.FILE_HANDLER = file_handler
                cls.DB_HANDLER = db_handler

        self._server = UvServer(config=UvConfig(self._app,
                                                host=self._host,
                                                port=self._port,
                                                reload=False,
                                                log_level="debug"))

    def start(self):
        self._server.run()