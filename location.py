"""Browser geolocation helper for Arjun Field.

Keeps the existing streamlit-geolocation dependency and provides the
parse_location() helper expected by app.py.
"""

from typing import Any, Optional, Tuple

from streamlit_geolocation import streamlit_geolocation


LocationTuple = Tuple[float, float, float]


def get_location(active: bool = False) -> Any:
    """Render the browser location control and return its raw result.

    ``streamlit-geolocation`` returns a dict containing latitude, longitude,
    accuracy, and possibly an error field.  The raw object is kept here so
    callers can decide how to display or store errors.
    """
    try:
        return streamlit_geolocation()
    except Exception as exc:
        return {"error": str(exc)}


def parse_location(value: Any) -> Optional[LocationTuple]:
    """Convert a raw geolocation result into (latitude, longitude, accuracy).

    Returns None when a valid GPS fix is not available.
    """
    if value is None:
        return None

    # Already-normalized tuple/list: (lat, lon, accuracy)
    if isinstance(value, (tuple, list)) and len(value) >= 2:
        try:
            lat = float(value[0])
            lon = float(value[1])
            accuracy = float(value[2]) if len(value) > 2 and value[2] is not None else 0.0
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon, max(0.0, accuracy)
        except (TypeError, ValueError):
            return None

    if not isinstance(value, dict):
        return None

    # Component may return an error object or partial result.
    if value.get("error"):
        return None

    try:
        lat = value.get("latitude")
        lon = value.get("longitude")
        accuracy = value.get("accuracy", 0)

        if lat is None or lon is None:
            # Also accept a navigator-style nested shape if one is returned.
            coords = value.get("coords")
            if isinstance(coords, dict):
                lat = coords.get("latitude")
                lon = coords.get("longitude")
                accuracy = coords.get("accuracy", 0)

        if lat is None or lon is None:
            return None

        lat = float(lat)
        lon = float(lon)
        accuracy = float(accuracy or 0)

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None

        return lat, lon, max(0.0, accuracy)
    except (TypeError, ValueError):
        return None