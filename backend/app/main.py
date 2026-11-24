import sys
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add project root and backend dir to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
for p in [PROJECT_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from backend.app.core.config import settings
from backend.app.core.security import RateLimitMiddleware, SecurityHeadersMiddleware
from backend.app.api.v1.endpoints import journey, stops, crowding, health, live

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="High-performance backend for Crowdedness-Aware Journey Planning in Delhi DTC Bus Network."
)

# 1. OWASP Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Rate Limiting Middleware (150 requests/min per IP)
app.add_middleware(RateLimitMiddleware, max_requests=settings.RATE_LIMIT_REQUESTS_PER_MINUTE, window_seconds=60)

# 3. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler (Prevents stack traces and sensitive information leaks)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again shortly."}
    )

# Include Routers
app.include_router(journey.router, prefix="/api/v1/journey", tags=["Journey Planning"])
app.include_router(stops.router, prefix="/api/v1/stops", tags=["Bus Stops"])
app.include_router(crowding.router, prefix="/api/v1/crowding", tags=["Crowdedness Diagnostics"])
app.include_router(live.router, prefix="/api/v1/live", tags=["Realtime GTFS Live Buses"])
app.include_router(health.router, prefix="/api/v1/health", tags=["System Health"])

@app.get("/")
async def root():
    return {
        "name": "Delhi Transport Stack (DTC) Crowdedness Journey Engine",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
