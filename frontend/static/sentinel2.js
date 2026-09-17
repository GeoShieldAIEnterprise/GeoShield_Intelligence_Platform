/*
============================================================
 GeoShield AI Enterprise
 Sentinel-2 Frontend Module
============================================================

Responsibilities:

1. Sentinel-2 scene search
2. Date filtering
3. Cloud-cover filtering
4. Scene list rendering
5. Scene selection
6. NDVI request
7. Safe API error handling
8. Standalone operation
============================================================
*/

window.Sentinel2 = {

    scenes: [],

    selectedScene: null,

    map: null,

    initialized: false,

    init(mapInstance) {

        if (this.initialized) {
            return;
        }

        this.map = mapInstance || window.map || null;

        this.bindEvents();

        this.createProductInterface();

        this.initialized = true;

        this.loadRecentScenes();

        console.log(
            "Sentinel-2 frontend initialized"
        );

    },

    bindEvents() {

        document.addEventListener(
            "click",
            event => {

                const target =
                    event.target.closest(
                        "[data-sentinel-action]"
                    );

                if (!target) {
                    return;
                }

                const action =
                    target.dataset.sentinelAction;

                if (action === "search") {

                    this.searchScenes();

                }

                if (action === "clear") {

                    this.clearSearch();

                }

                if (action === "ndvi") {

                    const sceneId =
                        target.dataset.sceneId;

                    this.requestNdvi(sceneId);

                }

                if (action === "select") {

                    const sceneId =
                        target.dataset.sceneId;

                    this.selectScene(sceneId);

                }

            }
        );

    },    
    createProductInterface() {

        /*
        ----------------------------------------------------------
        EXISTING HTML PRODUCT CONTAINER
        ----------------------------------------------------------

        The Sentinel-2 product interface already exists in
        index.html inside #sentinel2Product.

        DO NOT create another product section.
        DO NOT append anything to .main-content.
        DO NOT create #sentinel2-product.

        This method only binds to the existing Intelligence
        Center container.
        ----------------------------------------------------------
        */

        const product =
            document.getElementById(
                "sentinel2Product"
            );

        if (!product) {

            console.warn(
                "Sentinel-2 product container not found in Intelligence Center."
            );

            return null;
        }

        return product;

    },

    setStatus(text, type = "normal") {

        const element =
            document.querySelector(".sentinel2-status");

        if (!element) {
            return;
        }

        element.innerText = text;

        element.className =
            "sentinel2-status " + type;

    },

    setMessage(text) {

        const element =
            document.querySelector(".sentinel2-message");

        if (element) {

            element.innerText = text;

        }

    },

    getSearchParameters() {

        const dateFrom =
            document.getElementById(
                "sentinel-date-from"
            );

        const dateTo =
            document.getElementById(
                "sentinel-date-to"
            );

        const cloud =
            document.getElementById(
                "sentinel-cloud"
            );

        const bbox =
            window.GeoShieldConfig.getBbox();

        return {

            bbox: bbox.join(","),

            date_from:
                dateFrom?.value || "",

            date_to:
                dateTo?.value || "",

            cloud_cover:
                cloud?.value || 30,

            limit:
                window.GeoShieldConfig
                    .sentinel2
                    .maxResults

        };

    },

    async searchScenes() {

        this.setStatus(
            "SEARCHING",
            "loading"
        );

        this.setMessage(
            "Querying Sentinel-2 catalogue..."
        );

        const params =
            this.getSearchParameters();

        try {

            const url =
                window.GeoShieldConfig.buildUrl(
                    "sentinelSearch",
                    params
                );

            const response =
                await fetch(url);

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }

            const data =
                await response.json();

            this.scenes =
                this.extractScenes(data);

            this.renderScenes();

            this.setStatus(
                "ONLINE",
                "success"
            );

            this.setMessage(
                `${this.scenes.length} Sentinel-2 scene(s) found.`
            );

        } catch (error) {

            console.error(
                "Sentinel-2 search error:",
                error
            );

            this.setStatus(
                "API ERROR",
                "error"
            );

            this.setMessage(
                "Sentinel-2 service is unavailable or returned an error."
            );

            this.renderEmptyState();

        }

    },

    async loadRecentScenes() {

        const today =
            new Date();

        const from =
            new Date(today);

        from.setDate(
            today.getDate() -
            window.GeoShieldConfig
                .sentinel2
                .defaultDaysBack
        );

        const dateFrom =
            document.getElementById(
                "sentinel-date-from"
            );

        const dateTo =
            document.getElementById(
                "sentinel-date-to"
            );

        if (dateFrom) {

            dateFrom.value =
                from.toISOString()
                    .slice(0, 10);

        }

        if (dateTo) {

            dateTo.value =
                today.toISOString()
                    .slice(0, 10);

        }

        await this.searchScenes();

    },

    extractScenes(data) {

        if (Array.isArray(data)) {
            return data;
        }

        if (Array.isArray(data.scenes)) {
            return data.scenes;
        }

        if (Array.isArray(data.features)) {

            return data.features.map(
                feature => {

                    return {

                        ...feature,

                        ...(feature.properties || {})

                    };

                }
            );

        }

        if (
            data.data &&
            Array.isArray(data.data)
        ) {

            return data.data;

        }

        return [];

    },

    renderScenes() {

        const container =
            document.getElementById(
                "sentinel2-results"
            );

        if (!container) {
            return;
        }

        if (!this.scenes.length) {

            this.renderEmptyState();

            return;

        }

        container.innerHTML =
            this.scenes.map(
                scene =>
                    this.buildSceneCard(scene)
            ).join("");

    },

    renderEmptyState() {

        const container =
            document.getElementById(
                "sentinel2-results"
            );

        if (!container) {
            return;
        }

        container.innerHTML = `

            <div class="sentinel2-empty">

                <strong>
                    No Sentinel-2 scenes found
                </strong>

                <span>
                    Adjust the date,
                    cloud-cover or map extent.
                </span>

            </div>

        `;

    },

    buildSceneCard(scene) {

        const id =
            this.getSceneId(scene);

        const date =
            this.getSceneDate(scene);

        const cloud =
            this.getCloudCover(scene);

        const platform =
            scene.platform ||
            scene.mission ||
            "Sentinel-2";

        const product =
            scene.productType ||
            scene.product_type ||
            scene.processingLevel ||
            "MSIL2A";

        return `

            <article
                class="sentinel2-card"
                data-scene="${this.escape(id)}">

                <div class="sentinel2-card-top">

                    <div>

                        <span
                            class="sentinel2-platform">
                            ${this.escape(platform)}
                        </span>

                        <h3>
                            ${this.escape(id)}
                        </h3>

                    </div>

                    <span
                        class="sentinel2-cloud">
                        ${cloud}%
                    </span>

                </div>

                <div class="sentinel2-meta">

                    <span>
                        DATE
                        <strong>
                            ${this.escape(date)}
                        </strong>
                    </span>

                    <span>
                        PRODUCT
                        <strong>
                            ${this.escape(product)}
                        </strong>
                    </span>

                </div>

                <div class="sentinel2-actions">

                    <button
                        type="button"
                        class="sentinel2-button"
                        data-sentinel-action="select"
                        data-scene-id="${this.escape(id)}">
                        SELECT
                    </button>

                    <button
                        type="button"
                        class="sentinel2-button primary"
                        data-sentinel-action="ndvi"
                        data-scene-id="${this.escape(id)}">
                        CALCULATE NDVI
                    </button>

                </div>

            </article>

        `;

    },

    getSceneId(scene) {

        return String(
            scene.id ||
            scene.scene_id ||
            scene.name ||
            scene.productIdentifier ||
            "unknown-scene"
        );

    },

    getSceneDate(scene) {

        const value =
            scene.datetime ||
            scene.date ||
            scene.sensing_time ||
            scene.start_datetime ||
            "";

        if (!value) {
            return "—";
        }

        return String(value).slice(0, 10);

    },

    getCloudCover(scene) {

        const value =
            scene.cloud_cover ??
            scene.cloudCover ??
            scene["eo:cloud_cover"] ??
            scene.cloud_percentage ??
            0;

        const number =
            Number(value);

        if (Number.isNaN(number)) {
            return "—";
        }

        return number.toFixed(1);

    },

    selectScene(sceneId) {

        const scene =
            this.scenes.find(
                item =>
                    this.getSceneId(item) ===
                    sceneId
            );

        if (!scene) {
            return;
        }

        this.selectedScene =
            scene;

        document
            .querySelectorAll(
                ".sentinel2-card"
            )
            .forEach(card => {

                card.classList.remove(
                    "selected"
                );

            });

        const selected =
            document.querySelector(
                `[data-scene="${CSS.escape(sceneId)}"]`
            );

        if (selected) {

            selected.classList.add(
                "selected"
            );

        }

        this.setMessage(
            `Selected Sentinel-2 scene: ${sceneId}`
        );

        console.log(
            "Selected Sentinel-2 scene:",
            scene
        );

    },

    async requestNdvi(sceneId) {

        this.selectScene(sceneId);

        this.setStatus(
            "PROCESSING",
            "loading"
        );

        this.setMessage(
            "Submitting NDVI processing request..."
        );

        try {

            const url =
                window.GeoShieldConfig.buildUrl(
                    "sentinelNdvi"
                );

            const response =
                await fetch(
                    url,
                    {

                        method: "POST",

                        headers: {

                            "Content-Type":
                                "application/json"

                        },

                        body: JSON.stringify({

                            scene_id:
                                sceneId

                        })

                    }
                );

            if (!response.ok) {

                throw new Error(
                    `HTTP ${response.status}`
                );

            }

            const data =
                await response.json();

            this.setStatus(
                "NDVI READY",
                "success"
            );

            this.setMessage(
                "NDVI processing request completed."
            );

            console.log(
                "NDVI response:",
                data
            );

        } catch (error) {

            console.error(
                "NDVI request error:",
                error
            );

            this.setStatus(
                "PROCESSING ERROR",
                "error"
            );

            this.setMessage(
                "NDVI processing endpoint is unavailable."
            );

        }

    },

    escape(value) {

        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");

    },

    clearSearch() {

        const from =
            document.getElementById(
                "sentinel-date-from"
            );

        const to =
            document.getElementById(
                "sentinel-date-to"
            );

        const cloud =
            document.getElementById(
                "sentinel-cloud"
            );

        if (from) {
            from.value = "";
        }

        if (to) {
            to.value = "";
        }

        if (cloud) {
            cloud.value = 30;
        }

        this.loadRecentScenes();

    }

};

document.addEventListener(
    "DOMContentLoaded",
    function () {

        if (
            window.Sentinel2 &&
            typeof window.Sentinel2.init ===
            "function"
        ) {

            window.Sentinel2.init(
                window.map || null
            );

        }

    }
);

