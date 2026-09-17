# GEOSHIELD AI ENTERPRISE
# MASTER AI PROJECT CONTEXT & SYSTEM ARCHITECTURE
# ============================================================
# This document is the high-level architectural context for
# GeoShield AI Enterprise.
#
# PURPOSE:
# This file is intended to be supplied to another AI/developer
# so that GeoShield AI can be understood as ONE integrated
# intelligence platform rather than as unrelated modules.
#
# IMPORTANT:
# This document distinguishes between implemented/connected
# functionality and functionality that is still being developed.
# Do not assume an unfinished component is complete.
# ============================================================


# 1. PROJECT IDENTITY
# ============================================================

Project Name:
    GeoShield AI Enterprise

Primary Purpose:
    GeoShield AI is an integrated geospatial intelligence,
    environmental intelligence, disaster intelligence and
    decision-support platform.

Core Idea:
    GeoShield AI collects information from satellites,
    geospatial data sources, environmental sources, event
    sources and specialized intelligence services; processes
    and correlates that information through a central Main
    Engine; and transforms the resulting information into
    intelligence, risk information, alerts, reports, analytics
    and actionable situational awareness.

GeoShield is NOT simply:
    - A satellite viewer
    - A map application
    - A weather application
    - A collection of unrelated APIs
    - A single AI chatbot
    - A collection of independent engines

GeoShield IS:
    A connected intelligence ecosystem in which data sources,
    satellites, specialized engines, AI systems, analytical
    services, alerts, reports and the user interface communicate
    as parts of one platform.


# 2. THE CORE GEOShIELD CONCEPT
# ============================================================

The fundamental architecture is:

    DATA SOURCES
         |
         v
    SATELLITES / EXTERNAL DATA
         |
         v
    DATA INGESTION & SERVICES
         |
         v
    =========================
          MAIN ENGINE
    =========================
         |
         +--------------------------+
         |                          |
         v                          v
    SPECIALIZED ENGINES       INTELLIGENCE SERVICES
         |                          |
         +-------------+------------+
                       |
                       v
                  AI / RISK
                       |
          +------------+------------+
          |            |            |
          v            v            v
       ALERTS       REPORTS      ANALYTICS
          |            |            |
          +------------+------------+
                       |
                       v
                GEOSHIELD UI
                       |
                       v
                HUMAN DECISION


The Main Engine is the central communication and orchestration
layer.

The services and engines are intended to communicate through
this central architecture instead of becoming isolated systems.


# 3. MAIN ENGINE
# ============================================================

The Main Engine is one of the most important architectural
components of GeoShield AI.

Its purpose is to coordinate the platform.

The Main Engine acts as the central integration/orchestration
layer between:

    - Satellite systems
    - External data providers
    - Specialized engines
    - Intelligence services
    - AI risk analysis
    - Alerts
    - Reports
    - Analytics
    - Resources
    - User-facing systems

Conceptually:

    Satellite A --------\
    Satellite B ---------\
    Satellite C ----------\
    External APIs ---------> MAIN ENGINE
    Earthquake Engine ----/
    Agriculture Engine ---/
    Traffic Services ----/
    Resource Services ---/
                           |
                           +--> AI Risk
                           |
                           +--> Alerts
                           |
                           +--> Reports
                           |
                           +--> Analytics
                           |
                           +--> UI / Dashboard


The Main Engine should be treated as the central nervous system
of the platform.

A new service should be designed with the Main Engine architecture
in mind rather than being added as an isolated feature.


# 4. SATELLITE INTELLIGENCE
# ============================================================

GeoShield AI has a satellite intelligence layer.

The satellite layer provides Earth-observation and related
information that can be used by the rest of the platform.

Satellite information may contribute to:

    - Land observation
    - Environmental monitoring
    - Agriculture
    - Disaster assessment
    - Change detection
    - Mapping
    - Infrastructure observation
    - Resource intelligence
    - Risk analysis
    - Situational awareness

The currently connected satellite systems/providers are part of
the project's existing implementation.

IMPORTANT:
    Do not invent additional satellite integrations.
    When working directly with the repository, inspect the
    actual satellite registry, satellite services and API
    implementations to determine the exact current inventory.

Satellite data should ultimately flow into the platform's
central intelligence architecture rather than remain isolated
inside a satellite viewer.


# 5. SPECIALIZED INTELLIGENCE ENGINES
# ============================================================

GeoShield is designed around specialized engines.

Each engine focuses on a particular intelligence domain while
remaining part of the larger GeoShield ecosystem.

The engines currently include or are intended to include:


## 5.1 EARTHQUAKE ENGINE
Status:
    Connected / part of the current service architecture.

Purpose:
    Detect, process and communicate earthquake-related
    information.

