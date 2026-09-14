// ======================================================
// Controls Module
// ======================================================

function initializeControls() {

    // ----------------------------
    // Search (Nominatim, no external plugin needed)
    // ----------------------------

    const searchBtn = document.getElementById("dashboardSearchBtn");
    const searchInput = document.getElementById("dashboardSearchInput");

    async function dashboardSearchLocation(query) {
        if (!query || !query.trim()) return;
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`);
            const results = await res.json();
            if (!results.length) {
                alert("Location not found: " + query);
                return;
            }
            const { lat, lon } = results[0];
            map.setView([parseFloat(lat), parseFloat(lon)], 12);
        } catch (error) {
            console.error("[Dashboard] search failed:", error);
            alert("Search failed. Check your connection.");
        }
    }

    if (searchBtn) {
        searchBtn.addEventListener("click", () => dashboardSearchLocation(searchInput.value));
    }
    if (searchInput) {
        searchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") dashboardSearchLocation(searchInput.value);
        });
    }

    // ----------------------------
    // Locate Button
    // ----------------------------

    const locateBtn = document.getElementById("locateBtn");

    if (locateBtn) {

        locateBtn.addEventListener("click", function () {

            map.locate({

                setView: true,
                maxZoom: 13

            });

        });

    }

    // ----------------------------
    // Location Found
    // ----------------------------

    map.on("locationfound", function (e) {

        window.currentIncident = {

            lat: e.latitude,
            lng: e.longitude

        };

        L.marker([e.latitude, e.longitude])

            .addTo(map)

            .bindPopup("📍 Current Incident Location")

            .openPopup();

    });

    // ----------------------------
    // Location Error
    // ----------------------------

    map.on("locationerror", function () {

        alert("Unable to access your location.");

    });

}

