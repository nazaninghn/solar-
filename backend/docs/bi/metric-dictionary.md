# Metric Dictionary & North Star (STEP 80)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Business/Product | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

## North Star Metric

**Weekly Active Factories** — the count of distinct `factories` whose
organization has at least one authenticated request in the trailing 7
days (via `api_usage_metrics`, populated since Step 78).

**Why this, not MRR or signups:** SolarFlow's actual value delivery is
a factory operator checking their energy state, acting on a
recommendation, or reviewing savings — not a login and not a dollar.
Revenue (MRR) lags behind usage and is currently zero in this
deployment (no billing integration is live yet — see revenue-metrics.md).
Signups measure acquisition, not value delivered. A factory that stops
being actively checked is a factory at risk of churn regardless of
whether its subscription is still nominally active. This is a judgment
call, not a measured fact — worth revisiting once real subscription
data exists and revenue metrics become meaningful (see
`app/modules/bi/service.py`'s `north_star.py` docstring for how to
recompute it if this changes).

## Metric Dictionary

### Acquisition & Activation

| Metric | Definition | Source | Computed By |
|---|---|---|---|
| Signups | New `users` rows per period | `users.created_at` | `app.modules.bi.funnel` |
| Organizations created | New `organizations` rows per period | `organizations.created_at` | `app.modules.bi.funnel` |
| Activation rate | % of new orgs that create >=1 factory within 7 days of signup | `organizations.created_at`, `factories.created_at` | `app.modules.bi.funnel.compute_activation_rate` |
| Funnel stage counts | Signup -> First Factory -> First Device -> First Recommendation | `organizations`, `factories`, `devices`, `recommendations` created_at | `app.modules.bi.funnel.compute_funnel` |

### Engagement & Retention

| Metric | Definition | Source | Computed By |
|---|---|---|---|
| Weekly Active Factories (North Star) | Factories with >=1 API request in trailing 7 days | `api_usage_metrics` | `app.modules.bi.retention` |
| Retention rate | % of a signup cohort still active (last_login_at within window) N periods later | `users.created_at`, `users.last_login_at` | `app.modules.bi.retention.compute_cohort_retention` |
| Churn rate | Inverse of retention — % of a cohort no longer active | Same as above | `app.modules.bi.retention.compute_cohort_retention` |

### Revenue (currently $0 — see revenue-metrics.md)

| Metric | Definition | Source | Computed By |
|---|---|---|---|
| MRR | Sum of active subscriptions' monthly-equivalent price | `subscriptions`, `plans` | `app.modules.bi.revenue.compute_mrr` |
| ARR | MRR x 12 | Same | `app.modules.bi.revenue.compute_arr` |
| Revenue churn | MRR lost to cancellations / MRR at period start | `subscriptions.cancelled_at` | `app.modules.bi.revenue.compute_revenue_churn` |
| LTV | Average revenue per organization / revenue churn rate | Derived from MRR + churn | `app.modules.bi.revenue.compute_ltv` |
| CAC | **Out of scope** — no marketing/ad spend data exists anywhere in this system. Would need a real acquisition-cost data source before this can be computed, not fabricated. | N/A | Not built |

### Segmentation

| Metric | Definition | Source | Computed By |
|---|---|---|---|
| By plan tier | Organization count per `plans.name` | `subscriptions`, `plans` | `app.modules.bi.segmentation` |
| By industry | Factory count per `factories.industry` | `factories.industry` | `app.modules.bi.segmentation` |
| By size | Organizations bucketed by factory/device count | `factories`, `devices` | `app.modules.bi.segmentation` |

## Data Lineage

```
users.created_at ──┐
organizations.created_at ─┤→ funnel/activation (app.modules.bi.funnel)
factories.created_at ──┤
devices.created_at ──┤
recommendations.created_at ─┘

users.last_login_at ──→ retention/cohort (app.modules.bi.retention)
api_usage_metrics (Step 78) ──→ North Star (Weekly Active Factories)
subscriptions + plans + invoices ──→ revenue (app.modules.bi.revenue) — currently empty
factories.industry, factory/device counts ──→ segmentation (app.modules.bi.segmentation)
```

Every number this dictionary defines traces back to a real column
already in the schema — nothing here is a fabricated or simulated
figure. Where the underlying table has zero rows (billing), the
metric correctly computes to zero rather than a placeholder value.
