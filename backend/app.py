import os
import sys
from contextlib import asynccontextmanager
from fastapi import BackgroundTasks

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from router import (
    handle_completion,
    list_models,
    get_stats,
    update_routing_config,
    CompletionRequest,
)
from providers import get_provider
from models.registry import MODEL_REGISTRY


ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting LLM Cost Autopilot...")
    for provider_name in {"openai", "anthropic", "ollama"}:
        try:
            provider = get_provider(provider_name)
            healthy = provider.health_check()
            print(f"  {provider_name}: {'OK' if healthy else 'NOT CONFIGURED'}")
        except Exception as e:
            print(f"  {provider_name}: ERROR - {e}")
    yield
    print("Shutting down LLM Cost Autopilot...")


app = FastAPI(
    title="LLM Cost Autopilot",
    description="Intelligent LLM routing layer that minimizes cost while maintaining quality",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
        return await call_next(request)

    if ROUTER_API_KEY:
        provided_key = request.headers.get("X-API-Key", "")
        if provided_key != ROUTER_API_KEY:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

    return await call_next(request)


@app.get("/health")
async def health():
    statuses = {}
    for provider_name in {"openai", "anthropic", "ollama"}:
        try:
            provider = get_provider(provider_name)
            statuses[provider_name] = provider.health_check()
        except Exception:
            statuses[provider_name] = False
    return {"status": "ok", "providers": statuses}


@app.post("/v1/completions")
async def completions(req: CompletionRequest, background_tasks: BackgroundTasks):
    return await handle_completion(req, background_tasks)


@app.get("/v1/models")
async def models():
    return list_models()


@app.get("/v1/stats")
async def stats():
    return await get_stats()


@app.put("/v1/routing-config")
async def routing_config(new_config: dict):
    return update_routing_config(new_config)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)