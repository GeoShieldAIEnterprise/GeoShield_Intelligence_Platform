/* GeoShield OS - Sentinel-2 Map Layer Handler */
document.addEventListener("DOMContentLoaded", () => {
    console.log("Sentinel-2 map layer script loaded successfully.");
    if (window.initSentinel2Map) {
        window.initSentinel2Map('map');
    }
});