Potential intelligence:
    - Earthquake events
    - Location
    - Magnitude
    - Depth
    - Event timing
    - Geographic impact
    - Potential affected areas
    - Event correlation

The Earthquake Engine should communicate its results through
the Main Engine so that earthquake information can contribute
to alerts, risk analysis, reports and analytics.


## 5.2 AGRICULTURE ENGINE
Status:
    Connected / part of the current service architecture.

Purpose:
    Provide agricultural and land-related intelligence using
    available geospatial and environmental information.

Potential intelligence:
    - Crop/vegetation conditions
    - Land condition
    - Agricultural stress
    - Environmental changes
    - Agricultural risk
    - Area-based agricultural intelligence

Agriculture intelligence should be capable of interacting with
satellite observations and other relevant services through the
Main Engine.


## 5.3 ALERTS ENGINE
Status:
    Connected, with additional alert functionality still being
    developed.

Purpose:
    Transform detected events and intelligence into actionable
    alerts.

The Alerts Engine is expected to work with information from
multiple parts of GeoShield rather than from one source only.

Possible alert sources include:

    - Earthquake events
    - Disaster events
    - Environmental risks
    - Agricultural risks
    - Traffic incidents
    - Other detected hazards
    - AI-generated risk conditions
    - Satellite-derived changes

Alerts should ultimately be capable of reaching:

    - GeoShield dashboard
    - Active Alerts interface
    - Notification systems
    - Phone/mobile notification channels


# 6. SERVICES
# ============================================================

GeoShield is not limited to large "engines".

The platform also contains supporting services.

These services provide information that can be consumed by
engines and the Main Engine.

Examples include:


## 6.1 LIVE TRAFFIC
Purpose:
    Provide traffic and mobility-related intelligence.

Traffic information can contribute to:

    - Situational awareness
    - Disaster response
    - Emergency routing
    - Infrastructure intelligence
    - Resource deployment
    - Incident monitoring

Traffic should be treated as another intelligence data source
that can communicate with the Main Engine.


## 6.2 RESOURCES
Purpose:
    Provide information about available resources relevant to
    response, analysis and decision-making.

Resources may include information such as:

    - Response resources
    - Emergency resources
    - Geographic resources
    - Infrastructure
    - Facilities
    - Personnel/resource availability
    - Other operational assets

The exact resource schema should follow the actual repository
implementation.


## 6.3 OTHER SERVICES
GeoShield is designed to allow additional services to be added
without breaking the central architecture.

Examples could include:

    - Weather
    - Flood information
    - Fire information
    - Environmental monitoring
    - Infrastructure monitoring
    - Population-related datasets
    - Roads
    - Emergency facilities
    - Government/open datasets
    - Other external intelligence sources

These should be integrated through the established architecture.


# 7. INTELLIGENCE CORRELATION
# ============================================================

One of GeoShield's fundamental purposes is CORRELATION.

A single data source may only describe one part of a situation.

GeoShield should be capable of combining information from
multiple sources.

Example:

    Satellite observation
            +
    Weather information
            +
    Terrain/geospatial information
            +
    Agriculture information
            +
    Traffic information
            +
    Resources
            +
    Historical information
            |
            v
       MAIN ENGINE
            |
            v
       AI / RISK ANALYSIS
            |
            v
    SITUATIONAL INTELLIGENCE


This allows GeoShield to move from:

    RAW DATA

to:

    INFORMATION

to:

    CORRELATED INTELLIGENCE

to:

    RISK / SITUATIONAL AWARENESS

to:

    ACTIONABLE OUTPUT


# 8. AI RISK SYSTEM
# ============================================================

Status:
    The AI Risk system exists conceptually but is NOT yet
    considered fully wired/finished.

The intended purpose of AI Risk is to analyze information
coming from the GeoShield intelligence ecosystem and assist
with identifying risk conditions.

AI Risk should NOT be treated as an independent disconnected AI.

It should receive structured information from the platform,
including relevant outputs from:

    - Satellites
    - Earthquake Engine
    - Agriculture Engine
    - Alerts Engine
    - Traffic
    - Resources
    - Other services
    - Main Engine
    - Historical/analytical information

Potential outputs include:

    - Risk identification
    - Risk classification
    - Risk context
    - Geographic risk areas
    - Risk explanations
    - Confidence/context information
    - Recommended attention/action areas

IMPORTANT:
    The exact AI Risk architecture is still under development.
    Do not claim that it is fully implemented.


# 9. ACTIVE ALERTS
# ============================================================

Status:
    Still being developed.

Active Alerts is the user-facing operational representation
of currently relevant alerts.

It should eventually allow GeoShield to distinguish between:

    - Active alerts
    - Resolved alerts
    - Historical alerts
    - New alerts
    - Alert severity
    - Alert location
    - Alert source
    - Alert time
    - Alert status

