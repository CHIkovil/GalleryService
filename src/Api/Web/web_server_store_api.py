from enum import Enum
from src.Api.Web.base_api import BaseApi


class WebServerStoreApi(str, Enum):
    info = "info"
    file = "{uid}"

    def on_type_value(self, *, type: str) -> str:
        if self == WebServerStoreApi.info:
            return f"{BaseApi.to_store()}/{self._value_}/{type}"
        elif self == WebServerStoreApi.file:
            return f"{BaseApi.to_store()}/{type}/{self._value_}"


