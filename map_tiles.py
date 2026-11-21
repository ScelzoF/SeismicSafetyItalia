"""Explicit keyless street tiles, independent of provider-catalog changes."""

import folium

OSM_TILES = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
OSM_ATTRIBUTION = (
    '&copy; <a href="https://www.openstreetmap.org/copyright">'
    "OpenStreetMap</a> contributors"
)


def street_map(location, zoom_start, **kwargs):
    """Build an interactive map without a paid provider or API-key placeholder."""
    map_ = folium.Map(
        location=location, zoom_start=zoom_start, tiles=None, **kwargs
    )
    folium.TileLayer(
        tiles=OSM_TILES,
        attr=OSM_ATTRIBUTION,
        name="OpenStreetMap",
        max_zoom=19,
        control=False,
    ).add_to(map_)
    return map_
