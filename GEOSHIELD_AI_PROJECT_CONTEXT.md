# GEOSHIELD AI ENTERPRISE — MASTER PROJECT CONTEXT

## LAST UPDATED
19 September 2026
## PROJECT IDENTITY

Project: GeoShield AI Enterprise

Purpose:
Geospatial Intelligence, Disaster Management, Environmental Monitoring and Decision Support.

GeoShield AI is an integrated intelligence platform combining satellite observations, weather data, geospatial data, specialized analytical engines, risk assessment, analytics, alerts, reporting and AI assistance into one system.

Core principle:

DATA -> OBSERVATION -> FUSION -> ANALYSIS -> RISK -> INTELLIGENCE -> ACTION

---

# CORE ARCHITECTURE

DATA SOURCES
-> SATELLITES / EXTERNAL DATA
-> DATA INGESTION & CONNECTORS
-> MAIN ENGINE
-> SPECIALIZED INTELLIGENCE ENGINES
-> AI / RISK / ANALYTICS
-> ALERTS / REPORTS / DECISION SUPPORT
-> GEOSHIELD COMMAND-CENTER UI
-> HUMAN DECISION

The Main Engine is the central orchestration layer.

Specialized engines should communicate through the Main Engine rather than becoming isolated systems.

---

# CORE DATA SOURCES

- Sentinel-2 — vegetation and land-surface intelligence, especially NDVI
- GPM — precipitation/rainfall observations
- Weather data — temperature, humidity, wind and related atmospheric conditions
- VIIRS / MODIS — additional environmental and vegetation observations
- SRTM / elevation data — terrain and slope analysis
- Sentinel-1 SAR — planned soil-moisture/ground-condition intelligence
- GIS boundaries and infrastructure datasets
- Future external disaster and emergency-response services

GeoShield should increasingly use multi-source data fusion instead of relying on a single measurement.

---

# SATELLITE / COPERNICUS STATUS

Satellite connectivity is integrated into the GeoShield architecture.

Copernicus Data Space authentication has previously been verified successfully.

Sentinel-2 is used for vegetation and land intelligence, including county-level NDVI analysis.

The current NDVI system performs county-level analysis across Kenya's 47 counties.

Important:

Satellite connectivity should not be confused with successful retrieval of every individual product or statistical request. External provider rate limits and transient failures must be handled safely.

---

# FLOOD INTELLIGENCE

## Flood Engine — CURRENT STATUS

STATUS: ACTIVE — CATCHMENT / DRAINAGE PIVOT COMPLETED AND VERIFIED

The Flood Engine has moved beyond a purely rainfall-driven model.

The `calculate_flood_risk()` function in:

`core/risk_engine.py`

was updated to include:

- Rainfall conditions
- Existing `upland_skm` catchment-size factor
- `reference_discharge_cms` as a separate static hydrology scoring factor
- HydroRIVERS static reference discharge
- Static hydrology metadata

The new output includes:

`static_hydrology_factors_used`

This explicitly distinguishes static hydrology information from live discharge observations.

Static reference discharge must NEVER be represented as live river discharge.

## VERIFICATION

The updated Flood Engine was verified through:

`/api/flood/live`

and the GeoShield UI.

Under real inputs:

Marsabit moved from:

Low -> Moderate

The resulting risk mathematics was checked against the implemented formula and matched correctly.

## FLOOD MODEL PHILOSOPHY

Flood risk should progressively move toward:

RAINFALL
+
CATCHMENT CHARACTERISTICS
+
TERRAIN
+
SLOPE
+
DRAINAGE
+
LOW-LYING / ACCUMULATION CONDITIONS
+
HYDROLOGICAL CONTEXT

The same rainfall amount should not automatically produce the same flood risk everywhere.

Flat and poorly drained areas can behave differently from steep and well-drained terrain.

## FLOOD VISUALIZATION

Flood severity should use clearly differentiated severity colors:

- Low — green
- Moderate — yellow / amber
- High — orange
- Extreme — red

## FORECAST / ANTICIPATORY INTELLIGENCE GAP

A real architectural gap has been identified.

GeoShield currently provides primarily reactive live-condition scoring.

It does NOT yet contain a dedicated forecast / anticipatory flood-risk layer.

Current active flood warnings may be anticipatory based on forecast rainfall rather than evidence of active flooding at the exact current moment.

Future roadmap:

FORECAST DATA
-> EXPECTED RAINFALL
-> EXPECTED HYDROLOGICAL CONDITIONS
-> TERRAIN / DRAINAGE CONTEXT
-> ANTICIPATORY RISK
-> EARLY WARNING

This should remain a distinct future capability rather than being falsely represented as already operational.

---

# AGRICULTURE INTELLIGENCE

STATUS: SUBSTANTIALLY IMPLEMENTED

Current functionality can retrieve:

- Rainfall
- Temperature
- Humidity
- Wind
- Sentinel-2 NDVI
- Agriculture risk score
- Severity
- Recommended actions

The Agriculture Engine is NOT the current development priority.

---

# NDVI SYSTEM — CURRENT INCIDENT / RELIABILITY WORK

## ROOT CAUSE CONFIRMED

The NDVI null-result problem was investigated and the root cause was confirmed.

The Copernicus Statistical API is returning:

`429 RATE_LIMIT_EXCEEDED`

The primary trigger is excessive concurrent request cycles.

Multiple GeoShield endpoints can independently initiate a complete 47-county NDVI fetch when the cache is cold.

Examples include:

- `/api/agriculture/live`
- `/api/flood/live`
- `/api/dashboard`
- Startup warmup

When these execute concurrently, each can initiate its own 47-county cycle.

This results in many Copernicus requests being sent simultaneously with insufficient pacing.

## ROOT CAUSE STATUS

CONFIRMED — NOT A GUESS.

The following possible causes were investigated and ruled out:

### County-name mismatch

`Keiyo-Marakwet` versus official:

`Elgeyo-Marakwet`

was checked.

The NDVI and river-lookup files agree internally, so this is NOT the active cause of the null-result problem.

The official Kenyan spelling should still be preferred where appropriate.

### Connector happy-path failure

An isolated sequential test successfully retrieved:

47 / 47 counties

This demonstrated that the basic connector logic can work correctly when requests are made sequentially without the concurrent request storm.

---

# NDVI FIXES ALREADY APPLIED

The following changes have been written to disk.

## 1. STALE-WHILE-REVALIDATE FALLBACK

When a county fails to retrieve fresh NDVI data:

- The system attempts to use the last-known-good value.
- The stale result is clearly logged as stale.
- The system no longer immediately converts a temporary failure into `null`.

Only a county with ZERO previous successful NDVI result should return `null`.

This prevents temporary external API failures from unnecessarily destroying usable intelligence.

## 2. DEEP ERROR LOGGING

Deep error logging was added.

The system now exposes the actual Copernicus response body when a request fails.

This was critical for identifying the actual:

`429 RATE_LIMIT_EXCEEDED`

response rather than incorrectly guessing that the problem was caused by county names or missing satellite data.

## 3. CONCURRENCY LOCK

A `threading.Lock()` has been added around the NDVI `search()` process.

Purpose:

Only ONE complete 47-county NDVI fetch cycle should run at a time.

This prevents multiple endpoint-triggered cycles from simultaneously hammering Copernicus.

## 4. REQUEST PACING

A delay of approximately:

`0.8 seconds`

is inserted between county requests.

This reduces request bursts against the Copernicus Statistical API.

## 5. RETRIES

Per-county retries have been added.

Current design:

- Up to 3 retries
- Approximately 5-second backoff
- Retry handling for rate-limit failures
- Fall back to stale data when fresh retrieval remains unsuccessful

---

# NDVI LIVE TEST STATUS

IMPORTANT:

The concurrency-lock + pacing + retry patch has been:

- Written to disk
- Syntax validated

BUT:

It has NOT YET been fully tested under live concurrent server load.

Therefore DO NOT claim that the 429 problem has been completely solved yet.

## NEXT REQUIRED TEST

Restart the FastAPI server:

`uvicorn backend.main:app --reload`

Then trigger concurrent load using the same PowerShell `Start-Job` burst previously used against:

`/api/agriculture/live`

Verify from the logs that:

1. No two complete 47-county fetch cycles run simultaneously.
2. Copernicus 429 errors decrease substantially or disappear.
3. Any remaining 429 responses are retried.
4. Temporary failures fall back to stale NDVI rather than immediately becoming `null`.
5. A county with previous successful data remains usable during temporary Copernicus failure.

Only after this live test passes should the NDVI reliability fix be considered fully verified.

---

# FUTURE AGRICULTURE RISK MODEL

The agriculture risk model should move away from generic logic such as:

Low rainfall + high temperature + low humidity + low NDVI = high agricultural risk.

Risk should become crop-specific and location-specific.

Create a Kenya County Crop Registry covering all 47 counties.

Agricultural contexts include:

- Maize regions
- Tea / coffee highlands
- Arid and semi-arid zones
- Sorghum / millet areas
- Livestock-dominant zones
- Other county-specific agricultural systems

Each Crop Profile should contain:

- Optimal temperature range
- Tolerable temperature range
- Water requirement
- Drought tolerance
- Expected environmental conditions
- Other relevant agronomic characteristics

Risk should become a:

CONDITION -> CROP MISMATCH SCORE

This measures how far current environmental conditions deviate from the requirements of crops actually grown in that county.

Future agricultural intelligence should incorporate:

- Soil moisture
- Crop / yield estimates
- NDVI trends
- Rainfall anomalies
- Temperature anomalies
- Crop-specific environmental requirements

---

# INTELLIGENCE ENGINES

## Earthquake Engine

STATUS: COMPLETED

The Earthquake Engine remains intact internally even where its summary card is hidden from the main dashboard UI.

## Agriculture Engine

STATUS: SUBSTANTIALLY IMPLEMENTED

Current NDVI reliability work is active.

Agriculture is not the current development priority.

## Drought Intelligence

STATUS: ACTIVE / IMPLEMENTED

## Fire Intelligence

STATUS: IMPLEMENTED / INTEGRATED

## Flood Engine

STATUS: ACTIVE

Catchment / drainage pivot:

COMPLETED AND VERIFIED

Further expansion can incorporate additional terrain, drainage and anticipatory forecast intelligence.

## Analytics Engine

STATUS: COMPLETED — BACKEND VERIFIED

The Analytics Engine has been completed and verified as the source for combined GeoShield risk intelligence.

## OVERALL RISK DATA MODEL

The Overall Risk calculation is explicitly based on:

- Agriculture
- Fire
- Flood
- Drought

Earthquake is excluded from Overall Risk.

The Analytics Engine stores severity information in:

`analytics_history`

and `get_county_analytics()` filters the aggregated result to:

`agriculture`
`fire`
`flood`
`drought`

This prevents unrelated engines such as Earthquake from silently entering the Overall Risk calculation.

## SNAPSHOT CYCLE

`run_snapshot_cycle()` now records severity data for:

- Agriculture
- Fire
- Flood
- Drought

This provides the historical data required by county-level analytics.

## DASHBOARD BACKEND

The dashboard route now accepts:

`?county=<county>`

and passes the selected county through the relevant hazard-summary calls.

The dashboard response now contains:

`overall_risk`

sourced from:

`analytics_engine.get_county_analytics(county)`

