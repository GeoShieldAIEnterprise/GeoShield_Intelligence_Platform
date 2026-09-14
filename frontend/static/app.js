function initializeSentinel2Safe() {
    try {
        if (
            window.Sentinel2 &&
            typeof window.Sentinel2.init === "function"
        ) {
            window.Sentinel2.init(window.map || null);

            console.log(
                "GeoShield Sentinel-2 frontend initialized."
            );
        } else {
            console.warn(
                "Sentinel-2 module loaded, but init() was not found."
            );
        }
    } catch (error) {
        console.error(
            "Sentinel-2 initialization failed:",
            error
        );
    }
}

console.log(typeof initializeMap);

if (typeof initializeMap === "function") {
    initializeMap();
}

if (typeof initializeControls === "function") {
    initializeControls();
}

if (typeof loadCounties === "function") {
    loadCounties();
}

setInterval(function () {
    if (typeof loadDashboard === "function") {
        loadDashboard();
    }
}, 60000);

setInterval(function () {
    if (typeof loadFireHotspots === "function") {
        loadFireHotspots();
    }
}, 30000);

if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initializeSentinel2Safe,
        { once: true }
    );
} else {
    initializeSentinel2Safe();
}

