"""Domain models for Dropcountr API responses.

Shapes are based on live `application/vnd.dropcountr.api+json;version=2`
payloads (Hydra collections, IRI templates, nested premise/meter resources).
Unknown JSON keys are ignored so the models stay resilient to API drift.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

from .timezone import localize_api_time, timezone_for_address

# Series bucket sizes. ``billing`` requires the ``billing_period`` feature flag
# on the service connection (or utility).
Period = Literal["hour", "day", "week", "month", "billing"]
PERIODS: tuple[str, ...] = ("hour", "day", "week", "month", "billing")
BILLING_PERIOD_FEATURE = "billing_period"


def _get(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


@dataclass(frozen=True)
class ResourceRef:
    """Hydra/JSON-LD resource link (`{"@id": "..."}`)."""

    id: str

    @classmethod
    def from_dict(cls, data: Optional[Any]) -> Optional[ResourceRef]:
        if data is None:
            return None
        if isinstance(data, str):
            return cls(id=data)
        if isinstance(data, dict) and "@id" in data:
            return cls(id=data["@id"])
        return None


@dataclass(frozen=True)
class IriTemplate:
    """Hydra IRI template used for series endpoints."""

    template: str
    type: str = "IriTemplate"
    context: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[IriTemplate]:
        if not data or "template" not in data:
            return None
        return cls(
            template=data["template"],
            type=data.get("@type", "IriTemplate"),
            context=data.get("@context"),
        )


@dataclass(frozen=True)
class Address:
    id: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[Address]:
        if not data:
            return None
        return cls(
            id=_get(data, "@id"),
            street=data.get("street"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            country=data.get("country"),
            lat=data.get("lat"),
            lng=data.get("lng"),
        )


@dataclass(frozen=True)
class Utility:
    id: Optional[str] = None
    utility_id: Optional[str] = None
    name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    street: Optional[str] = None
    measurement_interval: Optional[str] = None
    contracted: Optional[bool] = None
    thumbnail_url: Optional[str] = None
    features: List[str] = field(default_factory=list)
    disable_user_defined_goals: Optional[bool] = None
    usage_start_date: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[Utility]:
        if not data:
            return None
        return cls(
            id=_get(data, "@id"),
            utility_id=data.get("utility_id"),
            name=data.get("name"),
            city=data.get("city"),
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            street=data.get("street") or data.get("street_address"),
            measurement_interval=data.get("measurement_interval"),
            contracted=data.get("contracted"),
            thumbnail_url=data.get("thumbnail_url"),
            features=list(data.get("features") or []),
            disable_user_defined_goals=data.get("disable_user_defined_goals"),
            usage_start_date=data.get("usage_start_date"),
        )


@dataclass(frozen=True)
class UsageGallonsRange:
    begin: Optional[float] = None
    exclusive_end: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[UsageGallonsRange]:
        if not data:
            return None
        return cls(begin=data.get("begin"), exclusive_end=data.get("exclusive_end"))


@dataclass(frozen=True)
class PriceTier:
    id: Optional[str] = None
    usd_per_gallon: Optional[float] = None
    price: Optional[float] = None
    price_currency: Optional[str] = None
    unit_code: Optional[str] = None
    usage_gallons: Optional[UsageGallonsRange] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[PriceTier]:
        if not data:
            return None
        return cls(
            id=_get(data, "@id"),
            usd_per_gallon=data.get("usd_per_gallon"),
            price=data.get("price"),
            price_currency=data.get("priceCurrency"),
            unit_code=data.get("unitCode"),
            usage_gallons=UsageGallonsRange.from_dict(data.get("usage_gallons")),
        )


@dataclass(frozen=True)
class PricingVersion:
    id: Optional[str] = None
    name: Optional[str] = None
    import_code: Optional[str] = None
    billing_unit: Optional[str] = None
    billing_period: Optional[str] = None
    price_currency: Optional[str] = None
    tiers: List[PriceTier] = field(default_factory=list)
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[PricingVersion]:
        if not data:
            return None
        return cls(
            id=_get(data, "@id"),
            name=data.get("name"),
            import_code=data.get("import_code"),
            billing_unit=data.get("billing_unit"),
            billing_period=data.get("billing_period"),
            price_currency=data.get("priceCurrency"),
            tiers=[
                t
                for t in (PriceTier.from_dict(item) for item in data.get("tiers") or [])
                if t is not None
            ],
            effective_from=data.get("effective_from"),
            effective_until=data.get("effective_until"),
            updated_at=data.get("updated_at"),
        )


@dataclass(frozen=True)
class ServiceConnection:
    id: str
    name: Optional[str] = None
    meter_id: Optional[str] = None
    service_type: Optional[str] = None
    measurement_period: Optional[str] = None
    is_disconnected: bool = False
    created_at: Optional[str] = None
    deactivated_at: Optional[str] = None
    features: List[str] = field(default_factory=list)
    current_pricing: Optional[PricingVersion] = None
    usage_series: Optional[IriTemplate] = None
    cost_series: Optional[IriTemplate] = None
    goal_series: Optional[IriTemplate] = None
    comparable_usage: Optional[IriTemplate] = None
    leaks: Optional[IriTemplate] = None
    timezone: Optional[str] = None
    premise: Optional[ResourceRef] = None
    usage_stats: Optional[ResourceRef] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> ServiceConnection:
        return cls(
            id=data["@id"],
            name=data.get("name"),
            meter_id=data.get("meter_id"),
            service_type=data.get("service_type"),
            measurement_period=data.get("measurement_period"),
            is_disconnected=bool(data.get("is_disconnected", False)),
            created_at=data.get("created_at"),
            deactivated_at=data.get("deactivated_at"),
            features=list(data.get("features") or []),
            current_pricing=PricingVersion.from_dict(data.get("current_pricing")),
            usage_series=IriTemplate.from_dict(data.get("usage_series")),
            cost_series=IriTemplate.from_dict(data.get("cost_series")),
            goal_series=IriTemplate.from_dict(data.get("goal_series")),
            comparable_usage=IriTemplate.from_dict(data.get("comparable_usage")),
            leaks=IriTemplate.from_dict(data.get("leaks")),
            timezone=timezone or data.get("timezone"),
            premise=ResourceRef.from_dict(data.get("premise")),
            usage_stats=ResourceRef.from_dict(data.get("usage_stats")),
        )


@dataclass(frozen=True)
class Premise:
    id: str
    name: Optional[str] = None
    premise_id: Optional[int] = None
    active: Optional[bool] = None
    people: Optional[int] = None
    account_type: Optional[str] = None
    use_type: Optional[str] = None
    bill_day: Optional[int] = None
    threshold: Optional[int] = None
    usd_alert_threshold: Optional[int] = None
    measurement_interval: Optional[str] = None
    monthly_goal_multiplier: Optional[float] = None
    address: Optional[Address] = None
    timezone: Optional[str] = None
    utility: Optional[Utility] = None
    service_connections: List[ServiceConnection] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Premise:
        address = Address.from_dict(data.get("address"))
        timezone = data.get("timezone") or timezone_for_address(address)
        return cls(
            id=data["@id"],
            name=data.get("name"),
            premise_id=data.get("premise_id"),
            active=data.get("active"),
            people=data.get("people"),
            account_type=data.get("account_type"),
            use_type=data.get("use_type"),
            bill_day=data.get("bill_day"),
            threshold=data.get("threshold"),
            usd_alert_threshold=data.get("usd_alert_threshold"),
            measurement_interval=data.get("measurement_interval"),
            monthly_goal_multiplier=data.get("monthly_goal_multiplier"),
            address=address,
            timezone=timezone,
            utility=Utility.from_dict(data.get("utility")),
            service_connections=[
                ServiceConnection.from_dict(sc, timezone=timezone)
                for sc in data.get("service_connections") or []
            ],
        )


@dataclass(frozen=True)
class User:
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    account_id: Optional[str] = None
    active: Optional[bool] = None
    measurement_interval: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_active: Optional[str] = None
    premises: List[ResourceRef] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> User:
        return cls(
            id=data["@id"],
            name=data.get("name"),
            email=data.get("email"),
            user_id=data.get("user_id") or data.get("id"),
            role=data.get("role"),
            timezone=data.get("timezone"),
            locale=data.get("locale"),
            account_id=data.get("account_id"),
            active=data.get("active"),
            measurement_interval=data.get("measurement_interval"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_active=data.get("last_active"),
            premises=[
                ref
                for ref in (
                    ResourceRef.from_dict(item) for item in data.get("premises") or []
                )
                if ref is not None
            ],
        )


@dataclass(frozen=True)
class UsagePoint:
    during: str
    total_gallons: float
    irrigation_gallons: float = 0.0
    irrigation_events: float = 0.0
    is_leaking: bool = False

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> UsagePoint:
        return cls(
            during=localize_api_time(data["during"], timezone) or data["during"],
            total_gallons=float(data.get("total_gallons") or 0.0),
            irrigation_gallons=float(data.get("irrigation_gallons") or 0.0),
            irrigation_events=float(data.get("irrigation_events") or 0.0),
            is_leaking=bool(data.get("is_leaking", False)),
        )


@dataclass(frozen=True)
class Quantity:
    value: float
    unit_code: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[Quantity]:
        if not data:
            return None
        return cls(value=float(data.get("value") or 0.0), unit_code=data.get("unitCode"))


@dataclass(frozen=True)
class Money:
    price: float
    price_currency: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional[Money]:
        if not data:
            return None
        return cls(
            price=float(data.get("price") or 0.0),
            price_currency=data.get("priceCurrency"),
        )


@dataclass(frozen=True)
class CostItem:
    name: str
    price: float
    during: Optional[str] = None
    price_currency: Optional[str] = None
    quantity: Optional[Quantity] = None
    price_specification: Optional[ResourceRef] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> CostItem:
        return cls(
            name=data.get("name") or "",
            price=float(data.get("price") or 0.0),
            during=localize_api_time(data.get("during"), timezone),
            price_currency=data.get("priceCurrency"),
            quantity=Quantity.from_dict(data.get("quantity")),
            price_specification=ResourceRef.from_dict(data.get("priceSpecification")),
        )


@dataclass(frozen=True)
class CostPoint:
    during: str
    price: float
    price_currency: Optional[str] = None
    items: List[CostItem] = field(default_factory=list)

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> CostPoint:
        return cls(
            during=localize_api_time(data["during"], timezone) or data["during"],
            price=float(data.get("price") or 0.0),
            price_currency=data.get("priceCurrency"),
            items=[
                CostItem.from_dict(item, timezone=timezone)
                for item in data.get("items") or []
            ],
        )


@dataclass(frozen=True)
class GoalPoint:
    during: str
    gallons: float

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> GoalPoint:
        return cls(
            during=localize_api_time(data["during"], timezone) or data["during"],
            gallons=float(data.get("gallons") or 0.0),
        )


@dataclass(frozen=True)
class UsageSeries:
    id: Optional[str]
    total_items: int
    members: List[UsagePoint]
    consumed_via: Optional[ResourceRef] = None
    type: str = "Collection"
    context: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> UsageSeries:
        return cls(
            id=_get(data, "@id"),
            total_items=int(data.get("totalItems") or 0),
            members=[
                UsagePoint.from_dict(m, timezone=timezone)
                for m in data.get("member") or []
            ],
            consumed_via=ResourceRef.from_dict(data.get("consumed_via")),
            type=data.get("@type", "Collection"),
            context=data.get("@context"),
        )


@dataclass(frozen=True)
class CostSeries:
    id: Optional[str]
    total_items: int
    members: List[CostPoint]
    charges_for: Optional[ResourceRef] = None
    type: str = "Collection"
    context: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> CostSeries:
        return cls(
            id=_get(data, "@id"),
            total_items=int(data.get("totalItems") or 0),
            members=[
                CostPoint.from_dict(m, timezone=timezone)
                for m in data.get("member") or []
            ],
            charges_for=ResourceRef.from_dict(data.get("charges_for")),
            type=data.get("@type", "Collection"),
            context=data.get("@context"),
        )


@dataclass(frozen=True)
class GoalSeries:
    id: Optional[str]
    total_items: int
    members: List[GoalPoint]
    goals_for: Optional[ResourceRef] = None
    type: str = "Collection"
    context: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> GoalSeries:
        return cls(
            id=_get(data, "@id"),
            total_items=int(data.get("totalItems") or 0),
            members=[
                GoalPoint.from_dict(m, timezone=timezone)
                for m in data.get("member") or []
            ],
            goals_for=ResourceRef.from_dict(data.get("goals_for")),
            type=data.get("@type", "Collection"),
            context=data.get("@context"),
        )


@dataclass(frozen=True)
class Leak:
    """Leak detected on a service connection (`via` points at the meter)."""

    id: str
    via: Optional[ResourceRef] = None
    started_at: Optional[str] = None
    resolved_at: Optional[str] = None
    est_total_volume: Optional[Quantity] = None
    est_hourly_volume: Optional[Quantity] = None
    est_total_cost: Optional[Money] = None
    is_ignored: bool = False
    is_archived: bool = False
    snoozed_until: Optional[str] = None
    usage_comp_series: Optional[IriTemplate] = None
    activities: Optional[ResourceRef] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], timezone: Optional[str] = None) -> Leak:
        return cls(
            id=data["@id"],
            via=ResourceRef.from_dict(data.get("via")),
            started_at=localize_api_time(data.get("started_at"), timezone),
            resolved_at=localize_api_time(data.get("resolved_at"), timezone),
            est_total_volume=Quantity.from_dict(data.get("est_total_volume")),
            est_hourly_volume=Quantity.from_dict(data.get("est_hourly_volume")),
            est_total_cost=Money.from_dict(data.get("est_total_cost")),
            is_ignored=bool(data.get("is_ignored", False)),
            is_archived=bool(data.get("is_archived", False)),
            snoozed_until=localize_api_time(data.get("snoozed_until"), timezone),
            usage_comp_series=IriTemplate.from_dict(data.get("usage_comp_series")),
            activities=ResourceRef.from_dict(data.get("activities")),
        )


@dataclass(frozen=True)
class LeakSeries:
    """Hydra collection of leaks for a service connection over a time range."""

    id: Optional[str]
    total_items: int
    members: List[Leak]
    type: str = "Collection"
    context: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> LeakSeries:
        return cls(
            id=_get(data, "@id"),
            total_items=int(data.get("totalItems") or 0),
            members=[
                Leak.from_dict(m, timezone=timezone) for m in data.get("member") or []
            ],
            type=data.get("@type", "Collection"),
            context=data.get("@context"),
        )


@dataclass(frozen=True)
class LeakUsageCompPoint:
    """Actual vs expected usage for a leak over one period bucket."""

    during: str
    actual_usage: Optional[Quantity] = None
    expected_usage: Optional[Quantity] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> LeakUsageCompPoint:
        return cls(
            during=localize_api_time(data["during"], timezone) or data["during"],
            actual_usage=Quantity.from_dict(data.get("actual_usage")),
            expected_usage=Quantity.from_dict(data.get("expected_usage")),
        )


@dataclass(frozen=True)
class LeakUsageCompSeries:
    """Hydra collection from a leak's ``usage_comp_series`` template."""

    id: Optional[str]
    total_items: int
    members: List[LeakUsageCompPoint]
    type: str = "Collection"
    context: Optional[str] = None

    @classmethod
    def from_dict(
        cls, data: Dict[str, Any], timezone: Optional[str] = None
    ) -> LeakUsageCompSeries:
        return cls(
            id=_get(data, "@id"),
            total_items=int(data.get("totalItems") or 0),
            members=[
                LeakUsageCompPoint.from_dict(m, timezone=timezone)
                for m in data.get("member") or []
            ],
            type=data.get("@type", "Collection"),
            context=data.get("@context"),
        )