The backend therefore supports genuine county-specific Overall Risk.

## VERIFICATION

Verified endpoint:

`/api/dashboard?county=Marsabit`

Returned:

`overall_risk: Moderate`

The underlying values were:

- Fire = Low = 0
- Drought = High = 2
- Flood = Moderate = 1
- Agriculture = High = 2

Mean:

`(0 + 2 + 1 + 2) / 4 = 1.25`

Rounded to the implemented severity scale:

`1 -> Moderate`

A separate Nairobi request produced a different correctly calculated result, confirming the calculation is genuinely county-specific rather than globally cached/shared.

## CURRENT STATUS

Backend Overall Risk logic:

**COMPLETED AND VERIFIED**

Frontend Overall Risk wiring:

**IN PROGRESS**

The remaining work is frontend integration so the dashboard displays `overall_risk` and refreshes it when the selected county changes.
# MAIN DASHBOARD — OVERALL AVERAGE RISK

The dashboard's former:

`AI Risk`

card should be represented as:

**Overall Average Risk**

It should represent the combined condition of the selected county using:

- Drought
- Fire
- Flood
- Agriculture

The Analytics Engine should be the source of this combined intelligence.

Do NOT create a duplicate dashboard-only calculation when the Analytics Engine already provides the relevant result.

---

# DASHBOARD UI

## Earthquake Card

Remove / hide the Earthquake summary card from the main dashboard UI.

DO NOT delete or damage the Earthquake Engine.

## Settings Card

Temporarily remove / hide the Settings card from the left sidebar.

These are UI-only changes.

## Map / Intelligence Separation

The GeoShield UI separates:

- Map
- Intelligence

The Map layout should be treated as stable when UI work is performed elsewhere.

Satellite intelligence belongs within the Intelligence area.

---

# ALERTS ENGINE

STATUS: DEVELOPMENT / INTEGRATION WORK

GeoShield already contains alert-related infrastructure including:

- `core/event_bus.py`
- `core/notification_*`
- `core/event_enrichment*`
- `engines/risk_alert*`
- `engines/alerts/*`
- `backend/routes/alerts*`

The alert system should eventually provide intelligent SMS and email notifications.

Notification providers should remain modular.

Potential providers include:

- Africa's Talking — SMS
- Brevo — Email

Do not make the architecture dependent on one notification provider.

## ANOMALY-BASED ALERTING

Do not rely primarily on universal fixed thresholds.

For example:

Temperature > 35 C

does not mean the same thing in every county.

Use county-specific historical climatology.

Maintain historical baselines for:

- Temperature
- Rainfall
- Humidity
- Wind
- NDVI
- Other appropriate environmental variables

Compare:

CURRENT OBSERVATION
vs
COUNTY BASELINE

The alert system should focus on unusual changes relative to local conditions.

---

## ALERT CONFIGURATION DISCOVERY

During the database/configuration audit, `core/config.py` was inspected.

The centralized configuration already contains scaffolding for:

- Africa's Talking SMS settings
- Alert recipient configuration

These settings are currently relevant to the future Alerts Engine implementation.

This means the Alerts Engine should reuse the existing centralized configuration rather than introducing a second independent configuration system.

The existence of configuration scaffolding does NOT by itself mean SMS alert delivery is fully operational.

Actual alert generation, anomaly detection, provider integration and end-to-end notification delivery must still be verified separately.

# EMERGENCY RESOURCES AND ROUTING

GeoShield should maintain spatial emergency resources for every county.

Examples:

- Hospitals
- Fire stations
- Water points
- Emergency facilities
- Disaster-response centers
- Relevant infrastructure

An existing infrastructure table already contains some resource information.

Expand existing infrastructure rather than unnecessarily duplicating it.

Emergency routing should calculate:

INCIDENT -> EMERGENCY RESOURCE

Possible routing providers:

- TomTom
- OpenRouteService
- OSRM

Avoid total dependence on one provider.

Compare:

- Free-tier limits
- API limits
- Coverage
- Routing quality
- Reliability
- Cost
- Self-hosting requirements

---

# REPORTS ENGINE

STATUS: TO BE DEVELOPED

Generate professional downloadable PDF disaster / intelligence reports containing, where relevant:

- Incident information
- Location
- Maps
- Satellite observations
- Weather
- Risk scores
- Engine outputs
- Analytics
- Recommendations
- Historical comparisons
- Charts
- Supporting information

---

# GEOSHIELD DISASTER VIDEO STUDIO

There is a separate project:

GeoShield Disaster Video Studio

It is intended to generate professional disaster-documentary/video reports using:

- Disaster imagery
- Video
- Maps
- Satellite information
- Weather information
- Incident data
- Music
- User-provided voiceover scripts

Keep this project separate from the main GeoShield platform during development.

Future architecture:

GeoShield Intelligence
-> API
-> Disaster Video Studio
-> Documentary / Video Report

Do NOT assume this integration already exists.

Inspect the Video Studio API/interface before implementing the integration.

---

# FUTURE AI INTELLIGENCE LAYER

GeoShield should eventually contain a dedicated AI Intelligence Layer beyond individual disaster engines.

Capabilities:

### A. Cross-platform intelligence

Analyze multiple engine outputs and identify relationships and patterns.

### B. Recommendations

Suggest appropriate disaster-management actions and operational insights.

### C. System / code assistance

Assist authorized developers in identifying GeoShield software errors.

### D. Cybersecurity assistance

Assist with security monitoring and identifying potential security problems.

### E. GeoShield AI Chat

Provide a conversational interface for disaster-management questions.

The AI should remain scoped to:

- Disaster management
- Environmental intelligence
- GeoShield-supported domains

It must never expose:

- API keys
- Passwords
- Private credentials
- Secrets
- Protected system information
- Unauthorized internal information

Strong authorization, data boundaries and security guardrails are required.

---

# DRAW-YOUR-OWN-AREA ANALYSIS

Future capability:

Allow users to draw an arbitrary polygon rather than being restricted to county boundaries.

For a user-drawn farm or other area, GeoShield should analyze:

- NDVI
- Soil moisture
- Temperature
- Rainfall
- Slope
- Other environmental indicators
- Agricultural recommendations

A polygon-drawing interface such as Leaflet Draw can be used.

Connectors and endpoints should accept user-drawn geometry rather than only predefined county geometry.

Sentinel Hub Statistical API can operate on arbitrary polygon geometry, allowing this capability to build on the existing satellite architecture.

---

# CURRENT DEVELOPMENT PRIORITY

The major completed milestones are:

1. Flood Engine catchment/drainage pivot — COMPLETED AND VERIFIED
2. NDVI concurrency/rate-limit reliability — FULLY VERIFIED
3. Analytics Engine — COMPLETED
4. Overall Risk backend calculation — COMPLETED AND VERIFIED

## CURRENT ACTIVE WORK

### 1. DATABASE RELOCATION

Move:

`database/geoshield.db`

off the Google Drive-synchronized project path.

Use:

`settings.data_dir`

from:

`core/config.py`

The configured default is a local Windows data directory under:

`%LOCALAPPDATA%\GeoShield`

Update all identified database consumers consistently.

Then re-measure county endpoint performance.

### 2. COMPLETE OVERALL RISK FRONTEND INTEGRATION

Update:

`frontend` dashboard JavaScript

to consume:

`data.overall_risk`

instead of:

`data.ai_risk`

County selection must trigger:

`/api/dashboard?county=X`

and refresh the Overall Risk card.

### 3. CLEAN DEAD DASHBOARD CODE

Inspect the hardcoded `"bottom"` object in `dashboard.py`.

Remove it if confirmed unused, or deliberately connect it to the actual county data service.

### 4. CLOSE OVERALL RISK END-TO-END

Verify:

COUNTY CLICK
-> COUNTY-SPECIFIC API REQUEST
-> ANALYTICS ENGINE
-> OVERALL RISK
-> FRONTEND CARD

using multiple counties.

### 5. ALERTS ENGINE

After Overall Risk is closed end-to-end, begin the Alerts Engine.

Reuse the existing alert-related configuration in:

`core/config.py`

including the existing Africa's Talking and alert-recipient configuration scaffolding.

# DATABASE RELOCATION SESSION — 19 SEPTEMBER 2026

## OBJECTIVE

Continue the performance investigation by moving:

`database/geoshield.db`

off the Google Drive-synchronized GeoShield project directory.

## DATABASE REFERENCE AUDIT

A project-wide PowerShell search was performed across:

- `backend\**\*.py`
- `core\**\*.py`
- `dashboard\**\*.py`

using:

`geoshield\.db|DB_PATH`

Four direct database consumers were identified:

### 1. `backend/routes/resources.py`

Current database reference:

`DATABASE = "database/geoshield.db"`

### 2. `backend/analytics/analytics_engine.py`

Current database construction:

`PROJECT_ROOT / "database" / "geoshield.db"`

The file is used for SQLite connections and existence checks.

### 3. `core/engines/main_engine.py`

Current database path:

`Path("database/geoshield.db")`

Used for database existence checks, SQLite connections and resource availability reporting.

### 4. `dashboard/services/county_service.py`

Current database construction:

`PROJECT_ROOT / "database" / "geoshield.db"`

Used for county data queries.

## CENTRAL CONFIGURATION INSPECTION

`core/config.py` was inspected because the NDVI connector already imports the centralized:

`settings`

object.

A new centralized data directory setting was added and verified.

The configuration contains:

`data_dir`

using:

`GEOSHIELD_DATA_DIR`

with the Windows default:

`%LOCALAPPDATA%\GeoShield`

and fallback:

`C:/GeoShield_data/GeoShield`

This establishes the intended single source of truth for local runtime data.

## CURRENT STATUS

Central `data_dir` configuration:

**ADDED AND VERIFIED**

Database file migration:

**NOT YET EXECUTED**

Four database consumers:

**IDENTIFIED**

Database-path rewiring:

**NEXT STEP**

Database performance verification:

**PENDING**

## DESIGN DECISION

Use the centralized configuration rather than independently hardcoding a new local path in each file.

Target:

`settings.data_dir / "geoshield.db"`

This avoids future path inconsistencies and allows the local data directory to be changed through:

`GEOSHIELD_DATA_DIR`

without modifying multiple source files.

## ALERT CONFIGURATION DISCOVERY

The inspection of `core/config.py` also confirmed that configuration scaffolding already exists for:

- Africa's Talking SMS
- Alert recipients

This should be reused when development reaches the Alerts Engine.

The configuration scaffolding should not be interpreted as proof that end-to-end SMS delivery is already operational.

---

# GEOSHIELD DEVELOPMENT PHILOSOPHY

GeoShield should progressively move from simple threshold-based systems toward:

CONTEXT-AWARE
+
SPATIALLY AWARE
+
HISTORICALLY AWARE
+
MULTI-SOURCE
+
EXPLAINABLE INTELLIGENCE

## Agriculture

Not:

"It's hot -> agriculture risk."

Instead:

"Current conditions compared with the requirements of crops actually grown in this county."

## Flood

Not:

"Heavy rain -> flood."

Instead:

"Rainfall + terrain + slope + drainage + low-lying geography + hydrological context -> flood risk."

## Alerts

Not:

"Temperature > 35 C -> alert."

Instead:

"Current conditions are significantly unusual compared with this county's historical baseline -> investigate / alert."

