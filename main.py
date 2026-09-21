from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import CORSMiddleware

from core.limiter import limiter
from core.storage import close_s3, init_s3
from database.db import close_db, init_db
from core.config import settings
from rag.qdrant_store import init_qdrant_collection
from services.exceptions import ServiceError
from routers.chat import chat
from routers.summaries import summaries



from routers.documents import docs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db(app)
    await init_s3(app)
    init_qdrant_collection()
    yield
    await close_s3(app)
    await close_db(app)

app = FastAPI(
    lifespan=lifespan,
    title="Docmind",
    description="AI document platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ServiceError)
async def service_error_handler(request: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

@app.get("/check")
def check():
    return{"status": "hakuna matata"}


app.include_router(docs)
app.include_router(chat)
app.include_router(summaries)

