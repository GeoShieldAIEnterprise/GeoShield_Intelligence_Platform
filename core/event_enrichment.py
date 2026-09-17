from backend.spatial.spatial_engine import SpatialEngine


class EventEnrichmentEngine:

    def __init__(self, data_manager):

        self.spatial = SpatialEngine(data_manager)

    def enrich(self, longitude, latitude):

        county = self.spatial.locate_point(
            longitude,
            latitude
        )

        if county.empty:
            county_name = "Unknown"
        else:
            county_name = county["COUNTY"].iloc[0]

        roads_layer = self.spatial.get_layer("roads")

        if roads_layer is None or roads_layer.empty:
            road_type = "Unavailable"
            road_surface = "Unavailable"
        else:
            road = self.spatial.nearest_road(
                longitude,
                latitude
            )
            road_type = road["RTT_DESCRI"] if "RTT_DESCRI" in road else "Unknown"
            road_surface = road["MED_DESCRI"] if "MED_DESCRI" in road else "Unknown"

        return {

            "longitude": longitude,

            "latitude": latitude,

            "county": county_name,

            "road_type": road_type,

            "road_surface": road_surface

        }
