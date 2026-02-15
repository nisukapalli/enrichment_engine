from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.workflow_routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Sixtyfour Workflow Engine",
    description="Configure and execute workflows with chainable blocks (Read CSV, Enrich Lead, Find Email, Filter, Save CSV).",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def root():
    return {"message": "Sixtyfour Workflow Engine API", "docs": "/docs"}