The Active Alerts system should communicate with the Alerts
Engine and Main Engine.


# 10. PHONE ALERTS / NOTIFICATIONS
# ============================================================

Status:
    Not fully completed.

GeoShield is intended to support alert delivery beyond the
desktop/web interface.

The intended architecture should allow important alerts to
reach a user's phone through an appropriate notification
mechanism.

Possible mechanisms may include:

    - Push notifications
    - SMS
    - Mobile application notifications
    - Other notification gateways

Do not assume a particular provider or technology until it is
specified and implemented.

The notification system should receive validated alerts from
the GeoShield alert architecture rather than independently
creating contradictory alert states.


# 11. REPORTS ENGINE
# ============================================================

Status:
    NOT FINISHED.

The Reports Engine has not yet been fully designed or completed.

The final architecture will be specified separately by the
GeoShield project owner.

The Reports Engine is intended to transform GeoShield data and
intelligence into structured reports.

Potential report inputs may include:

    - Satellite observations
    - Event information
    - Earthquake intelligence
    - Agriculture intelligence
    - Alerts
    - Risk analysis
    - Traffic
    - Resources
    - Analytics
    - Historical information

Potential report outputs may include:

    - Incident reports
    - Disaster reports
    - Situation reports
    - Agricultural reports
    - Risk reports
    - Intelligence reports
    - Executive summaries
    - Time-based reports
    - Geographic reports

IMPORTANT:
    Do not implement or assume the final Reports Engine design
    until the project owner provides its intended workflow.


# 12. ANALYTICS ENGINE
# ============================================================

Status:
    NOT YET CREATED / NOT COMPLETE.

The Analytics Engine is intended to become a dedicated
analytical layer within GeoShield.

Its future responsibility may include:

    - Historical analysis
    - Trend analysis
    - Event statistics
    - Geographic comparisons
    - Time-series analysis
    - Engine performance metrics
    - Alert statistics
    - Risk statistics
    - Satellite-derived statistics
    - Agricultural analytics
    - Disaster analytics
    - Operational analytics

The final implementation has not yet been defined.

Do not treat Analytics Engine as completed.


# 13. ALERT FLOW
# ============================================================

The intended alert architecture is approximately:

    DATA / EVENT
        |
        v
    DETECTION
        |
        v
    SPECIALIZED ENGINE
        |
        v
    MAIN ENGINE
        |
        v
    CORRELATION / VALIDATION
        |
        v
    AI RISK
        |
        v
    ALERTS ENGINE
        |
        +--------------------+
        |                    |
        v                    v
    ACTIVE ALERTS       PHONE ALERTS
        |
        v
    USER


This is an architectural concept.

Exact implementation details must follow the actual codebase
and future project specifications.


# 14. GEOSPATIAL FOUNDATION
# ============================================================

GeoShield is fundamentally spatial.

Information should be associated with geography wherever
appropriate.

Important spatial concepts include:

    - Coordinates
    - Points
    - Lines
    - Polygons
    - Counties
    - Administrative areas
    - Roads
    - Locations
    - Satellite footprints
    - Affected areas
    - Risk zones
    - Resource locations
    - Event locations

The map is therefore not merely a visual decoration.

It is a core interface for understanding the geographic
relationship between intelligence objects.


# 15. GEOShIELD USER INTERFACE
# ============================================================

The frontend is intended to expose the intelligence platform
through a command-center style interface.

The major conceptual workspace separation includes:

    MAP
       |
       v
    INTELLIGENCE


## MAP WORKSPACE

The Map workspace is intended to contain:

    - Main map
    - Right-side information panel
    - Bottom metrics
    - Geographic visualization
    - Spatial intelligence


## INTELLIGENCE WORKSPACE

The Intelligence workspace contains satellite and intelligence
interfaces.

The current frontend architecture separates:

    geoshieldMapPage

from:

    geoshieldIntelligencePage


The Satellite Intelligence area includes components such as:

    - Satellite center
    - Sentinel-2 product interface
    - Satellite navigation
    - Satellite cards/details

The inactive workspace should not interfere with the active
workspace layout.


# 16. FRONTEND PRINCIPLE
# ============================================================

The frontend should represent the architecture rather than
create a disconnected visual shell.

The UI should ultimately allow the user to move from:

    LOCATION
        ->
    DATA
        ->
    INTELLIGENCE
        ->
    RISK
        ->
    ALERT
        ->
    REPORT / ANALYTICS


The interface should make relationships between systems
understandable.


# 17. END-TO-END GEOShIELD WORKFLOW
# ============================================================