## Overall Risk

Not:

"One generic AI score."

Instead:

"Drought + Fire + Flood + Agriculture -> Analytics Engine -> Overall Average Risk."

---

# DEVELOPMENT RULES

1. Inspect the existing architecture before changing files.
2. Reuse the existing Main Engine and connector architecture where appropriate.
3. Do not duplicate functionality unnecessarily.
4. Do not break completed engines while developing new ones.
5. Keep specialized engines modular.
6. Use real data where the system already supports it.
7. Clearly distinguish implemented functionality from planned functionality.
8. Never claim a future capability is already operational.
9. Avoid hard-coded assumptions where a data-driven model is appropriate.
10. Prefer multi-source intelligence over dependence on one data source.
11. Build county-specific intelligence where environmental differences matter.
12. Preserve existing APIs unless a deliberate architectural change is required.
13. UI changes should not unnecessarily modify backend intelligence.
14. Agriculture Engine is NOT the current priority unless specifically requested.
15. Verify external-data behavior under realistic concurrent load.
16. Do not treat temporary external API failure as missing environmental data.
17. Preserve last-known-good intelligence where safe and appropriate.
18. The Main Engine remains the central orchestration layer.
19. Do not falsely claim live verification when a change has only been syntax validated.
20. GeoShield development workflow uses VS Code Terminal / PowerShell only.
21. Do NOT provide Cursor, GitHub Copilot or VS AI instructions unless explicitly requested by the user.

---

# PROJECT WORKFLOW

CORE PIPELINE:

DATA
-> OBSERVE
-> INGEST
-> NORMALIZE
-> FUSE
-> ANALYSE
-> RISK ASSESSMENT
-> INTELLIGENCE
-> ALERT / REPORT / DECISION SUPPORT
-> HUMAN DECISION

---

# LONG-TERM PURPOSE

GeoShield AI is intended to become a unified platform for:

- Disaster management
- Agriculture intelligence
- Flood monitoring
- Drought monitoring
- Fire intelligence
- Environmental monitoring
- GIS / spatial intelligence
- Emergency response
- Infrastructure intelligence
- Risk analysis
- Alerts
- Reporting
- AI-assisted decision support

The system should evolve from:

RAW DATA
-> STRUCTURED INTELLIGENCE
-> ACTIONABLE DECISION SUPPORT

---

# CORE VALUE PROPOSITION

GeoShield AI transforms distributed geospatial, satellite, environmental and disaster data into structured intelligence that helps people understand risk, monitor changing conditions and make better-informed decisions.

Core workflow:

OBSERVE
-> FUSE
-> ANALYSE
-> UNDERSTAND RISK
-> RESPOND

GeoShield AI Enterprise

Geospatial Intelligence for a Safer, Smarter World


# DASHBOARD — OVERALL AVERAGE RISK

STATUS: BACKEND COMPLETED / FRONTEND INTEGRATION IN PROGRESS

The Overall Risk card is intended to display the combined county-level intelligence from:

DROUGHT
+
FIRE
+
FLOOD
+
AGRICULTURE
->
ANALYTICS ENGINE
->
OVERALL RISK

## BACKEND STATUS

The backend now:

- Accepts a county parameter on `/api/dashboard`
- Retrieves the selected county's hazard information
- Calculates/returns `overall_risk`
- Sources Overall Risk from the Analytics Engine
- Excludes Earthquake from the Overall Risk calculation

Backend verification has been completed successfully.

## FRONTEND ISSUE IDENTIFIED

The frontend previously referenced:

`data.ai_risk`

This field does not exist in the dashboard API response.

The correct field is:

`data.overall_risk`

The HTML label has already been changed from:

`🤖 AI Risk`

to:

`🤖 Overall Risk`

The remaining frontend work is:

1. Change `dashboard.js` from `data.ai_risk` to `data.overall_risk`.
2. Ensure `/api/dashboard?county=X` is requested when a county is selected.
3. Trigger the Overall Risk card update from the county-selection flow.
4. Verify that different counties display their own Overall Risk values.

The intended behavior is:

COUNTY CLICK
->
SELECTED COUNTY
->
`/api/dashboard?county=X`
->
ANALYTICS ENGINE
->
`overall_risk`
->
OVERALL RISK CARD

No duplicate frontend risk calculation should be introduced.


# COUNTY DASHBOARD DATA AND PERFORMANCE

## CURRENT DATA SOURCE

The bottom county-information cards are powered by:

`/county/{name}`

and:

`dashboard/services/county_service.py`

The endpoint uses data from:

`analytics_history`

rather than directly triggering the live satellite connectors for every metric.

Therefore the bottom cards are based on real GeoShield data rather than fabricated/hardcoded frontend values.

## PERFORMANCE INVESTIGATION

The original county endpoint was opening approximately six separate SQLite connections per request, one for each metric lookup.

Because the database is located inside:

`N:\My Drive\GeoShield_Project`

which is a Google Drive-synchronized location, repeated SQLite connection/file touches introduced significant filesystem/synchronization overhead.

Measured request times were approximately:

- 1.8–4.2 seconds initially
- Approximately 2.8 seconds during subsequent measurement
- Approximately 1.0 second
- Approximately 0.4 seconds after repeated accesses

The decreasing timings indicated filesystem warming/cache effects rather than purely application-level computation cost.

## PERFORMANCE FIX ALREADY APPLIED

The county service was changed to:

- Use a single SQLite connection per request
- Use one combined query instead of six separate database lookups

This produced a measurable improvement.

However, the database still resides on the Google Drive-synced project path.

## NEXT PERFORMANCE CHANGE

The selected solution is:

**Option B — Move the SQLite database to a non-synced local path.**

Possible destination:

