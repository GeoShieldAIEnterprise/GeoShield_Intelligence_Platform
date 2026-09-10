from pathlib import Path

path = Path("frontend/static/workspace-nav.js")
src = path.read_text(encoding="utf-8-sig")
original = src

old = '''    const MAP_PAGE = "geoshieldMapPage";
    const INTELLIGENCE_PAGE = "geoshieldIntelligencePage";

    let currentWorkspace = "map";'''

new = '''    const MAP_PAGE = "geoshieldMapPage";
    const INTELLIGENCE_PAGE = "geoshieldIntelligencePage";
    const LIVEMAP_PAGE = "geoshieldLiveMapPage";

    let currentWorkspace = "map";'''

if old not in src:
    raise SystemExit("ERROR: constants block not found -- printing file:\n" + src)
src = src.replace(old, new)

old2 = '''    function setWorkspace(mode) {

        const mapPage = document.getElementById(MAP_PAGE);
        const intelligencePage =
            document.getElementById(INTELLIGENCE_PAGE);

        if (!mapPage || !intelligencePage) {
            console.error(
                "GeoShield: workspace pages not found."
            );
            return;
        }

        currentWorkspace =
            mode === "intelligence"
                ? "intelligence"
                : "map";

        const showMap =
            currentWorkspace === "map";

        mapPage.classList.toggle(
            "workspace-page-active",
            showMap
        );

        intelligencePage.classList.toggle(
            "workspace-page-active",
            !showMap
        );

        document.body.classList.toggle(
            "geoshield-map-mode",
            showMap
        );

        document.body.classList.toggle(
            "geoshield-intelligence-mode",
            !showMap
        );

        updateNavigator();

        /*
         * Leaflet may need to recalculate its dimensions
         * after its containing workspace becomes visible.
         */
        if (showMap) {
            window.dispatchEvent(
                new Event("resize")
            );
        }

        console.log(
            "GeoShield workspace:",
            currentWorkspace.toUpperCase()
        );
    }'''

new2 = '''    function setWorkspace(mode) {

        const mapPage = document.getElementById(MAP_PAGE);
        const intelligencePage =
            document.getElementById(INTELLIGENCE_PAGE);
        const liveMapPage =
            document.getElementById(LIVEMAP_PAGE);

        if (!mapPage || !intelligencePage) {
            console.error(
                "GeoShield: workspace pages not found."
            );
            return;
        }

        currentWorkspace = mode === "intelligence"
            ? "intelligence"
            : mode === "livemap"
                ? "livemap"
                : "map";

        const showMap = currentWorkspace === "map";
        const showLiveMap = currentWorkspace === "livemap";
        const showIntelligence = currentWorkspace === "intelligence";

        mapPage.classList.toggle("workspace-page-active", showMap);
        intelligencePage.classList.toggle("workspace-page-active", showIntelligence);

        if (liveMapPage) {
            liveMapPage.classList.toggle("workspace-page-active", showLiveMap);
        }

        document.body.classList.toggle("geoshield-map-mode", showMap);
        document.body.classList.toggle("geoshield-intelligence-mode", showIntelligence);
        document.body.classList.toggle("geoshield-livemap-mode", showLiveMap);

        updateNavigator();

        if (showMap) {
            window.dispatchEvent(new Event("resize"));
        }

        if (showLiveMap) {
            if (window.GeoShieldLiveMap) {
                window.GeoShieldLiveMap.init();
                window.GeoShieldLiveMap.refreshIfVisible();
            }
        }

        console.log(
            "GeoShield workspace:",
            currentWorkspace.toUpperCase()
        );
    }


    function goToLiveMap() {
        setWorkspace("livemap");
    }'''

if old2 not in src:
    raise SystemExit("ERROR: setWorkspace function not found -- printing file:\n" + src)
src = src.replace(old2, new2)

old3 = '''    function initialize() {

        createNavigator();

        setWorkspace("map");

        console.log(
            "GeoShield Workspace Navigation READY"
        );
    }'''

new3 = '''    function initialize() {

        createNavigator();

        setWorkspace("map");

        const liveMapLink = document.getElementById("navLiveMap");
        if (liveMapLink) {
            liveMapLink.addEventListener("click", goToLiveMap);
        }

        const closeBtn = document.getElementById("liveMapCloseBtn");
        if (closeBtn) {
            closeBtn.addEventListener("click", goToMap);
        }

        console.log(
            "GeoShield Workspace Navigation READY"
        );
    }'''

if old3 not in src:
    raise SystemExit("ERROR: initialize function not found -- printing file:\n" + src)
src = src.replace(old3, new3)

old4 = '''    window.GeoShieldWorkspace = {
        initialize,
        goToMap,
        goToIntelligence,

        getCurrentWorkspace: function () {
            return currentWorkspace;
        }
    };'''

new4 = '''    window.GeoShieldWorkspace = {
        initialize,
        goToMap,
        goToIntelligence,
        goToLiveMap,

        getCurrentWorkspace: function () {
            return currentWorkspace;
        }
    };'''

if old4 not in src:
    raise SystemExit("ERROR: window.GeoShieldWorkspace export not found -- printing file:\n" + src)
src = src.replace(old4, new4)

if src == original:
    print("No changes were necessary (already patched?).")
else:
    path.write_text(src, encoding="utf-8", newline="\n")
    print("workspace-nav.js patched -- Live Map wired into sidebar link and X close button.")
