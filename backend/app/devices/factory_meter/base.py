from abc import abstractmethod

from app.devices.base import BaseDevice


class BaseFactoryMeter(BaseDevice):
    @abstractmethod
    async def get_consumption(self) -> float:
        pass

    @abstractmethod
    async def get_status(self) -> str:
        pass
