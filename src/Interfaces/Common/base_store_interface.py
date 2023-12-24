from abc import ABC, abstractmethod


class BaseStoreInterface(ABC):

    @abstractmethod
    async def test_source(self) -> bool:
        pass
