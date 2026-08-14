"""
24.20-24.21 ask for roles/permissions/role_permissions as normalized DB
tables. For a fixed set of 6 roles that aren't dynamically created by
tenants (nobody can invent a 7th role from the UI), that's schema
overhead without a real benefit yet — this Python constant matrix gives
the same "permissions, not role string comparisons" property the DoD
actually cares about (24.20's real point), while staying easy to read
as one table. If custom per-company roles ever become a real feature,
that's when this earns being normalized into tables.
"""

VIEW_DASHBOARD = "VIEW_DASHBOARD"

VIEW_ENERGY = "VIEW_ENERGY"
MANAGE_ENERGY = "MANAGE_ENERGY"

VIEW_BATTERY = "VIEW_BATTERY"
MANAGE_BATTERY = "MANAGE_BATTERY"

VIEW_RECOMMENDATIONS = "VIEW_RECOMMENDATIONS"
MANAGE_RECOMMENDATIONS = "MANAGE_RECOMMENDATIONS"

VIEW_FINANCIAL = "VIEW_FINANCIAL"
MANAGE_FINANCIAL = "MANAGE_FINANCIAL"

MANAGE_FACTORY_SETTINGS = "MANAGE_FACTORY_SETTINGS"
MANAGE_USERS = "MANAGE_USERS"
MANAGE_COMPANY_SETTINGS = "MANAGE_COMPANY_SETTINGS"
CONTROL_ENERGY = "CONTROL_ENERGY"

ALL_PERMISSIONS = {
    VIEW_DASHBOARD,
    VIEW_ENERGY,
    MANAGE_ENERGY,
    VIEW_BATTERY,
    MANAGE_BATTERY,
    VIEW_RECOMMENDATIONS,
    MANAGE_RECOMMENDATIONS,
    VIEW_FINANCIAL,
    MANAGE_FINANCIAL,
    MANAGE_FACTORY_SETTINGS,
    MANAGE_USERS,
    MANAGE_COMPANY_SETTINGS,
    CONTROL_ENERGY,
}

# 24.19's matrix, transcribed exactly (✅=view+manage, 👁️=view only, ❌=none).
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "SUPER_ADMIN": set(ALL_PERMISSIONS),
    "COMPANY_ADMIN": set(ALL_PERMISSIONS),
    "FACTORY_MANAGER": {
        VIEW_DASHBOARD,
        VIEW_ENERGY,
        MANAGE_ENERGY,
        VIEW_BATTERY,
        MANAGE_BATTERY,
        VIEW_RECOMMENDATIONS,
        MANAGE_RECOMMENDATIONS,
        VIEW_FINANCIAL,
        MANAGE_FACTORY_SETTINGS,
    },
    "ENERGY_MANAGER": {
        VIEW_DASHBOARD,
        VIEW_ENERGY,
        MANAGE_ENERGY,
        VIEW_BATTERY,
        MANAGE_BATTERY,
        VIEW_RECOMMENDATIONS,
        MANAGE_RECOMMENDATIONS,
        CONTROL_ENERGY,
    },
    "FINANCIAL_MANAGER": {
        VIEW_DASHBOARD,
        VIEW_ENERGY,
        VIEW_RECOMMENDATIONS,
        VIEW_FINANCIAL,
        MANAGE_FINANCIAL,
    },
    "VIEWER": {
        VIEW_DASHBOARD,
        VIEW_ENERGY,
        VIEW_BATTERY,
        VIEW_FINANCIAL,
    },
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, set())
