from core.connectors.sentinel2.sentinel2_ndvi_connector import (
    STATISTICS_URL,
    NDVI_EVALSCRIPT,
    MAX_CLOUD_COVERAGE,
    NDVI_RESOLUTION_DEG,
    _curl_post_json,
)
from core.auth.copernicus import CopernicusAuthManager
import geopandas as gpd
from datetime import datetime, timedelta, timezone

auth = CopernicusAuthManager()
token = auth.get_token()

counties = gpd.read_file('frontend/static/data/kenya_counties.geojson')
row = counties.iloc[0]
name = row.get('COUNTY') or row.get('NAME') or row.get('name')
geometry = row.geometry.__geo_interface__

date_to = datetime.now(timezone.utc)
date_from = date_to - timedelta(days=14)

payload = {
    'input': {
        'bounds': {'geometry': geometry, 'properties': {'crs': 'http://www.opengis.net/def/crs/EPSG/0/4326'}},
        'data': [{'type': 'sentinel-2-l2a', 'dataFilter': {'maxCloudCoverage': MAX_CLOUD_COVERAGE}}],
    },
    'aggregation': {
        'timeRange': {'from': date_from.strftime('%Y-%m-%dT%H:%M:%SZ'), 'to': date_to.strftime('%Y-%m-%dT%H:%M:%SZ')},
        'aggregationInterval': {'of': 'P14D'},
        'evalscript': NDVI_EVALSCRIPT,
        'resx': NDVI_RESOLUTION_DEG,
        'resy': NDVI_RESOLUTION_DEG,
    },
}

print('Resolution used (degrees):', NDVI_RESOLUTION_DEG)
ok, text = _curl_post_json(STATISTICS_URL, token, payload, 45)
print('County:', name)
print('curl succeeded:', ok)
print('RAW RESPONSE:', text[:3000])
