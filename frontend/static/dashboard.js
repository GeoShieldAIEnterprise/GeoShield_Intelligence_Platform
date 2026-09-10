// ======================================================
// Dashboard Module
// ======================================================

function loadDashboard() {

    fetch("/api/dashboard")

        .then(response => response.json())

        .then(data => {

            document.getElementById("health").innerText =
                data.system_status ?? "--";

            document.getElementById("weather").innerText =
                data.weather ?? "--";

            document.getElementById("events").innerText =
                data.alerts ?? "--";

            document.getElementById("aiScore").innerText =
                (data.ai_risk ?? 0) + "%";

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
