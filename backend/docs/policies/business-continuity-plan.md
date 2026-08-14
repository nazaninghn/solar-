# Business Continuity & Communication Plan (STEP 83)

| Field | Owner | Version | Effective Date | Review Date |
|---|---|---|---|---|
| Engineering | Engineering | 1.0 | 2026-08-14 | 2027-02-14 |

This is the piece `docs/operations/incidents.md` and
`docs/operations/disaster-recovery.md` deliberately don't cover: not "how do
we technically recover" (that's the DR plan) but **who tells whom, what, and
when** — and what the business does while recovery is in progress. Before
this document, `incidents.md`'s communication section was two lines
("team channel updated every 15 min", "stakeholders notified for P0/P1")
with no definition of who a stakeholder is, no template, no channel.

## Essential Business Functions, Ranked

Same list `docs/operations/disaster-recovery.md`'s "Critical vs Non-Critical"
table already established — restated here as the thing this plan protects,
not duplicated logic:

| Must keep running | Can be degraded/paused during an incident |
|---|---|
| Authentication (customers must be able to log in) | Advanced analytics / BI dashboards |
| Core API + dashboard read access | Report generation |
| Device telemetry ingestion | Email notifications (queue and send later) |
| Billing data integrity | Webhook delivery to integrations |
|  | Historical data backfill |

## Who Communicates What, To Whom

| Audience | Trigger | Channel | Owner |
|---|---|---|---|
| Internal engineering | Any P0/P1 (per `incidents.md`'s severity table) | Team channel, updated every 15 min per the existing incident process | Incident owner (whoever acknowledged it) |
| Company admins of affected organizations | P0 outage lasting >15 min, or any confirmed data-integrity issue | Email to each affected org's `COMPANY_ADMIN` users (`User.role == "COMPANY_ADMIN"`, `User.organization_id` scoped to what's actually affected) | Incident owner, or whoever they designate |
| All customers | Platform-wide P0 (not a single-org issue) | Email to all active `COMPANY_ADMIN`/`FACTORY_MANAGER` users — this platform has no separate status page or SMS channel today (confirmed: no `statuspage`-style integration exists in this codebase) | Engineering lead |
| Vendors (Render, Open-Meteo) | Only if the incident traces to their outage, to confirm ETA | Vendor's own support channel — see `docs/policies/vendor-policy.md` for the tracked vendor list and risk tiers | Incident owner |

**A real, stated gap:** there is no dedicated public status page or SMS/push
notification channel — customer communication during a platform-wide outage
is email-only today. This is a genuine limitation worth revisiting once
customer count justifies the operational cost of a status page, not
something to pretend is solved by documentation.

## Communication Templates

**Initial customer notification (within 30 min of confirmed P0):**
> We're currently experiencing [degraded performance / an outage] affecting
> [specific feature, e.g. "device telemetry ingestion"]. Our team is
> actively investigating. We'll update you within [X] with more
> information. [Affected organizations only, if scoped.]

**Resolution notification:**
> The issue affecting [feature] has been resolved as of [time, UTC]. Root
> cause: [one sentence]. [If applicable: no customer data was lost / X
> minutes of telemetry data may need to be re-sent from affected devices.]
> A full postmortem will be shared within 48 hours per our standard process.

**No update yet, but time has passed (every 30-60 min during an extended P0):**
> Still investigating [feature] issue first reported at [time]. Current
> status: [one sentence]. Next update by [time].

These are starting points, not scripts to paste verbatim — the incident
owner adjusts specifics, but every P0/P1 external communication should hit
these three beats: what's affected, what we know, when we'll say more.

## Escalation Hierarchy

Reuses the existing on-call rotation (`OnCallSchedule`,
`app/modules/alerts/oncall.py`, Step 77) rather than defining a second one:
the on-call engineer is first responder for any severity. Escalation beyond
on-call:

1. **P0/P1 not acknowledged within its response-time target** (per
   `incidents.md`'s table) — on-call's designated backup is paged.
2. **Any incident touching billing data or requiring customer-facing
   communication** — the incident owner loops in whoever owns customer
   relationships (today: the same person, since this is a small team; this
   line exists so the plan doesn't silently break once that's no longer true).
3. **Security incident (credential compromise, suspected breach)** — follows
   `docs/operations/disaster-recovery.md`'s "Credential Compromise" scenario
   (contain, rotate, review, notify) in addition to this plan's
   communication steps; `SecurityEvent` correlation (Step 79, populated
   with real data since Step 82) is the detection signal, not a separate
   manual trigger.

## During Extended Recovery (Business Continuity, Not Just Technical Recovery)

For anything longer than the RTO targets in
`docs/operations/disaster-recovery.md` (i.e., recovery is taking longer than
planned):

- The incident owner makes a call on whether degraded-mode operation is
  possible (e.g., dashboard read-only while write paths are down) rather
  than a hard "everything or nothing" outage — matching the "Critical vs
  Non-Critical" split above.
- Customer communication cadence increases to every 30-60 min even without
  new information, per the template above — silence during a long outage is
  worse than an "still working on it" update.
- After resolution, the postmortem (`incidents.md`'s existing requirement
  for P0/P1) explicitly includes whether communication itself met this
  plan's targets — not just the technical recovery timeline.

## Relationship to Other Documents

This plan sits alongside, not instead of:
- `docs/operations/incidents.md` — technical incident lifecycle and severity
- `docs/operations/disaster-recovery.md` — RPO/RTO targets, backup policy,
  disaster scenarios and technical recovery steps
- `docs/policies/vendor-policy.md` — third-party dependency risk (Render,
  Open-Meteo)
- `docs/security/zero-trust-architecture.md` — security event detection
  (Step 82) that feeds the security-incident escalation path above
