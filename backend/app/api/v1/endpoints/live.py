from fastapi import APIRouter, Query
from typing import List, Dict, Any, Optional
from backend.app.services.live_bus_service import live_bus_service
from backend.app.services.transit_data import DELHI_STOPS

router = APIRouter()

@router.get("/fleet")
async def get_live_fleet_overview():
    """
    Get real-time DTC & DIMTS active bus fleet statistics
    sourced live from Delhi Transport Stack (DTS).
    """
    return live_bus_service.get_fleet_summary()

@router.get("/nearby")
async def get_nearby_live_buses(
    lat: Optional[float] = Query(None, description="Latitude"),
    lon: Optional[float] = Query(None, description="Longitude"),
    stop_name: Optional[str] = Query(None, description="Stop name to look up coordinates"),
    radius_km: float = Query(3.5, description="Search radius in km"),
    limit: int = Query(15, description="Max buses to return")
):
    """
    Returns live buses near a given stop or GPS coordinate.
    """
    search_lat, search_lon = lat, lon

    if (search_lat is None or search_lon is None) and stop_name:
        stop_key = stop_name.strip().lower()
        for k, v in DELHI_STOPS.items():
            if stop_key in k or stop_key in v["name"].lower():
                search_lat, search_lon = v["lat"], v["lon"]
                break

    if search_lat is None or search_lon is None:
        # Default to Central Delhi (Connaught Place)
        search_lat, search_lon = 28.6315, 77.2167

    buses = live_bus_service.get_buses_near(search_lat, search_lon, radius_km, limit)
    return {
        "search_center": {"lat": search_lat, "lon": search_lon},
        "radius_km": radius_km,
        "total_nearby": len(buses),
        "buses": buses
    }
