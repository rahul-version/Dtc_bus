from fastapi import APIRouter, Query
from typing import List, Dict, Any
from backend.app.services.transit_data import DELHI_STOPS

router = APIRouter()

@router.get("/search")
async def search_stops(q: str = Query("", description="Query prefix or keyword for bus stop")):
    """
    Autocomplete / search bus stops in Delhi DTC network.
    """
    query = q.strip().lower()
    results = []
    
    for key, stop in DELHI_STOPS.items():
        if not query or query in key or query in stop["name"].lower() or query in stop["zone"].lower():
            results.append({
                "id": stop["id"],
                "name": stop["name"],
                "lat": stop["lat"],
                "lon": stop["lon"],
                "zone": stop["zone"],
                "is_major_hub": stop["is_major_hub"]
            })
            
    # Sort major hubs first
    results.sort(key=lambda x: (not x["is_major_hub"], x["name"]))
    return {"results": results[:15]}

@router.get("/popular")
async def get_popular_routes():
    """
    Returns popular origin-destination presets for easy one-click testing.
    """
    return {
        "presets": [
            {"from": "Anand Vihar ISBT", "to": "Connaught Place (Shivaji Stadium)", "desc": "Arterial East-to-Central Commute"},
            {"from": "Kashmere Gate ISBT", "to": "AIIMS (Sri Aurobindo Marg)", "desc": "North-to-South Medical Corridor"},
            {"from": "Nehru Place Bus Terminal", "to": "Dhaula Kuan", "desc": "South-to-South-West Ring Corridor"},
            {"from": "Karol Bagh (Gurudwara Road)", "to": "Connaught Place (Shivaji Stadium)", "desc": "West-to-Central Quick Hop"}
        ]
    }
