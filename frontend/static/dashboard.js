// ======================================================
// Dashboard Module
// ======================================================

function loadDashboard() {

    const county = window.currentCounty;
    const url = county ? "/api/dashboard?county=" + encodeURIComponent(county) : "/api/dashboard";

    fetch(url)

        .then(response => response.json())

        .then(data => {

            document.getElementById("health").innerText =
                data.system_status ?? "--";

            document.getElementById("weather").innerText =
                data.weather ?? "--";

            document.getElementById("events").innerText =
                data.alerts ?? "--";

            const overallEl = document.getElementById("aiScore");
            const overallRisk = data.overall_risk ?? "--";
            const overallPercent = data.overall_risk_percent;
            overallEl.innerText = (overallPercent != null) ? overallPercent + "%" : "--";
            const overallColors = {
                "Low": "#00b894", "Moderate": "#f1c40f",
                "High": "#e67e22", "Extreme": "#e74c3c"
            };
            overallEl.style.color = overallColors[overallRisk] || "";

            document.getElementById("fireRisk").innerText =
                data.fire_risk ?? "--";

            const now = new Date();

            document.getElementById("lastUpdate").innerText =
                now.toLocaleTimeString();

        })

        .catch(error => {

            console.error(error);

            document.getElementById("health").innerText =
                "Connection Failed";

        });

}