A simplified operational workflow is:

    1. DATA IS COLLECTED
       |
       v
    2. SATELLITE / EXTERNAL SOURCES PROVIDE INFORMATION
       |
       v
    3. DATA IS INGESTED INTO GEOShIELD SERVICES
       |
       v
    4. INFORMATION IS ROUTED THROUGH THE MAIN ENGINE
       |
       v
    5. SPECIALIZED ENGINES PROCESS DOMAIN-SPECIFIC INFORMATION
       |
       v
    6. MAIN ENGINE COORDINATES THE OUTPUTS
       |
       v
    7. INFORMATION IS CORRELATED
       |
       v
    8. AI / RISK LAYER ANALYZES RELEVANT CONDITIONS
       |
       v
    9. ALERTS ARE GENERATED WHERE APPROPRIATE
       |
       +-----------> ACTIVE ALERTS
       |
       +-----------> PHONE NOTIFICATIONS
       |
       +-----------> REPORTS
       |
       +-----------> ANALYTICS
       |
       v
    10. GEOShIELD PRESENTS INTELLIGENCE TO THE USER
       |
       v
    11. HUMAN USERS MAKE INFORMED DECISIONS


# 18. EXAMPLE: DISASTER INTELLIGENCE
# ============================================================

Example scenario:

A significant event occurs in a geographic area.

GeoShield may receive:

    - Satellite information
    - Event information
    - Weather information
    - Traffic information
    - Geographic information
    - Resource information

The information enters the platform.

The Main Engine coordinates the relevant services.

The appropriate specialized engines process their domains.

The system correlates the information.

AI Risk can evaluate relevant risk conditions.

The Alerts Engine can generate an operational alert.

The Active Alerts interface can display it.

The notification layer can communicate the alert to a phone.

The Reports Engine can eventually produce a formal report.

The Analytics Engine can eventually analyze the event
historically and statistically.

This illustrates how GeoShield is intended to function as one
system rather than a collection of independent applications.


# 19. EXAMPLE: AGRICULTURAL INTELLIGENCE
# ============================================================

Satellite observations can provide information about land and
vegetation.

The Agriculture Engine can process agricultural information.

The Main Engine can coordinate that information with other
relevant services.

AI Risk can eventually identify agricultural risk conditions.

Alerts can communicate important changes.

Reports can document the situation.

Analytics can eventually identify trends across time and
geographic areas.

The result is agricultural intelligence rather than simply
displaying a satellite image.


# 20. EXAMPLE: TRAFFIC + DISASTER RESPONSE
# ============================================================

Traffic information can become significantly more useful when
combined with disaster intelligence.

Example:

    Disaster event
         +
    affected geographic area
         +
    traffic congestion
         +
    available resources
         |
         v
      MAIN ENGINE
         |
         v
    CORRELATED INTELLIGENCE
         |
         v
    OPERATIONAL AWARENESS


This demonstrates the importance of integrating services
through the Main Engine.


# 21. DATA -> INFORMATION -> INTELLIGENCE
# ============================================================

GeoShield should be understood through this hierarchy:

    DATA
      |
      v
    INFORMATION
      |
      v
    CORRELATION
      |
      v
    INTELLIGENCE
      |
      v
    RISK / SITUATIONAL AWARENESS
      |
      v
    ALERT / REPORT / ANALYTICS
      |
      v
    HUMAN DECISION


GeoShield's value is not merely collecting data.

Its purpose is to transform data into useful intelligence.


# 22. HUMAN-IN-THE-LOOP PRINCIPLE
# ============================================================

GeoShield is a decision-support platform.

The system provides:

    - Information
    - Intelligence
    - Risk indicators
    - Alerts
    - Reports
    - Analytics
    - Geographic context

Human users remain responsible for interpreting intelligence
and making operational decisions.

AI outputs should be presented with appropriate context,
provenance and uncertainty where applicable.


# 23. SYSTEM COMMUNICATION PRINCIPLE
# ============================================================

Every new major service should answer:

    1. What data does it consume?
    2. Where does that data come from?
    3. How does it communicate with the Main Engine?
    4. What does it produce?
    5. Which other services consume its output?
    6. Can its output contribute to risk?
    7. Can its output contribute to alerts?
    8. Can its output contribute to reports?
    9. Can its output contribute to analytics?
    10. How is its information represented geographically?


# 24. EXTENSIBILITY
# ============================================================

GeoShield is intended to be extensible.

Future integrations may include:

    - Additional satellites
    - Additional Earth-observation providers
    - Additional disaster data providers
    - Weather services
    - Traffic providers
    - Agricultural datasets
    - Infrastructure datasets
    - Emergency systems
    - New AI models
    - New analytical models
    - Mobile applications
    - Notification providers
    - Additional intelligence engines