`C:\GeoShield_data\`

or:

`%LOCALAPPDATA%\GeoShield\`

The objective is to remove Google Drive synchronization overhead from the live SQLite workload.

Required changes:

- Move `database/geoshield.db`
- Update `DB_PATH` in `dashboard/services/county_service.py`
- Update `DB_PATH` in `analytics_engine.py`
- Verify all other database consumers that reference the old path
- Re-measure county endpoint performance afterward

Do NOT assume the move solved the problem until performance is measured again.

## BOTTOM OBJECT IN DASHBOARD ROUTE

The `dashboard.py` route also contains a separate:

`"bottom"`

object

whose values are currently hardcoded to:

`"--"`

This is separate from `/county/{name}` and is not the real data source used by the frontend.

It is currently dead/unnecessary code.

Future action:

- Remove it if confirmed unused, OR
- Wire it to the real county data source if there is a deliberate reason to retain it.

Do not maintain duplicate sources of truth.



# DATABASE ARCHITECTURE AND STORAGE

## DATABASE LOCATION — CURRENT MIGRATION

The GeoShield SQLite database was previously stored inside the Google Drive-synchronized project directory:

`N:\My Drive\GeoShield_Project\database\geoshield.db`

Performance investigation showed that the county endpoint could take approximately:

`1.8–4.2 seconds`

on initial measurements.

The county service was subsequently optimized from six separate SQLite connections/queries to a single connection and combined query.

Repeated measurements improved to approximately:

`2.8s -> 1.0s -> 0.4s`

However, the database remained on the Google Drive-synchronized filesystem.

The remaining filesystem/synchronization overhead therefore became the target of the next optimization.

## SELECTED SOLUTION

Use a local, non-cloud-synchronized data directory.

The project will use the centralized configuration value:

`settings.data_dir`

from:

`core/config.py`

The configured environment variable is:

`GEOSHIELD_DATA_DIR`

Default behavior on Windows:

`%LOCALAPPDATA%\GeoShield`

Fallback:

`C:/GeoShield_data/GeoShield`

This keeps SQLite and other local runtime data outside the Google Drive-synchronized project tree.

## CENTRAL CONFIGURATION

`core/config.py` now contains:

`data_dir`

configured through:

`GEOSHIELD_DATA_DIR`

This creates a single source of truth for the local GeoShield data directory instead of independently hardcoding the database path in multiple services.

## DATABASE PATH MIGRATION

The following files were identified as direct database-path consumers:

1. `backend/routes/resources.py`
2. `backend/analytics/analytics_engine.py`
3. `core/engines/main_engine.py`
4. `dashboard/services/county_service.py`

Current references found during the audit include:

`database/geoshield.db`

and:

`PROJECT_ROOT / "database" / "geoshield.db"`

## REQUIRED MIGRATION

The four consumers should be updated to construct their database path from the centralized configuration.

Target architecture:

`settings.data_dir`
-> `geoshield.db`

rather than:

`PROJECT_ROOT / database / geoshield.db`

The existing database file must then be moved to the new local data directory.

## IMPORTANT

The database relocation is an infrastructure change.

Do not delete the original database until:

1. The new directory exists.
2. The database has been copied/moved successfully.
3. All four consumers point to the new location.
4. The application starts successfully.
5. Database-dependent endpoints work.
6. County endpoint latency is re-measured.
7. The new database contains the expected existing data.

Keep a backup of the original database during migration.

## PERFORMANCE VERIFICATION

After migration, measure at minimum:

`/county/Marsabit`

and:

`/county/Nairobi`

Compare the results against the previous measurements.

The purpose is to determine whether Google Drive synchronization was materially contributing to SQLite request latency.

Do not mark the migration as performance-verified until these measurements have been completed.

---

## ALERT CONFIGURATION DISCOVERY

During the database/configuration audit, `core/config.py` was inspected.

The centralized configuration already contains scaffolding for:

- Africa's Talking SMS settings
- Alert recipient configuration

These settings are currently relevant to the future Alerts Engine implementation.

This means the Alerts Engine should reuse the existing centralized configuration rather than introducing a second independent configuration system.

The existence of configuration scaffolding does NOT by itself mean SMS alert delivery is fully operational.

Actual alert generation, anomaly detection, provider integration and end-to-end notification delivery must still be verified separately.


# LATEST SESSION UPDATE — 20 SEPTEMBER 2026
## OVERALL RISK, PERFORMANCE OVERHAUL & ALERTS ENGINE

## 1. VERIFIED BASELINE BEFORE THIS SESSION

The following components were already implemented and live:

- Flood Engine: rainfall + terrain/slope + catchment/drainage factors.
- Agriculture, Drought, Fire, and Earthquake engines: live satellite/weather data.
- Analytics Engine: aggregates Agriculture, Fire, Flood, and Drought severity into `overall_risk`.
- Earthquake is deliberately excluded from the Overall Risk aggregation.
- Overall Risk backend logic: complete and verified.

## 2. OVERALL RISK — COMPLETE END-TO-END

The Overall Risk feature is now closed end-to-end.

Completed:
- Fixed frontend wiring in `dashboard.js` and `counties.js`.
- Live Overall Risk percentage now displays with severity-based coloring.
- Fixed a 60-second timer that silently reset the card to `--` after a correct county selection.
- Fixed severity rounding: exact 50% splits were incorrectly labeled Low because of banker's rounding. The logic now uses round-half-up, correctly classifying 50% as Moderate.

Status: Backend and frontend behavior verified.

## 3. INFRASTRUCTURE BUGS — FIXED

### index.html encoding crash
- Two stray non-UTF-8 bytes in `index.html` were crashing page loads.
- Fixed precisely at the byte level.

### UI emoji corruption
- Most UI emoji had previously been replaced with literal `?` characters by a script that saved the file without explicitly using UTF-8.
- The original emoji could not be recovered from the damaged file itself.
- Correct emoji were restored from an older session backup and reinjected while preserving newer changes.

Both issues are recorded as fixed.

## 4. MAJOR PERFORMANCE OVERHAUL — VERIFIED

Root cause of slow county selection:
- Every hazard engine re-fetched all 47 counties on each request.
- The Analytics database was stored on a Google Drive-synced path.

Completed:
- Added a 5-minute cache to all four hazard engines.
- Executed the planned Analytics database relocation.
- Identified and addressed a fifth database consumer missed in the earlier relocation plan.
- Added a proactive background thread to keep the cache warm, avoiding cold-start work on user clicks.

Verified performance:
- Cold request: approximately 146 seconds.
- Warm request: approximately 2.09 seconds.
- User confirmed county selection now feels instant in practice.

Remaining performance note:
- Approximately 2 seconds of dashboard latency may be caused by repeated SQLite writes through `submit_engine_output`, including on cache hits.
- This is flagged as low priority because current performance is acceptable.

## 5. ALERTS ENGINE — INVENTORY AND PARTIAL IMPLEMENTATION

Existing components identified:
- Event bus.
- SMS notifier.
- Alert standardizer.

The actual alert orchestrator in `alert_engine.py` was confirmed to be empty and is not yet implemented.

Completed this session:
- Registered Drought and Flood with the alert system.
- Fire, Earthquake, and Agriculture were already registered.

## 6. ALERTS ENGINE — OPEN WORK

### Immediate next task: build the alert orchestrator

Implement a background loop that:
1. Reads cached hazard data for 47 counties across four hazards: Agriculture, Fire, Flood, and Drought.
2. Reuses the existing cache rather than triggering fresh live fetches.
3. Compares current severity with the last-seen severity for each county/hazard.
4. Generates alerts only for new or worsening severity.
5. Publishes qualifying events through the existing event bus and alert standardizer.

### Required safeguards and integration
- Add deduplication/state tracking to prevent repeated alerts for unchanged severity.
- Wire the orchestrator into the background-thread pattern in `main.py`.
- Expose alert data through a real `/api/alerts` route.
- Run and observe the orchestrator in dry-run mode before enabling real SMS sends.
- Keep live SMS delivery disabled until dry-run behavior is verified.

Spam prevention is designed conceptually but not yet built.

## 7. OTHER UNVERIFIED OR OPEN ITEMS

- NDVI concurrency fix from an earlier session was reported as written but has not been tested under real concurrent load.
- Repeated SQLite writes on cache hits may account for residual dashboard latency; low priority.
- Do not mark either item fully resolved without verification.

## 8. RECOMMENDED NEXT SESSION WORKFLOW

Priority 1 — Alerts Engine orchestrator:
- Inspect the current `alert_engine.py`, event bus, alert standardizer, notifier interfaces, and `main.py` background-thread pattern.
- Implement cached-data polling across 47 counties and the four registered hazards.
- Add per-county/per-hazard severity deduplication so only new or worsening conditions publish alerts.
- Add the `/api/alerts` endpoint.
- Start in dry-run mode and verify events, deduplication, and safe startup/shutdown behavior.
- Enable real SMS only after dry-run results are reviewed.

Priority 2 — Verify NDVI concurrency behavior under actual concurrent requests.

Priority 3 — Revisit SQLite write frequency only if dashboard latency becomes a practical issue.

## 9. CURRENT PROJECT HANDOFF

Overall Risk is complete and verified end-to-end. The frontend display, severity coloring, timer reset bug, and 50% rounding issue have been addressed.

The encoding crash and UI emoji corruption have been repaired.

The four hazard engines now use a 5-minute cache, with proactive cache warming. County selection has improved from approximately 146 seconds cold to approximately 2.09 seconds warm, and the user reports that it feels instant.

The Alerts Engine has existing infrastructure and registrations for Agriculture, Fire, Earthquake, Drought, and Flood. However, the orchestrator, severity-based spam prevention, background integration, and `/api/alerts` route remain open.

The immediate next task is to build and verify the alert orchestrator in dry-run mode before enabling real SMS delivery.


# LATEST SESSION UPDATE — 20 SEPTEMBER 2026
## ALERTS ORCHESTRATOR, FIRE HOTSPOT FIX & NEXT STEPS

## 1. ALERTS ENGINE ORCHESTRATOR — BUILT AND VERIFIED

Implemented `engines/alerts/alert_engine.py` as a background orchestrator.

### Implementation
- Runs as a background thread, started during FastAPI startup alongside NDVI warmup, Analytics snapshot, and hazard-cache warmup threads.
- Polls every 60 seconds.
- Reads each hazard engine's cached `.analyse()` output without forcing fresh live fetches.
- Processes county-level severity across the registered hazard engines.
- Tracks last-seen severity in an in-memory dictionary.
- Generates alerts only when severity is new or worsens.
- SMS dispatch remains in `dry_run` mode.

### Live verification
- Cold-start cycle generated 141 alerts. This was expected because no previous severity state existed.
- The second cycle generated exactly 16 alerts, all representing genuine escalations.
- Example: Baringo Agriculture escalated from Moderate to High.
- Deduplication was confirmed working.
- SMS dispatch remained in dry-run mode throughout verification.

Added `print()` statements alongside `logger.info()` because the existing logging configuration did not display the orchestrator's activity in the console.

## 2. ALERTS API — REPLACED AND REGISTERED

Replaced `backend/routes/alerts.py`.

Previously:
- The file referenced nonexistent `backend.services.ai_center` and `fire_monitor` modules.
- The router was not included in `main.py`.
- The active `/alerts` route was a hardcoded stub.

Now:
- `GET /api/alerts` is backed by `main_engine.get_alert_history()`.
- The alerts router is included in `main.py`.
- The old hardcoded `/alerts` stub was removed.
- `main.py` starts the orchestrator during application startup.
- An automatic backup was created at `backend/main.py.bak_alerts`.

The new API and orchestrator are implemented. Continue validating the route and frontend integration during the next session.

## 3. ALERT EVENT HANDLING — IMPLEMENTATION DETAIL

The existing `event_bus.publish()` method only appends to an in-memory list; it does not provide subscriber-based pub/sub behavior.

The orchestrator therefore writes directly to `risk_alert_engine.alert_history`, the same list read by `get_alert_history()`.

Do not assume that publishing to the event bus automatically dispatches alerts to subscribers or external services.

## 4. FIRE HOTSPOT MAP — FETCH URL FIX APPLIED

A frontend issue was identified when `fire.js` was incorrectly pointed to `/api/alerts`.

The Fire module's "alerts" are VIIRS hotspot map markers, not the county/hazard alert orchestrator's alert records.

Applied the correction in `frontend/static/fire.js`:
- Fetch URL changed to `/api/fire/events`.
- Added an `Array.isArray(data)` guard.
- Changed iteration from `data.alerts.forEach(...)` to `data.forEach(...)`.

The corrected file was printed and inspected after the PowerShell replacement. The fetch URL, array guard, and iteration changes were present.

The correct backend endpoint is `/api/fire/events`, implemented in `backend/api/fire_api.py`.

### Remaining Fire UI check
- Verify hotspot markers render correctly against the live endpoint.
- Inspect the timestamp field used in the popup. `alert.time` may be undefined because raw VIIRS records commonly use acquisition date/time fields. Confirm the actual payload before changing the popup.
- The hotspot-fetch correction is applied, but full browser-level marker and popup verification remains open.

## 5. ALERTS ENGINE — REMAINING WORK

### Priority 1: Complete Fire frontend verification
- Confirm `/api/fire/events` returns the expected array.
- Verify markers render.
- Check the popup timestamp field against the actual payload.

### Priority 2: Wire the Alerts sidebar navigation
- Add `id="navAlerts"` to the Alerts sidebar link in `index.html`.
- Inspect the existing navigation handler used by `navLiveMap`, `navAnalytics`, and `navDrought`.
- Add a matching Alerts view that calls `GET /api/alerts` and renders the alert list.

### Priority 3: Check dashboard alert data
- Inspect `dashboard.js` around `data.alerts ?? "--"`.
- Confirm the source and schema of `data`.
- Do not substitute the array returned by `/api/alerts` into a dashboard field expecting a different value or format.

### Priority 4: Decide alert-state persistence
- `_last_seen` currently exists only in memory.
- A server restart resets the severity history and may cause a new-alert burst for every county/hazard.
- Decide whether this behavior is acceptable or whether last-seen severity must be persisted to SQLite.

### Priority 5: Enable real SMS only after validation
- Keep SMS in dry-run mode until the route, deduplication, persistence decision, and multiple dry-run cycles have been reviewed.
- Real SMS requires `GEOSHIELD_NOTIFICATIONS_ENABLED=true` and valid Africa's Talking credentials in `.env`.
- Do not enable real SMS before the safeguards are verified.

## 6. OTHER OPEN OR CARRIED-OVER ISSUES

- Elevation connector concurrency contention was observed during cold-start bursts ("Another request is already fetching elevation data"). It self-recovered.
- GPM intermittently logged "Zonal statistics failed: Read failed" errors. These self-recovered.
- NDVI concurrency fix from an earlier session remains unverified under real concurrent load.
- `dashboard.py` contains a hardcoded `"bottom"` dead object; still open.
- ERA5 daily-quota fix has a known root cause, but the fix has not been written.

These are secondary to completing the Alerts UI and validating dry-run behavior.

## 7. REPORTS ENGINE — NOT STARTED

The Reports Engine remains the next major subsystem after the Alerts Engine.

Goal:
- Generate downloadable PDF disaster and intelligence reports.

No Reports Engine implementation was completed in this session.

## 8. CURRENT PROJECT HANDOFF

The Alerts Engine orchestrator is built and has been live-verified in dry-run mode. It polls cached hazard outputs every 60 seconds, tracks severity in memory, and generates alerts only for new or worsening conditions.

The second cycle generated 16 genuine escalations after the 141-alert cold-start cycle. Deduplication is confirmed working. SMS remains disabled in dry-run mode.

`GET /api/alerts` is now backed by Main Engine alert history, the router is included in `main.py`, and the orchestrator starts with the FastAPI background-thread pattern.

The Fire hotspot frontend fetch correction is applied: `fire.js` now requests `/api/fire/events` and handles an array response. Browser-level marker and popup verification, including the timestamp field, remains open.

Immediate next work:
1. Verify the Fire hotspot map fix and timestamp field.
2. Wire the Alerts sidebar view to `GET /api/alerts`.
3. Inspect the dashboard's existing `data.alerts` field.
4. Decide whether alert severity state should persist across restarts.
5. Observe more dry-run cycles before enabling real SMS.
6. Begin the Reports Engine after Alerts integration is settled.


# LATEST PROJECT CONTEXT UPDATE — 20 SEPTEMBER 2026
## ALERTS ENGINE LIFECYCLE, ACTIVE/HISTORICAL VIEWS & IMPLEMENTATION HANDOFF

## 1. PURPOSE OF THIS UPDATE

This update consolidates the established GeoShield architecture, completed work, verified behavior, current Alerts Engine design, implementation scripts supplied, and remaining verification tasks.

Important status distinction:
The existing orchestrator and basic alerts API were previously implemented and live-verified. The Active/Historical alert lifecycle expansion and UI scripts described in the latest session material must not be marked completed unless execution and verification are confirmed.

## 2. ESTABLISHED GEOSHIELD ARCHITECTURE AND DEVELOPMENT METHOD

GeoShield AI Enterprise integrates live satellite, weather, GIS, and hazard-engine outputs through the Main Engine and Analytics Engine to support risk analysis, alerts, reporting, and decision support.

Established development approach:
- Inspect the real interfaces and data shapes before writing integration code.
- Do not guess at backend methods, frontend markup, API response schemas, or CSS classes.
- Use the existing project architecture and cache where possible.
- Make targeted changes and preserve unrelated working functionality.
- Verify changes using PowerShell, compile/syntax checks where applicable, live API responses, server logs, and browser behavior.
- Clearly distinguish implemented, verified, drafted, and pending work.
- GeoShield development instructions remain VS Code Terminal / PowerShell only. No Cursor, Copilot, or VS AI unless explicitly requested.

## 3. PREVIOUSLY COMPLETED AND VERIFIED PLATFORM WORK

### Overall Risk
- Overall Risk backend logic is complete and verified.
- Analytics aggregates Agriculture, Fire, Flood, and Drought severity into `overall_risk`.
- Earthquake is deliberately excluded from Overall Risk aggregation.
- Frontend wiring in `dashboard.js` and `counties.js` was fixed.
- Live percentage and severity coloring display correctly.
- Fixed the 60-second timer that reset the card to `--`.
- Fixed exact 50% severity rounding using round-half-up rather than banker's rounding.

### Performance
- Four hazard engines use a 5-minute cache.
- Analytics database relocation from the Google Drive-synced path was completed, including a fifth DB consumer missed in the earlier plan.
- A proactive background thread warms the hazard cache.
- Measured county-selection performance improved from approximately 146 seconds cold to 2.09 seconds warm.
- User confirmed county selection feels instant in practice.
- Repeated SQLite writes through `submit_engine_output` may contribute to residual latency; low priority.

### Infrastructure and UI encoding
- Two stray non-UTF-8 bytes in `index.html` that crashed page loads were fixed at the byte level.
- UI emoji corruption was restored from a previous session backup without discarding newer changes.

### Flood Engine
- Rainfall + terrain/slope + HydroRIVERS catchment/drainage factors are implemented and previously reported live and verified.
- GloFAS live discharge was unreliable for Kenya; HydroRIVERS static attributes were selected as structural factors, not live discharge.

### Other hazard engines
- Agriculture, Drought, Fire, and Earthquake have been reported live with real satellite/weather data.
- Agriculture is not the current priority unless explicitly requested.

## 4. ALERTS ENGINE — EXISTING IMPLEMENTATION VERIFIED IN PRIOR SESSION

The initial orchestrator was implemented in `engines/alerts/alert_engine.py`.

Previously verified behavior:
- Runs as a background thread started during FastAPI startup.
- Polls every 60 seconds.
- Reads hazard engines' cached `.analyse()` outputs without forcing fresh live fetches.
- Tracks per-county/per-hazard severity in an in-memory `_last_seen` dictionary.
- Generates alerts only for new or worsening severity.
- Fire hotspot events are reduced to the worst severity per county for orchestration.
- Drought and Flood were registered with the alert system; Agriculture, Fire, and Earthquake had already been registered.
- Alert records are appended to `risk_alert_engine.alert_history`.
- SMS dispatch remains in `dry_run` mode.

Live verification from the earlier implementation:
- Cold-start cycle raised 141 alerts because no previous severity state existed.
- Second cycle raised 16 alerts, all genuine escalations.
- Example: Baringo Agriculture escalated from Moderate to High.
- Deduplication was confirmed working.
- Console `print()` statements were added alongside logger calls so orchestrator activity is visible.

The existing event bus `publish()` is an in-memory list append, not subscriber-based pub/sub. The orchestrator writes directly to `risk_alert_engine.alert_history`, which is read by `main_engine.get_alert_history()`.

## 5. BASIC ALERTS API — PREVIOUSLY IMPLEMENTED

`backend/routes/alerts.py` was replaced because its earlier version referenced nonexistent services and was not registered in `main.py`.

Previously implemented:
- `GET /api/alerts` backed by `main_engine.get_alert_history()`.
- Alerts router included in `main.py`.
- Old hardcoded `/alerts` stub removed.
- Orchestrator startup hook added to `main.py`.
- Backup created at `backend/main.py.bak_alerts`.

The basic history endpoint was implemented previously. The newer filtered response shape and Active/Historical routes described below are part of the proposed lifecycle expansion and require verification.

## 6. NEW ALERT LIFECYCLE DESIGN — ACTIVE VS HISTORICAL

The latest implementation plan expands alerts into two distinct views.

### Active Alerts
A live collection of currently elevated county/hazard pairs:
- Only Moderate, High, or Extreme severity is considered an active alert.
- Active entries are updated when severity worsens.
- When severity returns to Low, the active entry is removed and a recovery record is appended to history.
- For Fire, a county disappearing from the current hotspot feed is treated by the proposed logic as a recovery.
- Active state is held in `_active_alerts`, keyed by `(hazard, county)`.

### Historical Alerts
A log of raised alerts and recovery entries:
- Includes severity changes and recovery records.
- Recovery entries use `resolved: true`, a Low severity, previous severity, and a recovery reason.
- History can be cleared independently of active state.
- Clearing history must not clear currently active alerts.

### Notification thresholds in the proposed implementation
- Moderate: record/display only; no SMS attempt.
- High and Extreme: attempt notification dispatch.
- Recovery records: no notification.
- `DRY_RUN` remains `True`.
- Actual delivery also requires `GEOSHIELD_NOTIFICATIONS_ENABLED=true` and valid Africa's Talking credentials in `.env`.

This lifecycle expansion is described in the supplied rewrite script. Do not assume recovery behavior, active-state correctness, or the new API routes are verified until the code has been applied and tested.

## 7. PROPOSED ALERT API EXPANSION — PENDING VERIFICATION

The supplied replacement for `backend/routes/alerts.py` defines:

- `GET /api/alerts`
  - Historical alert log.
  - Optional `limit`, `county`, and `hazard` filters.
  - Response intended to contain `count` and `alerts`.

- `GET /api/alerts/active`
  - Currently active Moderate+ alerts.
  - Response intended to contain `count` and `alerts`.

- `POST /api/alerts/clear-history`
  - Clears historical entries only.
  - Active alert state must remain untouched.

These are proposed by the supplied script. Confirm the script ran, inspect the resulting file, and test each route before marking them complete.

## 8. ALERTS FRONTEND — INSPECTED STRUCTURE AND PROPOSED UI

### Existing Analytics modal markup
The actual modal structure was inspected in `frontend/templates/index.html`:
- `analyticsModalBackdrop`
- `analyticsModalTitle`
- `analyticsModalBody`
- `analyticsModalCloseBtn`

The modal uses:
- `analytics-modal-backdrop`
- `analytics-modal`
- `analytics-modal-header`
- `analytics-modal-body`

A CSS search in separate stylesheet files returned no matches for `.analytics-modal` or `.analytics-card`. The styles were then found inline in `index.html`.

### Proposed Alerts interface
Replace the single scrolling Alerts list with a two-card grid:
- Active Alerts
- Historical Alerts

Clicking either card opens a modal styled to match Analytics. The modal displays dated alert rows, county, hazard, severity, reason, and status.

Historical modal includes a "Clear All Historical Alerts" button with a confirmation step. Active Alerts must remain untouched when history is cleared.

The supplied frontend rewrite uses `frontend/static/alerts.js` and proposes:
- Fetching `/api/alerts/active`.
- Fetching `/api/alerts?limit=500`.
- Rendering card summaries and modal tables.
- Showing a clear-history control only in the Historical modal.
- Refreshing data when the Alerts page is initialized or becomes visible.

The supplied UI patch script expects a specific existing Alerts page body and inserts a new modal after the Agriculture Engine script anchor. It checks for exactly one matching block and reports `[FAIL]` if the expected markup differs.

### Verification status
The latest material contains the implementation scripts, but does not confirm that all scripts were executed successfully or that the updated Alerts page works in the browser.

Before considering the UI complete:
- Confirm the Alerts page body was replaced exactly once.
- Confirm the modal markup was inserted exactly once.
- Confirm `alerts.js` is loaded by the page.
- Confirm the navigation handler opens the Alerts page.
- Confirm both API requests succeed and return the expected schema.
- Confirm modal opening/closing, severity styling, long-list scrolling, and history clearing work.

## 9. ALERT ENGINE DESIGN RISKS TO VERIFY

The proposed lifecycle code introduces behavior that must be tested carefully:

- `_last_seen` and `_active_alerts` are in-memory only. A server restart resets them and can cause a new-alert burst; persistence remains undecided.
- Missing records are treated as recovery. This is particularly consequential for Fire, where a missing hotspot record may reflect feed coverage or reporting behavior rather than confirmed fire resolution.
- `_get_hazard_records()` returns an empty dictionary on engine exceptions. The proposed missing-record recovery path must not mistakenly resolve every active alert when an engine fetch/analysis fails.
- Validate that severity decreases from Extreme/High to Moderate updates the active record appropriately, rather than leaving stale severity.
- Validate thread safety between polling, active-alert reads, and history clearing.
- Confirm notification dispatch remains dry-run during all testing.
- Do not label High/Extreme entries "SMS notified" in the UI unless the actual dispatch result confirms delivery. Dry-run or skipped notification must be represented accurately.

These are verification concerns, not claims that each defect is present.

## 10. FIRE HOTSPOT FRONTEND FIX — APPLIED, BROWSER VERIFICATION OPEN

A prior correction in `frontend/static/fire.js` changed the hotspot fetch to `/api/fire/events`, added an array-response guard, and changed iteration to `data.forEach(...)`.

This is separate from the county/hazard alert orchestrator. Fire "alerts" in this context are VIIRS hotspot map markers, with fields such as FRP, brightness, latitude, and longitude.

The corrected source was printed and inspected after the PowerShell replacement. Full browser verification remains open.

Also inspect the popup timestamp field: `alert.time` may be undefined if the raw VIIRS record instead contains acquisition date/time fields. Confirm the actual payload before changing it.

## 11. IMMEDIATE NEXT TASKS — ALERTS

1. Inspect the current versions of `alert_engine.py`, `backend/routes/alerts.py`, `main.py`, `index.html`, and `alerts.js` to establish which proposed scripts actually ran.
2. Verify the Active/Historical API routes and response schemas.
3. Verify recovery behavior and ensure engine failures do not cause false recoveries.
4. Verify the Alerts sidebar navigation and card/modal interface.
5. Confirm Clear Historical Alerts does not modify active state.
6. Observe multiple dry-run cycles and verify escalation, deduplication, recovery, and restart behavior.
7. Decide whether severity state must persist across restarts.
8. Keep real SMS disabled until the route, lifecycle, deduplication, and dry-run behavior are settled.

## 12. REMAINING CARRIED-OVER ISSUES

- NDVI concurrency fix remains unverified under real concurrent load.
- `dashboard.py` hardcoded `"bottom"` dead object remains open.
- ERA5 daily-quota fix has a known root cause, but the fix has not been written.
- Elevation connector concurrency contention was observed during cold-start bursts; it self-recovered.
- GPM "Zonal statistics failed: Read failed" errors were intermittent and self-recovered.
- Residual dashboard latency from repeated SQLite writes is low priority while current performance remains acceptable.

## 13. REPORTS ENGINE — NEXT MAJOR SUBSYSTEM

The Reports Engine remains the next major subsystem after Alerts integration is settled.

Goal:
- Generate downloadable PDF disaster and intelligence reports.

No Reports Engine implementation was completed in the latest Alerts work.

## 14. CURRENT PROJECT HANDOFF

GeoShield's Overall Risk backend and frontend are complete and verified. Hazard caching and background warming substantially improved county-selection performance.

The initial Alerts orchestrator and basic history API were previously implemented and verified in dry-run mode. The latest work proposes a fuller alert lifecycle with separate Active and Historical views, recovery records, a clear-history endpoint, and a two-card/modal Alerts UI.

The latest supplied scripts must be checked against the actual project files before claiming the lifecycle expansion is complete. The immediate next step is to inspect current file contents, determine which scripts ran, and verify the API and browser behavior without enabling real SMS.

Once Alerts is stable, proceed to the Reports Engine for downloadable PDF intelligence and disaster reports.


---

# LATEST SESSION UPDATE — 20 SEPTEMBER 2026
## ALERTS ENGINE — COMPLETE AND VERIFIED

### Confirmed End-to-End Status

The GeoShield Alerts Engine is implemented and verified in-browser.

- `engines/alerts/alert_engine.py` polls cached hazard data every 60 seconds.
- Severity is tracked per `(hazard, county)` pair.
- Alerts are raised only for new or worsening severity.
- `_active_alerts` tracks currently elevated hazard/county pairs.
- Recovery events are logged automatically.
- Fire feed disappearance is treated as recovery, with defensive checks to prevent false mass-recoveries when an engine fails.

### Backend — Verified Live

The following routes are registered and responding:

- `GET /api/alerts`
- `GET /api/alerts/active`
- `POST /api/alerts/clear-history`

### Frontend — Verified Live in Browser

- Sidebar navigation opens the Alerts workspace.
- `alerts.js` fetches active and historical alert data.
- Summary cards populate correctly.
- Modals open with the correct data.
- Clear History affects historical records only; active alerts remain untouched.
- Both API calls returned HTTP 200.
- No browser console errors were observed during verification.

### SMS Delivery — Deliberately Paused

The dispatch logic requires all three conditions:

1. `DRY_RUN=False` in code.
2. `GEOSHIELD_NOTIFICATIONS_ENABLED=true` in `.env`.
3. A configured recipient.

The current Africa's Talking account is a Sandbox app. Sandbox delivery is limited to the simulator and does not deliver SMS to real phones.

Real SMS delivery requires a production Team/App with production credentials, shortcode approval (with carrier review time), and paid SMS credit.

**Safety state:**
- `DRY_RUN=True` has been restored.
- `.env` still contains sandbox credentials.
- `GEOSHIELD_NOTIFICATIONS_ENABLED=true` remains set.
- No live SMS delivery should be attempted while `DRY_RUN=True`.

To enable production SMS later: create the production Team/App, obtain and configure the shortcode, add credit, replace sandbox credentials in `.env`, and deliberately switch `DRY_RUN=False` after verification.

### Current Alerts Engine Classification

**IMPLEMENTED AND VERIFIED**
- Alert orchestration and severity escalation.
- Active vs. Historical lifecycle.
- Automatic recovery logging and defensive failure handling.
- Backend endpoints.
- Alerts workspace, summary cards, modals, and history-only clearing.
- In-browser API and UI verification.

**DEFERRED BY CHOICE**
- Production SMS delivery and Africa's Talking production onboarding.

### Handoff Decision

The Alerts Engine is in a stable, functional state, with real SMS safely disabled. No further Alerts implementation is required before moving to the next GeoShield subsystem. Preserve the current working implementation; do not rebuild or rewire it without a specific reason.


---

# LATEST PROJECT CONTEXT UPDATE — 20 SEPTEMBER 2026
## REPORTS ENGINE — NEW SUBSYSTEM / NOT YET IMPLEMENTED

### Starting Point

The Reports Engine is the next GeoShield AI Enterprise subsystem. At the time of this handoff, Reports functionality has not been implemented.

An existing sidebar placeholder was identified:

- `<a>📄 Reports</a>`

The link has no `id`, no pointer styling, and no workspace navigation or Reports functionality wired to it. It is the intended sidebar entry point to activate.

### Inspection and Development Approach

The Reports implementation was being scoped by inspecting the existing `frontend/static/workspace-nav.js` navigation patterns.

Targeted inspection was requested for:

- The remainder of `setWorkspace()`, including page visibility toggles and the `GeoShieldAlerts.init()` call.
- The `goToAlerts()` function and adjacent navigation functions/event bindings.
- The `if (showMap)` region, to understand the workspace activation and initialization pattern.

The inspection output was pasted, but the complete source context was not independently preserved in this report. Do not assume every required function body or insertion anchor has been fully verified.

### Proposed Reports Workspace

The planned Reports workspace package includes:

1. A `#geoshieldReportsPage` HTML section.
2. A PDF / Video report-type selector.
3. A Video sub-form adapted from the separate GeoShield Disaster Video Studio concept.
4. A new `frontend/static/reports.js` module.
5. Workspace navigation integration in `frontend/static/workspace-nav.js`.
6. A `REPORTS_PAGE` constant and Reports page visibility toggle.
7. A `goToReports()` function and sidebar event binding.
8. Close-button handling consistent with existing workspaces.
9. A script tag to load the Reports frontend module.
10. Updating the sidebar placeholder to a clickable `navReports` link.

