from abc import abstractmethod
from src.Interfaces.Common.base_store_interface import BaseStoreInterface


class FileStoreInterface(BaseStoreInterface):
    @abstractmethod
    async def download_files(self, **kwargs) -> [bytes]:
        pass

    @abstractmethod
    async def download_file(self, **kwargs):
        pass

    @abstractmethod
    async def upload_files(self, **kwargs):
        pass
