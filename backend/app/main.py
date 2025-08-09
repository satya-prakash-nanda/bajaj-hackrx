from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import logging
from app.api import router as api_router
from app.config import settings

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for even more detailed logs
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)


app = FastAPI(
    title="LLM Query Retrieval API",
    version="1.0.0",
    description="API to extract and answer queries from insurance, legal, and HR documents using Groq LLMs."
)

# ✅ CORS (allow all for now — restrict in prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔒 Replace with your frontend domain in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Bearer Token Middleware for protected routes
@app.middleware("http")
async def authenticate_request(request: Request, call_next):
    if request.url.path.startswith(settings.API_PREFIX):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"}
            )

        token = auth_header.split("Bearer ")[1].strip()
        if token != settings.BEARER_TOKEN:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid token provided"}
            )

    return await call_next(request)

# ✅ Root route for health check
@app.get("/")
async def root():
    return {
        "message": "🚀 HackRx Backend is running!",
        "docs": "/docs",
        "redoc": "/redoc",
        "api_base": settings.API_PREFIX
    }

# ✅ Register main API routes
app.include_router(api_router, prefix=settings.API_PREFIX)

# ✅ Inject Bearer Auth into Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"  # optional, just cosmetic
        }
    }

    for path in openapi_schema["paths"].values():
        for method in path.values():
            method.setdefault("security", []).append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