These are **proposed implementation items, not confirmed completed features**.

### Patch Safety Decision

Because prior PowerShell quoting and encoding issues caused file corruption, the proposed implementation approach was to use a Python patch script named `apply_reports_page.py`.

The intended safeguards are:

- Read and write files with explicit UTF-8 encoding.
- Use exact, anchored string replacements.
- Fail loudly if an expected anchor is missing.
- Avoid blind edits to unseen JavaScript.
- Preserve existing application code unless a specific insertion or replacement is required.

A script was described as created/shared in the prior handoff, but its contents, successful execution, and resulting application changes have not been verified here. Do not assume the Reports workspace or its navigation is already implemented.

### Current Classification

**CONFIRMED**
- Reports Engine work is beginning from scratch.
- An unwired Reports sidebar placeholder exists.
- `workspace-nav.js` is the navigation integration point under inspection.
- A safe, UTF-8-aware, anchor-based patch strategy was selected.

**PLANNED / PENDING VERIFICATION**
- Reports HTML and workspace layout.
- PDF / Video selector and Video sub-form.
- `reports.js` functionality.
- Sidebar activation and workspace navigation.
- Close-button handling and script loading.
- Python patch execution and post-patch validation.
- PDF generation, report data integration, and end-to-end testing.

### Handoff Instructions

