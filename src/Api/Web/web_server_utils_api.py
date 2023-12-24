from enum import Enum
from src.Api.Web.base_api import BaseApi


class WebServerUtilsApi(str, Enum):
    parser = "parser"

    def value(self) -> str:
        return f"{BaseApi.to_utils()}/{self._value_}"
