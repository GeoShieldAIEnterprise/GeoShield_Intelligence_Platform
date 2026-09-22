/*
============================================================
 GeoShield AI Enterprise
 Frontend Configuration
============================================================
*/

window.GeoShieldConfig = {

    apiBase: "",

    endpoints: {

        dashboard: "/dashboard",

        alerts: "/api/alerts",

        county: "/county",

        resources: "/resources",

        sentinelSearch: "/api/sentinel2/search",

        sentinelScene: "/api/sentinel2/scene",

        sentinelNdvi: "/api/sentinel2/ndvi"

    },

    map: {

        defaultCenter: [-0.0236, 37.9062],

        defaultZoom: 6

    },

    sentinel2: {

        cloudCoverMaximum: 30,

        maxResults: 20,

        defaultDaysBack: 30

    },

    getBbox() {

        if (window.map && typeof window.map.getBounds === "function") {

            const bounds = window.map.getBounds();

            return [

                bounds.getWest(),

                bounds.getSouth(),

                bounds.getEast(),

                bounds.getNorth()

            ];

        }

        return [

            33.8,

            -4.7,

            41.9,

            5.1

        ];

    },

    buildUrl(endpoint, params = {}) {

        const base =
            this.apiBase +
            (this.endpoints[endpoint] || endpoint);

        const query = new URLSearchParams();

        Object.keys(params).forEach(key => {

            const value = params[key];

            if (
                value !== undefined &&
                value !== null &&
                value !== ""
            ) {

                query.append(key, value);

            }

        });

        const queryString = query.toString();

        return queryString
            ? `${base}?${queryString}`
            : base;

    }

};

console.log(
    "GeoShield configuration loaded"
);
