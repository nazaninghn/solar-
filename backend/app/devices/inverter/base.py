from abc import abstractmethod

from app.devices.base import BaseDevice


class BaseInverter(BaseDevice):
    @abstractmethod
    async def get_power(self) -> float:
        pass

    @abstractmethod
    async def get_energy_today(self) -> float:
        pass

    @abstractmethod
    async def get_status(self) -> str:
        pass
