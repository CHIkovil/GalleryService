from abc import abstractmethod
from src.Interfaces.Common.base_store_interface import BaseStoreInterface
from pydantic import BaseModel


class DBStoreInterface(BaseStoreInterface):

    @abstractmethod
    async def get_data(self, **kwargs) -> [BaseModel]:
        pass

    @abstractmethod
    async def set_data(self,  **kwargs):
        pass

