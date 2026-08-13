from abc import ABC, abstractmethod


class BaseDevice(ABC):
    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def read_data(self):
        pass

    @abstractmethod
    async def health_check(self):
        pass
