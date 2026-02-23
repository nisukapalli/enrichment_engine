from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import workflows, jobs, files
from app.services import sixtyfour_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting server at http://127.0.0.1:8000")
    yield
    print("Shutting down server")
    await sixtyfour_client.close()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Workflow Engine",
        lifespan=lifespan,
    )

    allowed_origins = [
        "http://localhost:3000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(workflows.router)
    app.include_router(jobs.router)
    app.include_router(files.router)

    return app

app = create_app()