Any new component should integrate with the existing
architecture instead of bypassing the Main Engine without a
clear architectural reason.


# 25. OSIRI CONCEPT
# ============================================================

Potential future concept:

    OSIRI
    Open Source Intelligence Satellite / Starlink concept

Proposed purpose:
    Live-camera or near-live visual intelligence concept.

STATUS:
    PLANNED / CONCEPTUAL.

IMPORTANT:
    OSIRI must NOT be described as an implemented GeoShield
    satellite integration unless the repository later confirms
    that it has actually been implemented.


# 26. CURRENT DEVELOPMENT STATUS
# ============================================================

The following represents the project owner's current
description of the platform.

IMPLEMENTED / CONNECTED:
    - Satellite integrations
    - Main Engine architecture
    - Earthquake Engine
    - Agriculture Engine
    - Alerts Engine
    - Live traffic-related service capability
    - Resources-related service capability
    - Communication between connected services through the
      central architecture

IN PROGRESS / NEEDS COMPLETION:
    - AI Risk wiring
    - Active Alerts
    - Phone alert/notification functionality

NOT YET FINISHED:
    - Reports Engine
    - Analytics Engine

AWAITING PROJECT OWNER SPECIFICATION:
    - Final Reports Engine architecture
    - Final Analytics Engine architecture
    - Exact final AI Risk wiring
    - Exact phone notification provider/implementation

IMPORTANT:
    This status is based on the project owner's declared
    development state. When making code-level decisions,
    verify the actual repository implementation.


# 27. DEVELOPMENT RULES FOR FUTURE AI ASSISTANTS
# ============================================================

When another AI receives this document, it MUST understand:

    GeoShield is an integrated platform.

Do NOT automatically:

    - Rewrite the entire architecture.
    - Replace the Main Engine.
    - Create duplicate engines.
    - Disconnect existing services.
    - Replace working satellite integrations unnecessarily.
    - Assume unfinished systems are complete.
    - Invent APIs or providers.
    - Invent satellite capabilities.
    - Modify backend/database systems merely because a UI task
      was requested.
    - Change existing working functionality without a reason.

Before changing a system:

    1. Inspect the repository.
    2. Understand the existing architecture.
    3. Identify the Main Engine relationship.
    4. Identify dependencies.
    5. Determine what is already implemented.
    6. Determine what is incomplete.
    7. Make the smallest appropriate change.
    8. Test the affected functionality.


# 28. REPORTS ENGINE DEVELOPMENT RULE
# ============================================================

The Reports Engine is intentionally left open.

When the project owner provides its design:

    - Treat that specification as authoritative.
    - Integrate it into the Main Engine architecture.
    - Reuse existing intelligence outputs.
    - Avoid duplicating data processing unnecessarily.
    - Preserve existing satellite and engine integrations.
    - Connect reports to relevant alerts, risk and analytics
      where appropriate.


# 29. ANALYTICS ENGINE DEVELOPMENT RULE
# ============================================================

The Analytics Engine is also intentionally open.

When designed, it should consume appropriate structured
information from the platform.

It should not become a disconnected analytics application.

It should integrate with the Main Engine and use established
GeoShield data structures where appropriate.


# 30. AI CONTEXT RULE
# ============================================================

If this file is supplied to an AI, the AI should first build a
mental model of:

    GEOShIELD
       |
       +-- DATA SOURCES
       |
       +-- SATELLITES
       |
       +-- MAIN ENGINE
       |      |
       |      +-- EARTHQUAKE
       |      +-- AGRICULTURE
       |      +-- ALERTS
       |      +-- TRAFFIC
       |      +-- RESOURCES
       |      +-- OTHER SERVICES
       |
       +-- AI RISK
       |
       +-- ACTIVE ALERTS
       |
       +-- PHONE NOTIFICATIONS
       |
       +-- REPORTS
       |
       +-- ANALYTICS
       |
       +-- USER INTERFACE


The AI should then inspect the actual repository before making
implementation decisions.


# 31. WHAT GEOShIELD IS ULTIMATELY TRYING TO ACHIEVE
# ============================================================

GeoShield AI is intended to create a unified intelligence
environment in which geographically relevant information from
multiple sources can be collected, processed, correlated and
communicated.

The platform connects:

    EARTH OBSERVATION
          +
    GEOSPATIAL INFORMATION
          +
    SPECIALIZED INTELLIGENCE ENGINES
          +
    AI
          +
    RISK ANALYSIS
          +
    ALERTING
          +
    REPORTING
          +
    ANALYTICS
          +
    HUMAN DECISION-MAKING


The objective is to reduce fragmentation between data sources
and turn complex geographic information into understandable,
actionable intelligence.

GeoShield should therefore be thought of as an intelligence
ecosystem.

