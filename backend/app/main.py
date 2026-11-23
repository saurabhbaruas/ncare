"""App entry point: creates the FastAPI app, wires the routers and the error handling."""
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.deps import verify_api_key
from app.limiter import limiter
from app.logger import logger
from app.routers import auth, patients, users
from app.seed import seed


@asynccontextmanager
async def lifespan(app: FastAPI):
    # on startup: create the tables and load demo data if the DB is empty
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
    logger.info("Ncare API started")
    yield


app = FastAPI(title="Ncare API", lifespan=lifespan,
              docs_url="/api/docs", openapi_url="/api/openapi.json")
app.state.limiter = limiter

app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS,
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def log_and_secure(request: Request, call_next):
    """Logs each request and adds a few basic security headers."""
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# ---------- error handling: the frontend always gets {"detail": ...} ----------

@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    # show the first problem in plain words instead of pydantic's long list
    message = exc.errors()[0].get("msg", "Invalid input").replace("Value error, ", "")
    return JSONResponse(status_code=422, content={"detail": message})


@app.exception_handler(RateLimitExceeded)
async def too_many_requests(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Too many attempts. Please wait a minute and try again."})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception):
    # last safety net: log the full traceback, but never leak it to the user
    logger.exception(f"Unhandled error on {request.method} {request.url.path}")
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side."})


# every router below needs the API key (the /api/health check stays open)
protected = [Depends(verify_api_key)]
app.include_router(auth.router, prefix="/api", dependencies=protected)
app.include_router(users.router, prefix="/api", dependencies=protected)
app.include_router(patients.router, prefix="/api", dependencies=protected)


@app.get("/api/health")
def health():
    return {"status": "ok"}
