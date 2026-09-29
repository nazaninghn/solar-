"""
Turkish day-ahead market (GÖP): prices, fundamentals, PTF forecasts and
factory sell offers.

PTF (Piyasa Takas Fiyatı) is one national hourly price, so prices,
fundamentals and forecasts are market-wide (no factory_id). Offers are
per factory. All timestamps are stored UTC; one row = one delivery hour
starting at `timestamp`.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    ptf_try_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    ptf_usd_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    ptf_eur_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    # SMF (Sistem Marjinal Fiyatı) — balancing-market price, what an
    # imbalance is settled against.
    smf_try_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="EPIAS")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MarketFundamental(Base):
    """System-level drivers of PTF. Stored per delivery hour; *when* each
    becomes known matters for forecasting (see forecasting.py)."""

    __tablename__ = "market_fundamentals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, unique=True, index=True)
    load_forecast_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_total_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_wind_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_solar_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_hydro_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_river_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_natural_gas_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_lignite_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    dpp_imported_coal_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PtfForecast(Base):
    """One forecast of one delivery hour, issued on `issued_for_date - 1`
    before gate closure. Kept (not overwritten by actuals) so accuracy
    can be measured against what was actually known at bid time."""

    __tablename__ = "ptf_forecasts"
    __table_args__ = (
        UniqueConstraint("timestamp", "model_version", name="uq_ptf_forecast_hour_model"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    p10_try_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    p50_try_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    p90_try_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SellOffer(Base):
    """One hour of one factory's day-ahead offer. `mode` says what kind:
    GOP_BID rows are price-quantity bids for a market participant (or
    its aggregator) to submit; NET_METERING rows are an hourly
    sell/store plan with no bid. Never submitted automatically —
    status moves DRAFT -> SUBMITTED only when a user records it."""

    __tablename__ = "sell_offers"
    __table_args__ = (
        UniqueConstraint("factory_id", "timestamp", "tier", name="uq_sell_offer_factory_hour_tier"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    factory_id: Mapped[int] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=False, index=True)
    delivery_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # 1 = PV surplus (must-sell), 2 = battery discharge (opportunity-priced)
    tier: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity_mwh: Mapped[float] = mapped_column(Float, nullable=False)
    price_try_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_ptf_try_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    expected_revenue_try: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_p10_try: Mapped[float | None] = mapped_column(Float, nullable=True)
    revenue_p90_try: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    inputs: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