Satellites provide observations.

Services provide additional context.

Specialized engines interpret domain-specific information.

The Main Engine connects and coordinates those components.

AI helps interpret and assess relevant information.

Alerts communicate important conditions.

Reports document intelligence.

Analytics reveal patterns and trends.

The user interface brings the resulting intelligence together
for human understanding and decision-making.


# 32. FINAL ARCHITECTURAL PRINCIPLE
# ============================================================

THE MAIN ENGINE CONNECTS THE PLATFORM.

SATELLITES PROVIDE OBSERVATIONS.

SERVICES PROVIDE CONTEXT.

SPECIALIZED ENGINES PROCESS DOMAIN-SPECIFIC INFORMATION.

AI CORRELATES AND ASSISTS WITH INTELLIGENCE AND RISK ANALYSIS.

ALERTS COMMUNICATE IMPORTANT CONDITIONS.

REPORTS DOCUMENT EVENTS AND INTELLIGENCE.

ANALYTICS REVEAL PATTERNS, TRENDS AND PERFORMANCE.

THE USER INTERFACE PRESENTS THE RESULT.

THE HUMAN USER MAKES THE FINAL DECISION.


# END OF GEOSHIELD AI MASTER CONTEXT
# ============================================================

---

# CURRENT DEVELOPMENT STATUS

## COMPLETED

- Core GeoShield platform architecture
- Main Engine architecture/integration
- Satellite intelligence architecture
- Earthquake Engine
- Existing satellite connections/integrations as verified in the repository
- Existing intelligence/services already implemented in the repository

## REMAINING MAJOR DEVELOPMENT

1. Agriculture Engine
2. Reports Engine
3. Analytics Engine
4. Alerts System
5. AI Risk integration/refinement
6. Active Alerts implementation/refinement
7. Phone/mobile alert notifications

## IMPORTANT

The Earthquake Engine is now considered **COMPLETED**.

The next major development work should focus on the remaining components rather than rebuilding completed architecture.

The user will provide additional specifications for the Agriculture, Reports, Analytics and Alerts components.

Future AI assistants must inspect the repository before modifying existing systems and must preserve the Main Engine communication architecture.

---

# HANDOFF INSTRUCTION FOR THE NEXT AI

This document is the master context for GeoShield AI Enterprise.

The next AI should:

1. Read this entire file first.
2. Understand that GeoShield is an integrated intelligence platform, not merely a map or satellite viewer.
3. Inspect the repository before writing code.
4. Treat the Earthquake Engine as completed.
5. Focus remaining development on Agriculture, Reports, Analytics and Alerts according to the user's instructions.
6. Do not rebuild completed components without a technical reason.
7. Do not invent functionality that has not been specified or verified.
8. Preserve the Main Engine as the central communication/orchestration architecture.
9. Ask for or follow the user's specifications when implementing the unfinished engines.
10. Maintain the separation between data acquisition, services, intelligence engines, AI/risk, alerts, reports, analytics and the UI.
11. Keep humans responsible for final decisions; GeoShield provides intelligence and decision support.


## Agriculture Engine - NDVI Integration Status

### Completed / Done So Far

#### Sidebar Mojibake Corruption

The project-wide sidebar mojibake corruption has been fully resolved and confirmed in-browser.

#### NDVI Architecture

The NDVI architecture has been decided.

GeoShield will use **multi-source NDVI/vegetation-index fusion**:

1. **Sentinel-2** - primary source, approximately 10m spatial resolution.
2. **VIIRS-VI** - fallback and cross-check source.
3. **MODIS-VI** - fallback and cross-check source.

The architecture deliberately avoids relying on a single satellite source.

#### Sentinel-2 NDVI Connector

The Sentinel-2 NDVI connector has been built and wired into the Main Engine.

New file:

`core\connectors\sentinel2\sentinel2_ndvi_connector.py`

The connector:

- Follows the existing `BaseConnector` interface used by the other GeoShield connectors, including GPM, ERA5 and FIRMS.
- Reuses the existing `CopernicusAuthManager` OAuth2 token.
- Uses the existing curl-based Copernicus authentication pattern that has already been proven working for the WMS tile layer.
- Implements Sentinel-2 NDVI acquisition through Sentinel Hub's Statistical API.
- Processes county geometries and returns aggregated NDVI information.
- Includes live/mock fallback behavior and status tracking consistent with the existing connector architecture.

#### Main Engine Integration

`core\engines\main_engine.py` has been modified.

Changes include:

- Sentinel-2 NDVI connector import.
- Sentinel-2 NDVI connector registration:
  `registry.register(build_sentinel2_ndvi_connector())`
- New:
  `main_engine.get_sentinel2_ndvi()`
