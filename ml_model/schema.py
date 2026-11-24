"""
Crowdedness Prediction Schema and Data Contracts
Define standard structures for input features and prediction outputs.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class StopStretch(BaseModel):
    from_stop: str = Field(..., description="Boarding stop name")
    to_stop: str = Field(..., description="Alighting stop name")
    distance_km: Optional[float] = Field(default=1.5, description="Distance of stretch in km")
    stop_sequence_index: int = Field(default=0, description="Order of stretch along the trip")

class CrowdingInput(BaseModel):
    route_id: str = Field(..., description="Bus route name (e.g. '8UP', '502', '429')")
    stretches: List[StopStretch] = Field(..., description="Ordered stretches between departure and arrival")
    departure_time: str = Field(..., description="Time of day in HH:MM format (e.g. '18:00')")
    day_of_week: str = Field(default="weekday", description="'weekday', 'saturday', or 'sunday'")
    is_ac: bool = Field(default=False, description="Whether the bus is Air Conditioned (DTC Red/Orange)")
    vehicle_capacity: int = Field(default=65, description="Standard bus capacity (e.g. 35 seats + 30 standing = 65)")

class StretchPrediction(BaseModel):
    from_stop: str
    to_stop: str
    occupancy_ratio: float = Field(..., description="Ratio of estimated passengers to total capacity (0.0 to 1.5+)")
    estimated_passengers: int = Field(..., description="Estimated running count of passengers on board")
    crowding_level: str = Field(..., description="'SEATS_AVAILABLE' | 'STANDING_ROOM' | 'CROWDED' | 'PACKED'")
    crowding_color: str = Field(..., description="Hex color or badge name: green, yellow, orange, red")
    seats_free_estimate: int = Field(default=0, description="Estimated vacant seats")
    confidence: float = Field(default=0.85, description="Statistical confidence (0.0 - 1.0) based on sample depth")

class JourneyCrowdingOutput(BaseModel):
    route_id: str
    overall_crowding_level: str
    overall_occupancy_ratio: float
    crowding_badge_color: str
    stretches: List[StretchPrediction]
    comfort_score: float = Field(..., description="Comfort score between 0 (worst) and 100 (best)")
    commuter_advice: str = Field(..., description="Instant human-readable tip for commuter")
    model_version: str = Field(default="v1.0-custom-ready")
