(function () {
    "use strict";

    const MAP_PAGE = "geoshieldMapPage";
    const INTELLIGENCE_PAGE = "geoshieldIntelligencePage";
    const LIVEMAP_PAGE = "geoshieldLiveMapPage";

    let currentWorkspace = "map";

    function setWorkspace(mode) {

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
    }


    function goToMap() {
        setWorkspace("map");
    }


    function goToIntelligence() {
        setWorkspace("intelligence");
    }


    function updateNavigator() {

        const mapButton =
            document.getElementById(
                "workspaceMapArrow"
            );

        const intelligenceButton =
            document.getElementById(
                "workspaceIntelligenceArrow"
            );

        if (!mapButton || !intelligenceButton) {
            return;
        }

        const isMap =
            currentWorkspace === "map";

        mapButton.disabled = isMap;
        intelligenceButton.disabled = !isMap;

        mapButton.setAttribute(
            "aria-current",
            isMap ? "page" : "false"
        );

        intelligenceButton.setAttribute(
            "aria-current",
            !isMap ? "page" : "false"
        );
    }


    function createNavigator() {

        let nav =
            document.getElementById(
                "workspaceNavigator"
            );

        if (!nav) {

            nav =
                document.createElement("div");

            nav.id =
                "workspaceNavigator";

            nav.className =
                "workspace-navigator";

            nav.innerHTML = `
                <button
                    type="button"
                    id="workspaceMapArrow"
                    class="workspace-nav-arrow"
                    aria-label="Return to Main Map"
                    title="Return to Main Map">
                    ←
                </button>

                <div
                    class="workspace-nav-divider"
                    aria-hidden="true">
                </div>

                <button
                    type="button"
                    id="workspaceIntelligenceArrow"
                    class="workspace-nav-arrow"
                    aria-label="Open Satellite Intelligence"
                    title="Open Satellite Intelligence">
                    →
                </button>
            `;

            document.body.appendChild(nav);
        }


        if (nav.dataset.bound !== "true") {

            nav.addEventListener(
                "click",
                function (event) {

                    const button =
                        event.target.closest(
                            "button"
                        );

                    if (!button ||
                        button.disabled) {
                        return;
                    }

                    if (
                        button.id ===
                        "workspaceMapArrow"
                    ) {
                        goToMap();
                    }

                    if (
                        button.id ===
                        "workspaceIntelligenceArrow"
                    ) {
                        goToIntelligence();
                    }
                }
            );

            nav.dataset.bound = "true";
        }

        updateNavigator();
    }


    function initialize() {

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
    }


    window.GeoShieldWorkspace = {
        initialize,
        goToMap,
        goToIntelligence,
        goToLiveMap,

        getCurrentWorkspace: function () {
            return currentWorkspace;
        }
    };


    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            { once: true }
        );
    } else {
        initialize();
    }

})();