Treat Reports as the next active development task. Before applying changes, inspect the current files and confirm the exact source anchors. If the patch script exists, review it before running. After implementation, verify the modified files, server startup, workspace navigation, browser console, and actual report-generation behavior.

Do not mark the Reports Engine complete until its implemented functionality has been tested end-to-end.


---

# GEOSHIELD DISASTER VIDEO STUDIO — PROJECT CONTEXT & INTEGRATION ROADMAP
## Source: GeoShield_Disaster_Video_Studio_Overview.md
## Context Update: 20 September 2026

### 1. What GeoShield Disaster Video Studio Is

GeoShield Disaster Video Studio is a separate AI-powered disaster-briefing video generation system. It accepts a disaster type, location, timeframe, and target duration, then produces a narrated, broadcast-style disaster briefing video.

Its intended outputs are:
- A generated or user-written narration script.
- Professional neural voice narration.
- A mood-matched cinematic music bed.
- A rendered MP4 with branding, captions, and a title card.
- Watch and Download options, plus a Create New Video action.

The separate project folder is:
`N:\My Drive\GeoShield_Disaster_Video_Studio`

The Studio is designed to generate disaster briefings efficiently, with most durations reportedly rendering in under a minute. Its current visual layer is still a static branded background with text overlays.

### 2. Current Studio Pipeline

The Studio's existing pipeline is:

User Input
(disaster type, location, timeframe, duration)
        |
        v
Script Generation
        |
        v
Voice Synthesis
        |
        v
Music & Audio Synchronization
        |
        v
FFmpeg Video Rendering
        |
        v
Finished MP4 — Watch / Download

#### Script Generation
- Google Gemini (`gemini-3.6-flash`) generates documentary-style narration.
- A local phrase-bank fallback is used if Gemini remains unavailable after a retry.
- Open-Meteo weather data and ReliefWeb / UN OCHA situation reports provide external context.
- Users can submit their own script, bypassing AI script generation.
- Generated scripts target approximately 140 words per narration minute.

#### Voice Narration
- Microsoft Edge neural TTS (`edge-tts`) generates narration.
- Available profiles include `en-GB-RyanNeural` (male) and `en-GB-SoniaNeural` (female).
- If voice synthesis fails, the render can continue with music only.

#### Music and Synchronization
- Disaster categories map to mood-matched music pools.
- Royalty-free music tracks are used where available, with synthesized audio fallback.
- A 5-second cold-open title card precedes narration.
- FFmpeg sidechain compression automatically lowers music under narration.
- Final duration follows the actual synthesized narration length.

#### Video Rendering
- FFmpeg runs as a background subprocess with timeout handling.
- GeoShield AI branding and disaster/location captions are burned into the video.
- The finished MP4 is presented with Watch, Download, and Create New Video actions.

### 3. Relationship Between the Two Systems

GeoShield AI and GeoShield Disaster Video Studio are two complementary parts of the wider GeoShield ecosystem.

**GeoShield AI is the geospatial intelligence and hazard-analysis platform.**

It ingests and processes satellite imagery, weather data, GIS information, and other relevant sources. Its Main Engine coordinates data and specialized hazard engines to produce location-specific intelligence and risk outputs.

**GeoShield Disaster Video Studio is the disaster communication and briefing-generation system.**

It converts disaster-related inputs and contextual information into a narrated, scored video briefing.

The intended relationship is:

GeoShield AI detects and analyzes a hazard
        |
        v
Main Engine coordinates relevant intelligence
        |
        v
Studio receives event-specific data and imagery
        |
        v
Studio generates or adapts the narration
        |
        v
Narration is matched with relevant visuals
        |
        v
FFmpeg renders a grounded disaster briefing MP4
        |
        v
Video is available to watch, download, and share

The Studio should complement GeoShield AI, not replace its hazard engines, Main Engine, analytics, or alerting system.

### 4. How the Studio Will Connect to GeoShield AI

The intended integration is a direct, structured connection from the Studio to GeoShield AI's Main Engine.

The Studio will submit or pass the relevant disaster type, location, timeframe, and other event parameters. GeoShield AI's Main Engine will coordinate access to relevant intelligence, such as:

- Sentinel-2 satellite imagery through the Copernicus connection.
- Hazard-specific analysis from relevant engines, including Flood, Fire, Drought, Agriculture, and Earthquake.
- Weather and other relevant environmental data.
- Geographic context and relevant resource or infrastructure information.
- Risk analytics and other available event-specific outputs.

