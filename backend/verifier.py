import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from providers.openai_provider import OpenAIProvider

JUDGE_MODEL_ID = "gpt-4o"
MIN_ACCEPTABLE_SCORE = 3.5

_judge = None


def get_judge() -> OpenAIProvider:
    global _judge
    if _judge is None:
        _judge = OpenAIProvider()
    return _judge


JUDGE_SYSTEM_PROMPT = """You are an objective response quality evaluator.
Score the given response strictly on accuracy, completeness, and relevance.
Return ONLY valid JSON with no extra text, no markdown, no explanation outside the JSON.
Format: {"score": <number 1-5>, "reasoning": "<one sentence>"}"""


async def judge_response(prompt: str, response_text: str) -> dict:
    judge = get_judge()

    user_message = f"""Question: {prompt}

Response to evaluate:
{response_text}

Score this response 1-5:
1 = Wrong or completely off-topic
2 = Partially correct, missing key information
3 = Acceptable but lacks depth or has minor errors
4 = Good, minor gaps only
5 = Perfect, fully accurate and complete

Return only JSON: {{"score": <1-5>, "reasoning": "<one sentence>"}}"""

    result = await judge.send_request(
        prompt=user_message,
        model_id=JUDGE_MODEL_ID,
        system_prompt=JUDGE_SYSTEM_PROMPT,
        max_tokens=100,
        temperature=0.0,
    )

    if not result.success:
        return {"score": None, "reasoning": f"Judge call failed: {result.error}"}

    try:
        text = result.output_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        parsed = json.loads(text.strip())
        score = float(parsed.get("score", 0))
        reasoning = parsed.get("reasoning", "")
        return {"score": score, "reasoning": reasoning}
    except Exception as e:
        return {"score": None, "reasoning": f"Failed to parse judge response: {e}"}


async def verify_and_escalate(
    prompt: str,
    original_response_text: str,
    original_model_key: str,
    original_tier: int,
    original_cost: float,
) -> dict:
    """
    Full verification pipeline:
    1. Judge the original response
    2. If score < threshold, escalate to next tier
    3. Return verification result with escalation info
    """
    from providers import send_request
    from models.registry import MODEL_REGISTRY
    import yaml

    routing_config_path = os.path.join(os.path.dirname(__file__), "models", "routing_config.yaml")
    with open(routing_config_path) as f:
        config = yaml.safe_load(f)

    quality_config = config.get("quality", {})
    min_score = quality_config.get("min_acceptable_score", MIN_ACCEPTABLE_SCORE)


    judgment = await judge_response(prompt, original_response_text)
    score = judgment["score"]
    print(f"[VERIFIER] model={original_model_key} tier={original_tier} score={score} reasoning={judgment['reasoning']}")
    result = {
        "original_model": original_model_key,
        "original_tier": original_tier,
        "quality_score": score,
        "reasoning": judgment["reasoning"],
        "escalated": False,
        "escalation_model": None,
        "escalation_cost": 0.0,
        "cost_delta": 0.0,
    }


    if score is not None and score < min_score and original_tier < 3:
        next_tier = original_tier + 1
        next_tier_config = config["routing"][f"tier_{next_tier}"]
        escalation_model = next_tier_config["primary"]

        escalated_response = await send_request(
            prompt=prompt,
            model_key=escalation_model,
            max_tokens=1024,
        )

        if escalated_response.success:
            result["escalated"] = True
            result["escalation_model"] = escalation_model
            result["escalation_cost"] = escalated_response.cost
            result["cost_delta"] = escalated_response.cost - original_cost

    return result