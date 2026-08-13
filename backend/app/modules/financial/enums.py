from enum import Enum


class FinancialTransactionType(str, Enum):
    GRID_PURCHASE = "GRID_PURCHASE"
    GRID_SALE = "GRID_SALE"
    SOLAR_SAVING = "SOLAR_SAVING"
    BATTERY_SAVING = "BATTERY_SAVING"
    LOAD_SHIFT_SAVING = "LOAD_SHIFT_SAVING"