The Studio will then use the returned information to ground the narration and visual sequence in the selected event and location.

**Important:** The exact API contract, authentication method, response schema, image delivery mechanism, and error-handling behavior for this cross-project connection still need to be defined and implemented. Do not assume the Studio is already connected to the Main Engine merely because the two systems exist.

### 5. Visual Integration Roadmap

The uploaded Studio overview defines four stages:

#### Stage 1 — Connect to GeoShield AI Main Engine
Enable the Studio to request real satellite imagery and disaster-relevant data from GeoShield AI for a selected event and location.

#### Stage 2 — Scene-Level Timing and Matching
Use Edge TTS word-level timestamps, together with sentence, keyword, and location extraction, to identify what each narration segment describes and when it is spoken.

#### Stage 3 — Match Visuals to Each Scene
Match the narration segments with relevant Sentinel-2 imagery, resource or response-route overlays, and potentially interim Pixabay imagery. Display each visual at the appropriate narration time.

#### Stage 4 — Full System Convergence
GeoShield AI detects and analyzes a real event. The Studio automatically generates a fully grounded briefing with relevant imagery, location data, risk analytics, narration, and music—without requiring a user to manually describe the event first.

### 6. Current Capability vs. Planned Integration

**Studio capabilities documented as working:**
- Gemini script generation with local fallback.
- External weather and humanitarian context injection.
- User-written script support.
- Neural voice synthesis.
- Mood-matched music and synthesized fallback.
- Sidechain audio ducking and title-card opening.
- FFmpeg MP4 rendering with timeout handling.
- Watch, Download, and Create New Video actions.

**Known current limitation:**
The visual layer uses a static branded background with text overlays. Real satellite imagery, live GeoShield AI maps, and scene-matched hazard visuals are not yet integrated.

**Planned, not yet confirmed implemented:**
- Direct Main Engine integration.
- Scene-level narration timing and tagging.
- Automated imagery retrieval and scene matching.
- End-to-end automated video generation from a GeoShield AI-detected event.

### 7. How This Fits Into GeoShield AI Development

The Studio integration is a downstream intelligence-communication capability.

GeoShield AI's Main Engine and hazard analytics remain the source of geospatial intelligence. The Studio consumes relevant outputs and turns them into a visual briefing product.

The Reports Engine and Disaster Video Studio should be treated as related but distinct capabilities:
- Reports Engine: intended to produce structured disaster reports, including downloadable documents such as PDFs.
- Disaster Video Studio: produces narrated, scored MP4 disaster briefings.
- Both may eventually consume relevant GeoShield AI Main Engine outputs, but their implementation and output pipelines are separate.

Do not treat the Reports Engine as already integrated with the Studio, or assume the Studio's existing video-rendering pipeline automatically provides PDF report generation.

### 8. Development and Verification Rules

- Preserve the separation between the GeoShield AI platform and the Disaster Video Studio project unless a deliberate integration design requires otherwise.
- Inspect the actual source files before changing either project.
- Define and verify the Main Engine ↔ Studio API contract before implementing the connection.
- Keep existing working Studio audio and rendering behavior intact while adding real visuals.
- Verify that event data and imagery correspond to the selected hazard, location, and timeframe.
- Distinguish real GeoShield AI intelligence from fallback, mock, or externally sourced context.
- Do not mark visual integration complete until a real event can be processed into a correctly grounded, rendered MP4.

### 9. Handoff Summary

GeoShield Disaster Video Studio is an existing disaster-briefing video generator whose script, narration, music, and FFmpeg rendering pipeline is documented as working. Its current visual background is a placeholder.

GeoShield AI is intended to supply the real geospatial intelligence and imagery that will transform the Studio into a fully grounded disaster-briefing generator.

The integration roadmap is Main Engine connection → narration scene timing → visual matching → automated end-to-end briefing generation.

Treat this as the authoritative Studio overview and integration roadmap. Verify current project files and integration status before implementing or claiming completion.

---

---
# SESSION UPDATE — REPORTLAB INSTALLED
## 20 SEPTEMBER 2026 — REPORTS ENGINE DEPENDENCY

### Verified
- ReportLab version 5.0.1 successfully installed in the active `GeoShield_venv`.
- Installation succeeded using:
  `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org reportlab`
- Pillow 12.2.0 and `charset-normalizer` were already satisfied.
- Terminal returned to:
  `N:\My Drive\GeoShield_Project`

### Reports Engine Status
- ReportLab dependency installation blocker is resolved.
- This confirms the dependency installation only. It does NOT confirm that the Reports Engine patch has been applied, that its files exist, or that PDF generation works.
- The proposed `apply_reports_engine.py` patch remains unverified until its presence, contents, and project changes are inspected.

### Next Steps
1. Verify ReportLab imports and its installed version.
2. Inspect whether `apply_reports_engine.py` exists and whether any partial Reports Engine changes were made.
3. Review the patch and existing project files before applying changes.
4. Apply the Reports Engine patch only after confirming its anchors and current file state.
5. Test server startup, Reports workspace, alert listing, PDF generation, and PDF download.

### Safety
- Do not blindly rerun the patch if partial changes may exist.
- Keep existing verified Alerts functionality intact.
- SMS remains paused and must not be enabled as part of Reports Engine work.
---

---
# SESSION REPORT — GEOSHIELD REPORTS ENGINE
## 20 SEPTEMBER 2026 — IMPLEMENTATION & VERIFICATION

### 1. What We Built

#### Backend PDF Generation
- Created `backend\routes\reports.py`.
- Implemented `GET /api/reports/pdf?county=X`.
- Retrieves all four hazard summaries through `main_engine.get_hazard_summary()`.
- Retrieves `overall_risk` through `analytics_engine.get_county_analytics()`.
- Uses the same engine calls as `dashboard.py`.
- Generates a ReportLab PDF containing a severity-colored table.
- Returns the PDF using `StreamingResponse`.
- Registered the reports router in `main.py` alongside the existing `alerts_router`.

#### Gemini API Key Setup
- Created a separate Google AI Studio API key for GeoShield Reports.
- The key is independent of the Disaster Video Studio key.
- Added `GEOSHIELD_REPORTS_GEMINI_API_KEY` to `.env`.
- Added `settings.reports_gemini_api_key` to `core/config.py`.
- Live-tested successfully: the key loads and works with the tested endpoint, without the OpenSSL hang encountered elsewhere.

#### Frontend Wiring
- Replaced the `#reportsPdfCard` placeholder in `index.html` with a functional clickable card.
- Added `#reportsModalBackdrop`, structured similarly to the existing Alerts/Analytics modals.
- Rewrote `frontend\static\reports.js` for modal-based report generation.
- Added a county dropdown populated from `kenya_counties.geojson`.
- Connected the selected county to the PDF download flow.

#### Download Bug Investigation
- Initial fetch/blob downloads appeared corrupted or disappeared in Opera.
- Direct `curl.exe` requests, bypassing the browser, confirmed that server-side PDF generation was correct.
- Root cause was Opera's own "open after download" setting reprocessing downloaded files.
- The frontend download was also improved to use a plain `<a href>` direct-link download, avoiding blob-related race conditions.

### 2. Files Inspected
Read-only inspection was performed on:
- `dashboard.py`
- `main.py`
- `index.html`
- `workspace-nav.js`
- `alerts.js`
- `kenya_counties.geojson`
- `counties.js`
- `core/config.py`

### 3. Files Created
- `backend\routes\reports.py`

### 4. Files Edited
- `main.py` — reports router import and registration.
- `index.html` — Reports card update and modal insertion.
- `frontend\static\reports.js` — rewritten from stub to working modal/download implementation.
- `core\config.py` — added Reports Gemini API setting.
- `.env` — added `GEOSHIELD_REPORTS_GEMINI_API_KEY`.

### 5. Verified Current State
The Reports Engine workflow has been live-verified:
- Reports card opens the modal.
- County dropdown populates.
- PDF download works.
- Multiple real counties tested, with genuinely varied data.
- Direct `curl.exe` tests confirmed server-generated PDFs were valid.

### 6. Remaining Work — Gemini Narrative Generation
The PDF currently contains a title and a small data table. The next major task is to implement Gemini-powered narrative generation.

Planned work:
1. Pass the retrieved county hazard data and overall risk into a Gemini narrative-generation function.
2. Generate an executive summary.
3. Generate a per-hazard explanation.
4. Insert the narrative into the PDF before the severity table.
5. Implement a local fallback narrative template if Gemini fails or is unavailable.
6. Test the narrative against multiple counties and verify that it accurately reflects the retrieved data.

### 7. Next Session Starting Point
Continue with the Gemini narrative-generation function for the Reports Engine. Inspect the current `backend\routes\reports.py` and configuration before editing. Preserve the working county dropdown, modal, PDF endpoint, direct-link download, and existing Alerts functionality.

Do not claim narrative generation is implemented until it has been added and tested.

---

---

# GEOSHIELD AI ENTERPRISE V2 — MASTER DEVELOPMENT ROADMAP

**Status:** Planned development roadmap. This section records intended work, not proof of implementation.

## 1. V2 Vision

GeoShield AI Enterprise V2 is the planned evolution of GeoShield into a Kenya-wide, multi-hazard geospatial intelligence, agricultural monitoring, food-security, and emergency-response decision-support platform.

The platform will build on the existing satellite integrations, Main Engine, hazard engines, Live Map, dashboard, and Reports Engine. Existing architecture and verified functionality must be preserved unless an evidence-based change is required.

## 2. Development Rules

- Use VS Code Terminal / PowerShell only for GeoShield development.
- No Cursor, GitHub Copilot, or VS AI unless the user explicitly changes this constraint.
- Never patch on a guess. Trace the code path, inspect actual errors and API responses, and verify the fix.
- Preserve working architecture and existing functionality.
- Separate verified capabilities, confirmed root causes, pending investigations, and planned features.
- Do not present estimates as confirmed observations or unavailable data as live.
- Validate syntax and test actual application behavior after changes.
- Keep secrets, credentials, .env files, and sensitive operational data out of Git.
- Update this context file as verified milestones and decisions are completed.
- Do not mark a V2 feature complete until it has been implemented and tested.

## 3. Initial V2 Priorities

### 3.1 Achievements Documentation
Create ACHIEVEMENTS.md in the project root. Document verified milestones, integrations, engines, and completed fixes. Commit and push it to the GeoShield GitHub repository.

### 3.2 Restore Earthquake UI Card
Trace the existing earthquake backend/API and restore its frontend card. Reuse the existing backend data and avoid duplicating hazard logic in the UI.

### 3.3 Disaster Video Studio Integration and Reliability
Connect GeoShield Disaster Video Intelligence Studio to GeoShield AI through defined interfaces/APIs. Audit its local fallbacks, identify actual causes, correct provider configuration and error handling, and retain local fallback as a controlled recovery mechanism.

### 3.4 Satellite Reliability and Multi-Source Data
Audit satellite fallbacks and provider failures. Add provider health checks, data freshness validation, provenance, and controlled failover. Assess additional satellite and live-data sources. Do not assume that adding providers automatically guarantees uninterrupted coverage.

## 4. Satellite Change Detection and Imagery Intelligence