- The method mirrors the existing `get_gpm_rainfall()` and `get_era5_weather()` architecture.
- `_last_status` tracking is included.

#### End-to-End Plumbing Verification

The NDVI integration chain has been confirmed to execute cleanly.

Verified:

- Copernicus token authentication succeeds.
- County geometries load from the same `kenya_counties.geojson` source already used by GPM.
- Connector registry lookup works.
- Sentinel-2 NDVI connector `search()` call executes.
- No crashes occurred in the connector plumbing.

#### Resolution / CRS Units Mismatch - RESOLVED

The Sentinel Hub Statistical API request declares county bounds using `EPSG:4326`. Because the requested CRS uses geographic degrees, `resx` and `resy` must also be expressed in degrees rather than meters.

The first test incorrectly used `100` (interpreted as ~100 degrees/pixel - larger than Kenya's geographic extent). Sentinel Hub's error response allowed the resolution to be recalculated.

The corrected value, `0.01°` (~1.1 km at Kenyan latitude, below the 1500m limit), was applied to the real connector file and is confirmed working.

#### Full 47-County Live Validation - CONFIRMED

`test_all_counties.py` was rebuilt to use the corrected `0.01°` resolution (the earlier isolated test script had a stale hardcoded `0.05` value that was retesting the old broken configuration, not a real connector bug).

Result of the full live sweep:

    Connector enabled: True
    Success: True
    Elapsed seconds: 107.1
    Total counties: 47
    Counties with real NDVI: 47
    Counties with null NDVI: 0

Sample values (first 10):

    Turkana: 0.1042
    Marsabit: 0.0904
    Mandera: 0.1593
    Wajir: 0.0992
    West Pokot: 0.2532
    Samburu: 0.1842
    Isiolo: 0.1313
    Baringo: 0.2590
    Keiyo-Marakwet: 0.4127
    Trans Nzoia: 0.4683

All 47 counties returned physically plausible values: arid northern counties (Turkana, Marsabit, Mandera, Wajir) scored low, while Trans Nzoia - Kenya's wheat/maize breadbasket - scored high. NDVI is confirmed live end to end, not mock/fallback data.

#### Cold-Start Latency - Identified and Mitigated

A full 47-county sweep takes ~107 seconds (each Sentinel Hub Statistical API call is a real satellite-data computation, not a simple lookup). Left unmitigated, this meant the first `/api/agriculture/live` request after each 180-minute cache expiry would block for ~107 seconds.

Mitigation implemented: a background warm-up thread refreshes the NDVI cache every 170 minutes (just under the connector's 180-minute `CACHE_MINUTES` window), so live requests always hit the fast cached path.

#### RiskEngine - Rebalanced for NDVI - PATCHED

`core/risk_engine.py` -> `calculate_agriculture_risk()` has been rebalanced from 3 factors to 4 factors (rainfall, temperature, humidity, NDVI), with each factor's weight shrunk proportionally so the existing Low/Moderate/High/Extreme thresholds still mean the same thing.

NDVI scoring (lower NDVI = sparser/more stressed vegetation = higher risk contribution):

    NDVI is None   -> +10
    NDVI < 0.15    -> +25
    NDVI < 0.25    -> +17
    NDVI < 0.35    -> +8
    else           -> +3

**Note:** this genuinely changes the risk numbers for existing counties versus the old 3-factor scoring. That is expected and correct - it reflects real vegetation health now being factored in, not a bug.

Status: **patched successfully** (`risk_engine.py (calculate_agriculture_risk + NDVI)`).

#### AgricultureIntelligenceEngine - NDVI Merge - PATCHED

`backend/disaster/agriculture_engine.py` -> `analyse()` now calls `main_engine.get_sentinel2_ndvi()` alongside the existing `get_gpm_rainfall()` and `get_era5_weather()` calls, merges NDVI per county into each record, and passes it through to `calculate_agriculture_risk()`.

The engine's `satellites` list was also updated:

    ["GPM-IMERG", "ERA5-OpenMeteo"] -> ["GPM-IMERG", "ERA5-OpenMeteo", "Sentinel2-NDVI"]

Status: **patched successfully** (`agriculture_engine.py (analyse + NDVI)`, `agriculture_engine.py (satellites list)`).

#### Background NDVI Warm-Up Thread - PATCHED

`backend/main.py` now starts a daemon thread on FastAPI startup (`@app.on_event("startup")`) that calls `main_engine.get_sentinel2_ndvi()` every 170 minutes, logging `[NDVI Warmup] Refreshing Sentinel-2 NDVI cache...` and `[NDVI Warmup] Done -- mode=..., counties=...` on each cycle.

Status: **patched successfully** (`main.py (threading/time imports)`, `main.py (NDVI warmup thread)`).

### Current Status

**All NDVI wiring patches have been applied.** The reported patch run completed with:

    risk_engine.py (calculate_agriculture_risk + NDVI): patched successfully.
    agriculture_engine.py (analyse + NDVI): patched successfully.
    agriculture_engine.py (satellites list): patched successfully.
    main.py (threading/time imports): patched successfully.
    main.py (NDVI warmup thread): patched successfully.
    ALL NDVI WIRING PATCHES APPLIED.

### Immediate Next Step

The patches have been applied but **not yet confirmed running end-to-end after a server restart**. The remaining verification steps are:

1. Restart the server: `uvicorn backend.main:app --reload --port 8000`.
2. Confirm `[NDVI Warmup] Refreshing Sentinel-2 NDVI cache...` appears in the log at startup.
3. Confirm `[NDVI Warmup] Done -- mode=live, counties=47` appears ~107 seconds later.
4. Confirm `/api/agriculture/live` returns instantly (not blocking ~107s) and includes an `ndvi` value and `ndvi_mode` per county.
5. Spot-check that risk severities for a few counties reflect the new 4-factor scoring (expect changes from the old 3-factor baseline - this is expected, not a bug).

Do not treat this step as optional - the patches were applied by editing source files directly; they have not yet been proven live after a restart.

### Files Involved in NDVI Development

| File | Role |
|---|---|
| `core\connectors\sentinel2\sentinel2_ndvi_connector.py` | Sentinel-2 NDVI connector using Statistical API calls, per-county processing and caching. Confirmed live/working (47/47 counties). |
| `core\engines\main_engine.py` | NDVI connector import, registration and `get_sentinel2_ndvi()` method. Confirmed working. |
| `core\auth\copernicus.py` | Existing Copernicus OAuth2 authentication; reused unchanged. |
| `frontend\static\data\kenya_counties.geojson` | Existing county boundary source; reused unchanged from the GPM workflow. |
| `core\risk_engine.py` | Patched - `calculate_agriculture_risk()` rebalanced to 4 factors including NDVI. |
| `backend\disaster\agriculture_engine.py` | Patched - `analyse()` pulls and merges NDVI per county; `satellites` list updated. |
| `backend\main.py` | Patched - background NDVI cache warm-up thread added on startup. |
| `test_one_county.py` | Superseded - historically contained a stale hardcoded `0.05` resolution; no longer the source of truth. |
| `test_all_counties.py` | Rebuilt with corrected `0.01°` resolution; confirmed 47/47 counties returning real NDVI in 107.1s. |
| *(future)* VIIRS-VI connector | Not started; deferred until Sentinel-2 NDVI is proven live post-restart. |
| *(future)* MODIS-VI connector | Not started; deferred until Sentinel-2 NDVI is proven live post-restart. |

### Agriculture Engine Development Sequence

    Fix test script                                   [DONE]
      -> Confirm real NDVI value for one county        [DONE]
      -> Confirm real NDVI across all 47 counties       [DONE - 107.1s, 47/47]
      -> Extend RiskEngine with NDVI                    [DONE - patched]
      -> Extend AgricultureIntelligenceEngine to merge
         NDVI per county                                [DONE - patched]
      -> Add background cache warm-up (cold-start fix)  [DONE - patched]
      -> Restart server & confirm live end-to-end        [PENDING - next step]
      -> Build VIIRS-VI connector                        [NOT STARTED]
      -> Build MODIS-VI connector                        [NOT STARTED]
      -> Implement multi-source fusion and confidence
         logic                                           [NOT STARTED]
      -> Build live NDVI/risk map layer                  [NOT STARTED]
      -> Build Agriculture risk table UI                 [NOT STARTED]

Only proceed to the next stage after the current stage has been verified.

### Remaining GeoShield Development

After the Agriculture Engine is fully completed:

1. Analytics Engine
2. Reports Engine
3. Alerts Engine
4. AI Engine - final integration

### Important Agriculture Development Rules

- Preserve the Main Engine as the central communication/orchestration architecture.
- Preserve the existing working Agriculture risk and decision logic.
- Do not rebuild the Sentinel-2 NDVI connector unnecessarily.
- Do not treat the stale `test_one_county.py` resolution as a failure of the actual connector.
- Do not begin VIIRS-VI or MODIS-VI implementation until Sentinel-2 NDVI is fully proven live **after the server restart verification step above**.
- Reuse existing Copernicus authentication infrastructure.
- Reuse existing county boundary infrastructure.
- Do not create duplicate acquisition/authentication systems when existing GeoShield infrastructure already provides the required capability.
- Do not modify Copernicus/Sentinel infrastructure unnecessarily.
- Do not remove this Agriculture NDVI status until the Agriculture Engine is officially declared complete.
