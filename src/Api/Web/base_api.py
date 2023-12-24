from enum import Enum


class BaseApi(str, Enum):
    base_api = "api"
    store = "store"
    utils = "utils"

    @staticmethod
    def to_base() -> str:
        return f"/{BaseApi.base_api.value}"

    @staticmethod
    def to_store() -> str:
        return f"/{BaseApi.base_api.value}/{BaseApi.store.value}"

    @staticmethod
    def to_utils() -> str:
        return f"/{BaseApi.base_api.value}/{BaseApi.utils.value}"


