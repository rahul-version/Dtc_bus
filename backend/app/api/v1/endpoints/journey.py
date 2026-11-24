from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from backend.app.services.journey_service import journey_service

router = APIRouter()

class JourneyPlanRequest(BaseModel):
    from_stop: str = Field(..., examples=["Anand Vihar ISBT"])
    to_stop: str = Field(..., examples=["Connaught Place"])
    departure_time: str = Field(default="18:00", examples=["18:00"])
    day_of_week: str = Field(default="weekday", examples=["weekday"])
    preference: str = Field(default="balanced", examples=["balanced"]) # 'fastest', 'comfortable', 'balanced'

@router.post("/plan")
async def plan_journey_endpoint(payload: JourneyPlanRequest):
    """
    Plan a journey between two stops with crowdedness-aware ranking.
    """
    try:
        result = journey_service.plan_journey(
            from_stop=payload.from_stop,
            to_stop=payload.to_stop,
            departure_time=payload.departure_time,
            day_of_week=payload.day_of_week,
            preference=payload.preference
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Journey planning error: {str(e)}")

@router.get("/quick")
async def quick_plan(
    from_stop: str = Query(..., examples=["Anand Vihar ISBT"]),
    to_stop: str = Query(..., examples=["Connaught Place"]),
    time: str = Query("18:00"),
    day: str = Query("weekday"),
    pref: str = Query("balanced")
):
    """
    GET shortcut for quick journey lookup.
    """
    return journey_service.plan_journey(
        from_stop=from_stop,
        to_stop=to_stop,
        departure_time=time,
        day_of_week=day,
        preference=pref
    )
