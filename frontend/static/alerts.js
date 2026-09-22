(function () {
    "use strict";

    let modalBackdrop, modalTitle, modalBody, clearBtn;
    let initialized = false;
    let cachedActive = [];
    let cachedHistory = [];

    function el(id) {
        return document.getElementById(id);
    }

    function severityClass(sev) {
        return sev ? ("analytics-risk-" + sev) : "";
    }

    function fmtTime(ts) {
        return ts ? new Date(ts * 1000).toLocaleString() : "--";
    }

    function openModal(title, bodyHtml, showClear) {
        modalTitle.textContent = title;
        modalBody.innerHTML = bodyHtml;
        clearBtn.style.display = showClear ? "inline-block" : "none";
        modalBackdrop.classList.add("analytics-modal-open");
    }

    function closeModal() {
        modalBackdrop.classList.remove("analytics-modal-open");
    }

    function renderTable(alerts) {
        if (!alerts.length) {
            return '<p style="opacity:0.7;">No alerts to show.</p>';
        }
        const rows = alerts.map(function (a) {
            let status;
            if (a.resolved) {
                status = "Resolved";
            } else if (a.severity === "High" || a.severity === "Extreme") {
                status = "SMS notified";
            } else {
                status = "Monitoring only";
            }
            return (
                "<tr>" +
                    "<td>" + fmtTime(a.timestamp) + "</td>" +
                    "<td>" + (a.county || "Unknown") + "</td>" +
                    "<td>" + (a.hazard || "").toUpperCase() + "</td>" +
                    '<td class="' + severityClass(a.severity) + '">' + a.severity +
                        (a.previous_severity ? " (was " + a.previous_severity + ")" : "") + "</td>" +
                    "<td>" + (a.reason || "") + "</td>" +
                    "<td>" + status + "</td>" +
                "</tr>"
            );
        }).join("");

        return (
            '<table class="analytics-modal-table">' +
                "<thead><tr><th>Date</th><th>County</th><th>Hazard</th><th>Severity</th><th>Reason</th><th>Status</th></tr></thead>" +
                "<tbody>" + rows + "</tbody>" +
            "</table>"
        );
    }

    function renderActiveSummary(alerts) {
        let rows = '<div class="analytics-stat-row"><span>Currently elevated</span><strong>' + alerts.length + '</strong></div>';
        const bySeverity = {};
        alerts.forEach(function (a) { bySeverity[a.severity] = (bySeverity[a.severity] || 0) + 1; });
        ["Extreme", "High", "Moderate"].forEach(function (sev) {
            if (bySeverity[sev]) {
                rows += '<div class="analytics-stat-row"><span>' + sev + '</span><strong class="' +
                    severityClass(sev) + '">' + bySeverity[sev] + "</strong></div>";
            }
        });
        return rows;
    }

    function renderHistoricalSummary(alerts) {
        return '<div class="analytics-stat-row"><span>Total logged</span><strong>' + alerts.length + '</strong></div>';
    }

    async function fetchJSON(url, options) {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(url + " failed: " + res.status);
        return res.json();
    }

    function loadAll() {
        Promise.all([
            fetchJSON("/api/alerts/active"),
            fetchJSON("/api/alerts?limit=500"),
        ]).then(function (results) {
            cachedActive = results[0].alerts || [];
            cachedHistory = results[1].alerts || [];

            el("alertsActiveSummary").innerHTML = renderActiveSummary(cachedActive);
            el("alertsHistoricalSummary").innerHTML = renderHistoricalSummary(cachedHistory);

            el("alertsActiveCard").onclick = function () {
                openModal("Active Alerts", renderTable(cachedActive), false);
            };
            el("alertsHistoricalCard").onclick = function () {
                openModal("Historical Alerts", renderTable(cachedHistory), true);
            };
        }).catch(function (err) {
            console.error("GeoShield Alerts: load failed", err);
            const activeEl = el("alertsActiveSummary");
            const histEl = el("alertsHistoricalSummary");
            if (activeEl) activeEl.innerHTML = "Unable to reach alerts feed.";
            if (histEl) histEl.innerHTML = "Unable to reach alerts feed.";
        });
    }

    function handleClearHistory() {
        if (!window.confirm("This will permanently delete all Historical Alerts. Active alerts are not affected. Continue?")) {
            return;
        }
        fetchJSON("/api/alerts/clear-history", { method: "POST" }).then(function () {
            closeModal();
            loadAll();
        }).catch(function (err) {
            console.error("GeoShield Alerts: clear history failed", err);
            window.alert("Failed to clear historical alerts. Check the console for details.");
        });
    }

    function init() {
        if (!initialized) {
            modalBackdrop = el("alertsModalBackdrop");
            modalTitle = el("alertsModalTitle");
            modalBody = el("alertsModalBody");
            clearBtn = el("alertsClearHistoryBtn");

            const closeBtn = el("alertsModalCloseBtn");
            if (closeBtn) closeBtn.addEventListener("click", closeModal);
            if (clearBtn) clearBtn.addEventListener("click", handleClearHistory);

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") closeModal();
            });

            initialized = true;
        }
        loadAll();
    }

    function refreshIfVisible() {
        const page = el("geoshieldAlertsPage");
        if (page && page.classList.contains("workspace-page-active")) {
            loadAll();
        }
    }

    window.GeoShieldAlerts = { init: init, refreshIfVisible: refreshIfVisible };
})();
