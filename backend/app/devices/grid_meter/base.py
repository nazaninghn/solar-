from abc import abstractmethod

from app.devices.base import BaseDevice


class BaseGridMeter(BaseDevice):
    @abstractmethod
    async def get_import_power(self) -> float:
        pass

    @abstractmethod
    async def get_export_power(self) -> float:
        pass

    @abstractmethod
    async def get_status(self) -> str:
        pass
