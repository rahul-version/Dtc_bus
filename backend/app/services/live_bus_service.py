"""
Live Bus Tracking Service using Delhi Transport Stack (DTS) Realtime GTFS feed.
Parses VehiclePositions.pb with in-memory caching to support high concurrency.
"""

import time
import math
import requests
from typing import List, Dict, Any, Optional
from google.transit import gtfs_realtime_pb2
from backend.app.core.config import settings

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2.0)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2.0)**2
    return 2.0 * R * math.asin(math.sqrt(a))

class LiveBusService:
    def __init__(self):
        self.cached_feed: Optional[List[Dict[str, Any]]] = None
        self.last_fetch_time: float = 0
        self.cache_ttl: int = settings.CACHE_TTL_SECONDS
        self.api_url = settings.DTS_REALTIME_URL
        self.api_key = settings.DTS_API_KEY

    def _fetch_realtime_feed(self) -> List[Dict[str, Any]]:
        """Fetch and parse live VehiclePositions.pb with TTL caching."""
        now = time.time()
        if self.cached_feed is not None and (now - self.last_fetch_time) < self.cache_ttl:
            return self.cached_feed

        try:
            resp = requests.get(
                self.api_url,
                headers={"x-api-key": self.api_key},
                timeout=8
            )
            if resp.status_code != 200:
                print(f"[LiveBus] DTS API returned status {resp.status_code}")
                return self.cached_feed or []

            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(resp.content)

            vehicles = []
            for entity in feed.entity:
                if entity.HasField("vehicle"):
                    v = entity.vehicle
                    pos = v.position
                    veh_id = v.vehicle.id or entity.id
                    is_electric = "EV" in veh_id.upper()
                    
                    # Convert speed from m/s to km/h if valid
                    speed_kmh = round(pos.speed * 3.6, 1) if pos.speed and pos.speed > 0 else 0.0

                    vehicles.append({
                        "vehicle_id": veh_id,
                        "route_id": v.trip.route_id if v.HasField("trip") else "DTC",
                        "trip_id": v.trip.trip_id if v.HasField("trip") else "",
                        "lat": round(pos.latitude, 5),
                        "lon": round(pos.longitude, 5),
                        "speed_kmh": speed_kmh,
                        "bearing": round(pos.bearing, 1) if pos.bearing else 0.0,
                        "timestamp": v.timestamp if v.timestamp else int(now),
                        "is_electric": is_electric,
                        "bus_type": "Electric Zero-Emission" if is_electric else "Standard DTC CNG"
                    })

            self.cached_feed = vehicles
            self.last_fetch_time = now
            print(f"[LiveBus] Updated live feed: {len(vehicles)} active buses tracked in Delhi.")
            return vehicles

        except Exception as e:
            print(f"[LiveBus] Error fetching realtime feed: {e}")
            return self.cached_feed or []

    def get_fleet_summary(self) -> Dict[str, Any]:
        """Summary of live bus fleet on Delhi streets."""
        vehicles = self._fetch_realtime_feed()
        total = len(vehicles)
        electric_count = sum(1 for v in vehicles if v["is_electric"])
        moving_count = sum(1 for v in vehicles if v["speed_kmh"] > 5.0)
        
        return {
            "source": "Delhi Transport Stack (OTD Realtime GTFS)",
            "total_active_buses": total,
            "electric_buses_count": electric_count,
            "cng_buses_count": total - electric_count,
            "active_moving_buses": moving_count,
            "last_updated_epoch": int(self.last_fetch_time),
            "status": "connected"
        }

    def get_buses_near(self, lat: float, lon: float, radius_km: float = 3.5, limit: int = 25) -> List[Dict[str, Any]]:
        """Find active buses within radius_km of a coordinate."""
        vehicles = self._fetch_realtime_feed()
        nearby = []

        for v in vehicles:
            dist = haversine_km(lat, lon, v["lat"], v["lon"])
            if dist <= radius_km:
                v_copy = dict(v)
                v_copy["distance_km"] = round(dist, 2)
                # Estimated arrival in minutes assuming 18 km/h city speed
                v_copy["eta_mins"] = max(1, round((dist / 18.0) * 60))
                nearby.append(v_copy)

        nearby.sort(key=lambda x: x["distance_km"])
        return nearby[:limit]

    def get_buses_along_corridor(self, route_points: List[List[float]], buffer_km: float = 1.2, limit: int = 20) -> List[Dict[str, Any]]:
        """Find active buses operating along or near the route's coordinates."""
        vehicles = self._fetch_realtime_feed()
        along_corridor = []

        for v in vehicles:
            v_lat, v_lon = v["lat"], v["lon"]
            # Find min distance to any route point
            min_dist = min(haversine_km(v_lat, v_lon, p[0], p[1]) for p in route_points)
            if min_dist <= buffer_km:
                v_copy = dict(v)
                v_copy["distance_to_corridor_km"] = round(min_dist, 2)
                along_corridor.append(v_copy)

        along_corridor.sort(key=lambda x: x["distance_to_corridor_km"])
        return along_corridor[:limit]

live_bus_service = LiveBusService()
