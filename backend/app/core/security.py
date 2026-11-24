import time
from collections import defaultdict
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding Window In-Memory Rate Limiter.
    Protects API against spamming, scraping, and DoS without requiring external services,
    while ready for Redis distributed rate limiting.
    """
    def __init__(self, app, max_requests: int = 150, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_history = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Exempt health check and docs from strict rate limiting
        if request.url.path in ["/api/v1/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        
        # Clean timestamps older than the window
        timestamps = self.requests_history[client_ip]
        self.requests_history[client_ip] = [t for t in timestamps if now - t < self.window_seconds]
        
        if len(self.requests_history[client_ip]) >= self.max_requests:
            return Response(
                content='{"detail": "Rate limit exceeded. Please slow down your requests."}',
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)}
            )

        self.requests_history[client_ip].append(now)
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Applies OWASP recommended security headers to all responses.
    Prevents clickjacking, MIME-type sniffing, XSS, and restricts iframe embedding.
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        return response
