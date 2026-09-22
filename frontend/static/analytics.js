(function () {
    "use strict";

    let modalBackdrop, modalTitle, modalBody;
    let initialized = false;
    let activeChart = null;

    const RISK_COLORS = {
        "Low": "#2ecc71",
        "Moderate": "#ffd400",
        "High": "#ff8c00",
        "Extreme": "#ff3b30",
    };

    const RISK_ORDER = ["Low", "Moderate", "High", "Extreme"];

    const LEGEND_HTML = '<div class="analytics-chart-legend">' +
        RISK_ORDER.map(function (label) {
            return '<div class="analytics-chart-legend-item"><span class="analytics-chart-legend-swatch" style="background:' + RISK_COLORS[label] + '"></span>' + label + '</div>';
        }).join("") +
        '</div>';

    const barLabelPlugin = {
        id: "barLabelPlugin",
        afterDatasetsDraw: function (chart) {
            const orientation = chart.options.plugins.barLabelPlugin && chart.options.plugins.barLabelPlugin.orientation;
            if (!orientation) return;
            const labels = chart.options.plugins.barLabelPlugin.labels || [];
            const ctx = chart.ctx;
            const meta = chart.getDatasetMeta(0);

            ctx.save();
            ctx.font = "600 11px Arial";
            ctx.fillStyle = "#e2e8f0";

            meta.data.forEach(function (bar, i) {
                const text = labels[i];
                if (!text) return;
                if (orientation === "vertical") {
                    ctx.textAlign = "center";
                    ctx.fillText(text, bar.x, bar.y - 8);
                } else {
                    ctx.textAlign = "left";
                    ctx.fillText(text, bar.x + 6, bar.y + 4);
                }
            });
            ctx.restore();
        },
    };

    function el(id) {
        return document.getElementById(id);
    }

    function destroyActiveChart() {
        if (activeChart) {
            activeChart.destroy();
            activeChart = null;
        }
    }

    function openModal(title, bodyHtml, drawFn) {
        modalTitle.textContent = title;
        modalBody.innerHTML = bodyHtml;
        modalBackdrop.classList.add("analytics-modal-open");
        destroyActiveChart();
        if (drawFn) {
            requestAnimationFrame(function () {
                activeChart = drawFn();
            });
        }
    }

    function closeModal() {
        modalBackdrop.classList.remove("analytics-modal-open");
        destroyActiveChart();
    }

    function riskClass(risk) {
        return risk ? ("analytics-risk-" + risk) : "";
    }

    async function fetchJSON(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(url + " failed: " + res.status);
        return res.json();
    }

    function renderEngineSummary(data) {
        const engines = data.engines || [];
        return engines.map(function (e) {
            return '<div class="analytics-stat-row"><span>' + e.engine + '</span><strong class="' + riskClass(e.risk_level) + '">' + (e.risk_level || "--") + '</strong></div>';
        }).join("") || "No engines registered.";
    }

    function drawEngineChart(data) {
        const engines = data.engines || [];
        const labels = engines.map(function (e) { return e.engine; });
        const riskLabels = engines.map(function (e) { return e.risk_level || "Low"; });
        const values = engines.map(function (e) {
            const rank = { "Low": 0, "Moderate": 1, "High": 2, "Extreme": 3 };
            return rank[e.risk_level] != null ? rank[e.risk_level] : 0;
        });
        const colors = engines.map(function (e) { return RISK_COLORS[e.risk_level] || "#64748b"; });

        const canvas = el("analyticsChartCanvas");
        return new Chart(canvas, {
            type: "bar",
            plugins: [barLabelPlugin],
            data: {
                labels: labels,
                datasets: [{
                    label: "Severity Rank",
                    data: values,
                    backgroundColor: colors,
                    minBarLength: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: { padding: { top: 24 } },
                scales: {
                    y: {
                        min: 0, max: 3, ticks: { stepSize: 1, callback: function (v) { return RISK_ORDER[v]; }, color: "#94a3b8" },
                        grid: { color: "#1e293b" },
                        title: { display: true, text: "Current Severity", color: "#94a3b8" },
                    },
                    x: {
                        ticks: { color: "#e2e8f0" }, grid: { display: false },
                        title: { display: true, text: "Hazard Engine", color: "#94a3b8" },
                    },
                },
                plugins: {
                    legend: { display: false },
                    barLabelPlugin: { orientation: "vertical", labels: riskLabels },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return engines[ctx.dataIndex].risk_level || "Low";
                            },
                        },
                    },
                },
            },
        });
    }

    function renderCountySummary(data) {
        const counties = data.counties || [];
        const withRisk = counties.filter(function (c) { return c.overall_risk; });
        const extreme = withRisk.filter(function (c) { return c.overall_risk === "Extreme" || c.overall_risk === "High"; }).length;
        return '<div class="analytics-stat-row"><span>Counties reporting</span><strong>' + withRisk.length + ' / ' + counties.length + '</strong></div>' +
               '<div class="analytics-stat-row"><span>High/Extreme risk</span><strong class="analytics-risk-High">' + extreme + '</strong></div>';
    }

    function drawCountyChart(data) {
        const counties = (data.counties || []).slice().sort(function (a, b) {
            return (b.mean_rank || 0) - (a.mean_rank || 0);
        });
        const labels = counties.map(function (c) { return c.county; });
        const riskLabels = counties.map(function (c) { return c.overall_risk || "No data"; });
        const values = counties.map(function (c) { return c.mean_rank != null ? c.mean_rank : 0; });
        const colors = counties.map(function (c) { return RISK_COLORS[c.overall_risk] || "#64748b"; });

        const container = el("analyticsChartContainer");
        if (container) {
            container.style.height = (labels.length * 26 + 60) + "px";
        }

        const canvas = el("analyticsChartCanvas");
        return new Chart(canvas, {
            type: "bar",
            plugins: [barLabelPlugin],
            data: {
                labels: labels,
                datasets: [{
                    label: "Overall Risk",
                    data: values,
                    backgroundColor: colors,
                    minBarLength: 6,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: "y",
                scales: {
                    x: {
                        min: 0, max: 3, ticks: { stepSize: 1, callback: function (v) { return RISK_ORDER[v]; }, color: "#94a3b8" },
                        grid: { color: "#1e293b" },
                        title: { display: true, text: "Overall Risk (mean across reporting engines)", color: "#94a3b8" },
                    },
                    y: {
                        ticks: { autoSkip: false, color: "#e2e8f0" },
                        grid: { display: false },
                        title: { display: true, text: "County", color: "#94a3b8" },
                    },
                },
                plugins: {
                    legend: { display: false },
                    barLabelPlugin: { orientation: "horizontal", labels: riskLabels },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return counties[ctx.dataIndex].overall_risk || "No data";
                            },
                        },
                    },
                },
            },
        });
    }

    function renderSatelliteSummary(data) {
        const sats = data.satellites || [];
        const live = sats.filter(function (s) { return s.mode === "live"; }).length;
        return '<div class="analytics-stat-row"><span>Live connectors</span><strong>' + live + ' / ' + sats.length + '</strong></div>' +
               '<div class="analytics-stat-row"><span>Total tracked</span><strong>' + sats.length + '</strong></div>';
    }

    function drawSatelliteChart(data) {
        const sats = data.satellites || [];
        const live = sats.filter(function (s) { return s.mode === "live"; }).length;
        const mock = sats.filter(function (s) { return s.mode === "mock"; }).length;
        const other = sats.length - live - mock;

        const canvas = el("analyticsChartCanvas");
        return new Chart(canvas, {
            type: "doughnut",
            data: {
                labels: ["Live (" + live + ")", "Mock (" + mock + ")", "Unknown (" + other + ")"],
                datasets: [{
                    data: [live, mock, other],
                    backgroundColor: ["#2ecc71", "#ff8c00", "#64748b"],
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { color: "#e2e8f0" } },
                },
            },
        });
    }

    function renderHealthSummary(data) {
        return '<div class="analytics-stat-row"><span>Status</span><strong>' + (data.status || "--") + '</strong></div>' +
               '<div class="analytics-stat-row"><span>Live connectors</span><strong>' + data.live_connectors + '</strong></div>' +
               '<div class="analytics-stat-row"><span>Registered engines</span><strong>' + data.registered_engine_count + '</strong></div>';
    }

    function renderHealthModal(data) {
        let tiles = Object.keys(data).map(function (key) {
            let value = data[key];
            if (Array.isArray(value)) value = value.join(", ");
            return '<div class="analytics-stat-row"><span>' + key + '</span><strong>' + value + '</strong></div>';
        }).join("");
        return '<div class="analytics-card-body" style="font-size:15px;">' + tiles + '</div>';
    }

    function chartHtml(description, withLegend) {
        return '<p class="analytics-chart-description">' + description + '</p>' +
               '<div id="analyticsChartContainer" class="analytics-chart-container"><canvas id="analyticsChartCanvas"></canvas></div>' +
               (withLegend ? LEGEND_HTML : "");
    }

    async function loadAll() {
        try {
            const results = await Promise.all([
                fetchJSON("/api/analytics/engines"),
                fetchJSON("/api/analytics/counties"),
                fetchJSON("/api/analytics/satellites"),
                fetchJSON("/api/analytics/health"),
            ]);
            const engines = results[0];
            const counties = results[1];
            const satellites = results[2];
            const health = results[3];

            el("analyticsEngineList").innerHTML = renderEngineSummary(engines);
            el("analyticsCountyList").innerHTML = renderCountySummary(counties);
            el("analyticsSatelliteList").innerHTML = renderSatelliteSummary(satellites);
            el("analyticsHealthList").innerHTML = renderHealthSummary(health);

            const sceneInfo = el("analyticsSceneInfo");
            if (sceneInfo) {
                sceneInfo.textContent = "Live cross-engine analytics -- updated " + new Date().toLocaleTimeString();
            }

            el("analyticsEngineCard").onclick = function () {
                openModal(
                    "Engine Analytics",
                    chartHtml(
                        "Each bar shows the current risk level reported by one hazard engine, based on live satellite and connector data. Bar height and color both indicate severity: green = Low, yellow = Moderate, orange = High, red = Extreme. Hover a bar for the exact risk level.",
                        true
                    ),
                    function () { return drawEngineChart(engines); }
                );
            };
            el("analyticsCountyCard").onclick = function () {
                openModal(
                    "47 Counties",
                    chartHtml(
                        "Each bar shows one county's Overall Risk -- the average severity across every hazard engine currently reporting data for that county (Earthquake, Agriculture, Fire, and others once registered). Longer, redder bars mean higher combined risk right now. Counties are sorted highest-risk first.",
                        true
                    ),
                    function () { return drawCountyChart(counties); }
                );
            };
            el("analyticsSatelliteCard").onclick = function () {
                openModal(
                    "Satellite Analytics",
                    chartHtml(
                        "This shows how many of GeoShield's satellite/data connectors are currently returning live data versus falling back to mock placeholder data. 'Live' means real-time data is flowing from the actual source (e.g. NASA FIRMS, USGS, Copernicus); 'Mock' means that connector's live source is unavailable right now and a placeholder is being shown instead.",
                        false
                    ),
                    function () { return drawSatelliteChart(satellites); }
                );
            };
            el("analyticsHealthCard").onclick = function () {
                openModal("GeoShield Health", renderHealthModal(health), null);
            };

        } catch (error) {
            console.error("[Analytics] load failed:", error);
            const sceneInfo = el("analyticsSceneInfo");
            if (sceneInfo) sceneInfo.textContent = "Failed to load analytics data.";
        }
    }

    function init() {
        if (!initialized) {
            modalBackdrop = el("analyticsModalBackdrop");
            modalTitle = el("analyticsModalTitle");
            modalBody = el("analyticsModalBody");

            const closeBtn = el("analyticsModalCloseBtn");
            if (closeBtn) closeBtn.addEventListener("click", closeModal);

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") closeModal();
            });

            initialized = true;
        }
        loadAll();
    }

    function refreshIfVisible() {
        const page = el("geoshieldAnalyticsPage");
        if (page && page.classList.contains("workspace-page-active")) {
            loadAll();
        }
    }

    window.GeoShieldAnalytics = { init: init, refreshIfVisible: refreshIfVisible };
})();
