(function () {
    "use strict";

    let modalBackdrop, modalTitle, modalCloseBtn;
    let initialized = false;
    let countiesLoaded = false;

    function el(id) {
        return document.getElementById(id);
    }

    function openModal() {
        modalBackdrop.classList.add("analytics-modal-open");
        populateCountyDropdown();
    }

    function closeModal() {
        modalBackdrop.classList.remove("analytics-modal-open");
    }

    function populateCountyDropdown() {
        const select = el("reportsCountySelect");
        if (!select || countiesLoaded) {
            return;
        }
        fetch("/static/data/kenya_counties.geojson")
            .then(r => r.json())
            .then(data => {
                const names = data.features
                    .map(f => f.properties.COUNTY || f.properties.NAME || f.properties.name)
                    .filter(Boolean)
                    .sort();
                const unique = [...new Set(names)];
                select.innerHTML = "";
                unique.forEach(name => {
                    const opt = document.createElement("option");
                    opt.value = name;
                    opt.textContent = name;
                    select.appendChild(opt);
                });
                countiesLoaded = true;
            })
            .catch(err => {
                console.error("GeoShield Reports: failed to load county list", err);
            });
    }

    function setStatus(message, isError) {
        const status = el("reportsPdfStatus");
        if (!status) {
            return;
        }
        status.textContent = message;
        status.style.color = isError ? "#c62828" : "#2e7d32";
    }

    function downloadPdf() {
        const select = el("reportsCountySelect");
        const btn = el("reportsDownloadBtn");
        const county = select ? select.value : "";

        if (!county) {
            setStatus("Please select a county first.", true);
            return;
        }

        setStatus("Requesting report for " + county + "...", false);

        const downloadUrl = "/api/reports/pdf?county=" + encodeURIComponent(county);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.rel = "noopener";
        a.target = "_blank";
        a.download = "";
        document.body.appendChild(a);
        a.click();
        a.remove();

        setStatus("Download started for " + county + ". Check your browser downloads.", false);
    }

    function init() {
        if (!initialized) {
            modalBackdrop = el("reportsModalBackdrop");
            modalTitle = el("reportsModalTitle");
            modalCloseBtn = el("reportsModalCloseBtn");

            if (modalCloseBtn) {
                modalCloseBtn.addEventListener("click", closeModal);
            }

            document.addEventListener("keydown", function (event) {
                if (event.key === "Escape") closeModal();
            });

            const pdfCard = el("reportsPdfCard");
            if (pdfCard) {
                pdfCard.style.cursor = "pointer";
                pdfCard.addEventListener("click", openModal);
            }

            const btn = el("reportsDownloadBtn");
            if (btn) {
                btn.addEventListener("click", downloadPdf);
            }

            initialized = true;
        }
        console.log("GeoShield Reports workspace initialized.");
    }

    function refreshIfVisible() {
        // No periodic refresh needed; data is generated on demand.
    }

    window.GeoShieldReports = {
        init,
        refreshIfVisible
    };

})();