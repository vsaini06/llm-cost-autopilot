import os
import sys
import yaml
from fastapi import BackgroundTasks
from fastapi import Request
from verifier import verify_and_escalate
import hashlib
from db.database import log_request

sys.path.insert(0, os.path.dirname(__file__))

from typing import Optional
from pydantic import BaseModel, Field

from classifier import predict_tier
from providers import send_request
from models.registry import MODEL_REGISTRY


BASE_DIR = os.path.dirname(__file__)
CLASSIFIER_PATH = os.path.join(BASE_DIR, "data", "classifier.pkl")
ROUTING_CONFIG_PATH = os.path.join(BASE_DIR, "models", "routing_config.yaml")

CONFIDENCE_THRESHOLD = 0.75

class CompletionRequest(BaseModel):
    prompt: str
    max_tokens: int = Field(default=1024, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class CompletionResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    answer: str
    model_used: str
    complexity_tier: int
    classifier_confidence: float
    routing_reason: str
    cost: float
    cost_if_gpt4o: float
    cost_saved: float
    latency_ms: int
    quality_score: Optional[float] = None
    escalated: bool = False

def load_routing_config() -> dict:
    with open(ROUTING_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_routing_config(new_config: dict) -> None:
    with open(ROUTING_CONFIG_PATH, "w") as f:
        yaml.safe_dump(new_config, f, default_flow_style=False, sort_keys=False)


async def handle_completion(req: CompletionRequest, background_tasks: BackgroundTasks = None) -> CompletionResponse:
    config = load_routing_config()

    # ---Step 1---
    classification = predict_tier(req.prompt, CLASSIFIER_PATH)
    tier = classification["tier"]
    confidence = classification["confidence"]

    # ---Step 2---
    escalated_for_confidence = False
    if confidence < CONFIDENCE_THRESHOLD and tier < 3:
        tier = tier + 1
        escalated_for_confidence = True

    tier_key = f"tier_{tier}"
    tier_config = config["routing"][tier_key]
    model_key = tier_config["primary"]

    # ---Step 3---
    response = await send_request(
        prompt=req.prompt,
        model_key=model_key,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
    )

    if not response.success:
        fallback_key = tier_config.get("fallback")
        if fallback_key:
            response = await send_request(
                prompt=req.prompt,
                model_key=fallback_key,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            )
            model_key = fallback_key

    # ---Step 4---
    gpt4o = MODEL_REGISTRY["gpt-4o"]
    cost_if_gpt4o = gpt4o.estimate_cost(response.tokens_in, response.tokens_out)
    cost_saved = cost_if_gpt4o - response.cost

    routing_reason = tier_config.get("description", "")
    if escalated_for_confidence:
        routing_reason += f" (low classifier confidence {confidence:.2f} - escalated one tier)"

    if background_tasks is not None:
        background_tasks.add_task(
            verify_and_escalate,
            req.prompt,
            response.output_text,
            model_key,
            tier,
            response.cost,
        )

    prompt_hash = hashlib.sha256(req.prompt.encode()).hexdigest()
    await log_request({
        "prompt_hash": prompt_hash,
        "prompt_preview": req.prompt[:100],
        "complexity_tier": tier,
        "classifier_confidence": confidence,
        "model_used": model_key,
        "tokens_in": response.tokens_in,
        "tokens_out": response.tokens_out,
        "cost": response.cost,
        "cost_if_gpt4o": cost_if_gpt4o,
        "latency_ms": response.latency_ms,
        "quality_score": None,
        "escalated": 0,
        "escalation_model": None,
        "escalation_cost_delta": 0.0,
        "verified": 0,
    })

    return CompletionResponse(
        answer=response.output_text,
        model_used=model_key,
        complexity_tier=tier,
        classifier_confidence=confidence,
        routing_reason=routing_reason,
        cost=round(response.cost, 6),
        cost_if_gpt4o=round(cost_if_gpt4o, 6),
        cost_saved=round(cost_saved, 6),
        latency_ms=response.latency_ms,
        quality_score=None,
        escalated=escalated_for_confidence,
    )

def list_models() -> list[dict]:
    return [
        {
            "key": key,
            "provider": cfg.provider,
            "model_id": cfg.model_id,
            "display_name": cfg.display_name,
            "cost_per_input_token": cfg.cost_per_input_token,
            "cost_per_output_token": cfg.cost_per_output_token,
            "quality_tier": cfg.quality_tier,
            "context_window": cfg.context_window,
        }
        for key, cfg in MODEL_REGISTRY.items()
    ]


async def get_stats() -> dict:
    from db.database import get_stats as db_get_stats
    return await db_get_stats()


def update_routing_config(new_config: dict) -> dict:
    save_routing_config(new_config)
    return {"status": "updated", "config": new_config}