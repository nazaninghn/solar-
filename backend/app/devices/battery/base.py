from abc import abstractmethod

from app.devices.base import BaseDevice


class BaseBattery(BaseDevice):
    @abstractmethod
    async def get_soc(self) -> float:
        pass

    @abstractmethod
    async def get_power(self) -> float:
        pass

    @abstractmethod
    async def get_status(self) -> str:
        pass