### 4.1 Sentinel-2 Change Detection
Develop an observation-driven engine that compares new usable Sentinel-2 imagery with appropriate historical or pre-event imagery.

Planned workflow:
1. Retrieve new imagery for an area of interest.
2. Select a suitable baseline image.
3. Validate cloud cover, quality, acquisition dates, and spatial alignment.
4. Apply cloud masking and preprocessing.
5. Calculate relevant spectral indices and change metrics.
6. Detect and filter meaningful changes and false positives.
7. Produce change maps, area statistics, timestamps, and explanations.
8. Make results available to the Live Map, Alerts Engine, Reports Engine, Analytics Engine, and GeoShield AI.

Target use cases include flood extent changes, wildfire burn scars, vegetation loss/recovery, drought stress, agricultural change, and visible infrastructure/land-cover change where resolution permits.

A Sentinel-2 revisit does not guarantee a usable cloud-free observation. Change detection must distinguish actual change from cloud, shadow, seasonal variation, sensor effects, and other false positives.

### 4.2 Landsat + Sentinel-2 Comparison and Harmonization
Test whether compatible Landsat and Sentinel-2 observations can improve GeoShield's imagery coverage and analysis.

Planned work:
- Retrieve spatially and temporally compatible scenes.
- Validate source metadata, quality, cloud cover, and acquisition times.
- Harmonize compatible bands, reflectance, projections, and grids.
- Compare observations and quantify sensor differences.
- Test NASA HLS or an equivalent validated harmonization workflow.
- Produce source-attributed GeoShield composite/harmonized layers where scientifically appropriate.

Do not assume arbitrary tile blending produces sharper or more accurate imagery. Preserve native Sentinel-2 detail where suitable. Validate any fusion or resampling method before operational use and respect source licensing and redistribution terms.

## 5. Flood Engine — Expanded Scope

The Flood Engine will retain rainfall and drainage as its initial core focus and progressively add validated hazard-specific modules.

Planned modules:
1. Rainfall Flood Risk — intensity, accumulation, forecast rainfall, and drainage constraints.
2. Flash Flood Intelligence — rapid-onset conditions and downstream exposure.
3. Riverine Flood Intelligence — river observations, catchments, and floodplain conditions.
4. Drainage and Terrain — flow accumulation, slope, and drainage-capacity proxies.
5. El Niño / ENSO Intelligence — climate phase and seasonal rainfall outlooks as contextual flood-risk signals, not direct local flash-flood triggers.
6. Tsunami Intelligence — authoritative tsunami warnings and coastal exposure/response support. Tsunamis are a distinct coastal hazard, not a rainfall-driven flood mechanism.
7. Urban Flood Intelligence — localized rainfall, impervious surfaces, and drainage where data permit.
8. Soil Saturation / Antecedent Conditions.
9. Dam, Reservoir, and River-Release Intelligence where verified data are available.
10. Coastal Flooding and Storm Surge, distinct from tsunami hazards.
11. Flood Change Detection using satellite-observed water extent.
12. Flood Exposure and Impact — people, infrastructure, and agriculture.
13. Flood Forecasting and Alerting — confidence-qualified, time-stamped outputs.
14. Flood Recovery Intelligence — recession, visible damage, and recovery indicators.

Future modules must use appropriate data, validation, and hazard-specific methods. Do not imply that all modules are implemented or that every hazard can be forecast with equal confidence.

## 6. Kenya-Wide Alerts and Emergency Response Intelligence

Expand the Alerts Engine beyond Nairobi toward Kenya-wide coverage, initially prioritizing fires and flash floods while supporting longer-term hazards.

Alert classes:
- Rapid-onset: fires, flash floods, and other fast-developing incidents.
- Long-term: drought, agricultural stress, persistent flood risk, and other evolving hazards.

Planned map layers:
- Active and historical alerts.
- County, subcounty, ward, and relevant local boundaries.
- Emergency resources: fire stations, ambulances, hospitals, rescue teams, shelters, and other verified facilities.
- Population estimates and exposure.
- Vulnerability indicators, with responsible use of sensitive data.
- Road networks, access restrictions, response routes, and live traffic where providers support it.
- Incident footprints, historical events, and response records.

Alert intelligence may include hazard type, location, likely cause and confidence, severity, source evidence, estimated exposed population, verified injuries/casualties where available, vulnerable groups, nearby resources, traffic/routes, recommended actions, and timestamps.

Resource locations must not be represented as proof of operational readiness. Population estimates must not be presented as live headcounts. Injuries, casualties, traffic, and resource availability must be verified or explicitly marked unknown, estimated, or unverified.

Investigate alternatives to Brevo and Africa's Talking. Evaluate a GeoShield-owned notification orchestration layer with interchangeable delivery providers, retries, delivery logs, acknowledgements, and escalation. Building a proprietary telecom network is not assumed to be required.

## 7. Crop-Based Agriculture and Polygon Intelligence

### 7.1 Crop-Based Agricultural Intelligence
Move from generic county temperature/rainfall risk toward crop-specific suitability and agricultural risk.

Planned capabilities:
- Crop datasets by county and, where available, more localized areas.
- Crop-specific temperature, rainfall, soil, and growth-stage requirements.
- Crop condition, suitability, stress, and risk indicators.
- Integration with NDVI, drought, flood, and relevant environmental data.
- Crop-specific mitigation recommendations with evidence and uncertainty.

High temperature or rainfall must not automatically be classified as agricultural risk without considering crop-specific tolerances, growth stage, and local context.

### 7.2 Polygon Drawing and Area-of-Interest Analysis
Allow farmers, cartographers, and other users to draw polygons, upload boundaries, or select an area.

Develop a shared geospatial analysis service that returns available temperature, rainfall, NDVI, drought, fire, flood, crop/agricultural risk, area statistics, data freshness, and practical recommendations for the selected geometry.

Reuse this capability across Agriculture, Satellite Intelligence, Flood, Fire, Analytics, Reports, and GeoShield AI. Clearly identify unavailable datasets and spatial-resolution limits.

## 8. Food Security Intelligence Engine

Create a dedicated Food Security capability connected to Agriculture, Flood, Drought, Satellite Intelligence, Analytics, and GeoShield AI.

Initial MVP:
- Crop condition and production-anomaly indicators.
- Rainfall anomalies, drought stress, and flood disruption.
- Available food-security datasets and geographic indicators.
- County-level monitoring and historical trends.
- Food supply disruption indicators where supported.
- Evidence-based monitoring and mitigation recommendations.

Longer-term expansion may include market prices, household food access, affordability, nutrition indicators, food availability, supply-chain disruptions, and stability.

Food security is broader than crop production. Do not infer household hunger, malnutrition, or food availability from satellite imagery alone.

## 9. Analytics Engine — Continuous Data Analysis

Develop the Analytics Engine as a continuously operating backend service, independent of whether a dashboard is open.

Planned capabilities:
- Data ingestion and source-health analytics.
- Data quality, missing-value, anomaly, and freshness checks.
- Geospatial statistics and zonal analysis.
- Time-series, trend, and seasonal analysis.
- Hazard analytics and cross-county comparisons.
- Model validation and forecast verification against observed outcomes.
- Reproducible analysis, charts, maps, and executive-ready explanations.
- Presentation/report outputs explaining methodology, evidence, assumptions, and limitations.

Use scheduled and event-triggered jobs, persistent results, retries, logging, and job-health monitoring. The UI should display actual job status, processing lag, data freshness, and validation metrics. "Always running" means monitored backend processing, not an unverified claim of uninterrupted operation.

## 10. Functional UI Cards

Assess and add functional cards connected to real APIs/engines, including:
- GeoShield Map.
- Alerts & Emergency Response.
- Satellite Intelligence and Change Detection.
- Agriculture.
- Food Security.
- Analytics.
- Disaster Video Studio.
- GeoShield AI Assistant.
- Reports & Intelligence.
- Weather & Climate.
- Water Resources.
- Infrastructure Exposure.
- Population & Vulnerability.
- Environmental Monitoring.
- Recovery & Reconstruction.
- Data Source Health.
- Scenario Simulator.

Cards must show real data or clearly identify planned/unavailable functionality. Avoid fabricated metrics and duplicate cards that fragment the same capability.

## 11. GeoShield AI Interactive Intelligence Engine

Develop a GeoShield-specific conversational assistant grounded in authorized platform data and tools.

Planned capabilities:
- Answer questions about GeoShield hazards, imagery, agriculture, food security, maps, alerts, analytics, and reports.
- Retrieve current platform data through controlled APIs/tools.
- Explain risk classifications, evidence, assumptions, and uncertainty.
- Compare locations, time periods, and observations.
- Generate summaries and reports.
- Offer recommendations while preserving human decision authority.

Requirements:
- Access control and protection of classified/restricted information.
- No fabricated live data or unsupported claims.
- Clear distinction between observation, estimate, forecast, and recommendation.
- Auditable tool use and outputs.
- No unauthorized emergency dispatch or consequential action without an explicitly authorized workflow.

The AI is the primary intelligence interface, not an unrestricted authority over engines or emergency decisions.

## 12. Responsive Cross-Device UI

Make GeoShield usable across desktops, laptops, phones, tablets, and iPads.

Planned work:
- Responsive layouts using appropriate breakpoints, CSS Grid, and Flexbox.
- Touch-friendly map and polygon-drawing controls.
- Adaptive panels, navigation, cards, tables, and charts.
- Mobile map-first views and compact panels.
- Performance optimization for lower-powered devices and slower networks.
- Cross-browser and cross-device testing.

Preserve the existing Map / Intelligence page separation and page-visibility behavior while improving responsiveness. Avoid a wholesale redesign that destabilizes existing functionality.

## 13. Suggested Implementation Sequence

Phase 1 — Foundation:
- Achievements file and GitHub push.
- Restore Earthquake card.
- Audit Disaster Studio and satellite fallbacks.
- Establish regression tests and verify repository state.

Phase 2 — Data and imagery:
- Disaster Studio integration.
- Provider health and failover.
- Sentinel-2 Change Detection.
- Landsat-Sentinel comparison proof of concept.
- Shared Area-of-Interest Analysis API.

Phase 3 — Hazard and agricultural intelligence:
- Flood Engine expansion framework.
- ENSO and tsunami source integration.
- Crop-based Agriculture.
- Polygon analysis.
- Food Security MVP.

Phase 4 — National response and analytics:
- Kenya-wide Alerts and response map.
- Resource, population, vulnerability, traffic, and route data integrations.
- Historical/active alert registry.
- Continuous Analytics Engine.
- Functional UI card expansion.

Phase 5 — AI, responsive UI, and validation:
- GeoShield AI Assistant.
- Authorized cross-engine retrieval.
- Responsive UI.
- End-to-end testing, security, reliability, and performance validation.

This sequence is a planning framework, not a delivery guarantee. Provider access, data quality, validation, engineering capacity, and funding may change timelines. Parallel work must not compromise the existing platform.

## 14. Definition of Done

A V2 feature is complete only when:
- Its scope and data sources are documented.
- The implementation is connected to the intended engine/API.
- Relevant tests pass.
- Actual behavior is verified in the running application.
- Failures, stale data, and uncertainty are handled transparently.
- Existing functionality has not regressed.
- Documentation reflects the verified result.
- Git changes are reviewed before commit and push.

**Roadmap status:** Planned. Update individual items only as work is implemented and verified.

