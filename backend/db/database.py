import os
import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "requests.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp             TEXT    DEFAULT CURRENT_TIMESTAMP,
                prompt_hash           TEXT    NOT NULL,
                prompt_preview        TEXT,
                complexity_tier       INTEGER NOT NULL,
                classifier_confidence REAL,
                model_used            TEXT    NOT NULL,
                tokens_in             INTEGER DEFAULT 0,
                tokens_out            INTEGER DEFAULT 0,
                cost                  REAL    DEFAULT 0.0,
                cost_if_gpt4o         REAL    DEFAULT 0.0,
                latency_ms            INTEGER DEFAULT 0,
                quality_score         REAL,
                escalated             INTEGER DEFAULT 0,
                escalation_model      TEXT,
                escalation_cost_delta REAL    DEFAULT 0.0,
                verified              INTEGER DEFAULT 0
            )
        """)
        await db.commit()


async def log_request(data: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO requests (
                prompt_hash, prompt_preview, complexity_tier,
                classifier_confidence, model_used, tokens_in, tokens_out,
                cost, cost_if_gpt4o, latency_ms, quality_score,
                escalated, escalation_model, escalation_cost_delta, verified
            ) VALUES (
                :prompt_hash, :prompt_preview, :complexity_tier,
                :classifier_confidence, :model_used, :tokens_in, :tokens_out,
                :cost, :cost_if_gpt4o, :latency_ms, :quality_score,
                :escalated, :escalation_model, :escalation_cost_delta, :verified
            )
        """, data)
        await db.commit()


async def update_verification(prompt_hash: str, quality_score: float,
                               escalated: bool, escalation_model: str,
                               escalation_cost_delta: float):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE requests
            SET quality_score         = ?,
                escalated             = ?,
                escalation_model      = ?,
                escalation_cost_delta = ?,
                verified              = 1
            WHERE prompt_hash = ?
            AND id = (
                SELECT id FROM requests
                WHERE prompt_hash = ?
                ORDER BY id DESC LIMIT 1
            )
        """, (quality_score, int(escalated), escalation_model,
              escalation_cost_delta, prompt_hash, prompt_hash))
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        row = await db.execute_fetchall("""
            SELECT
                COUNT(*)                          AS total_requests,
                COALESCE(SUM(cost), 0)            AS total_cost,
                COALESCE(SUM(cost_if_gpt4o), 0)   AS total_cost_if_gpt4o,
                COALESCE(AVG(quality_score), 0)   AS avg_quality_score,
                COALESCE(SUM(escalated), 0)       AS total_escalations
            FROM requests
        """)
        totals = dict(row[0])

        model_rows = await db.execute_fetchall("""
            SELECT model_used, COUNT(*) as count
            FROM requests
            GROUP BY model_used
            ORDER BY count DESC
        """)
        model_dist = {r["model_used"]: r["count"] for r in model_rows}

        tier_rows = await db.execute_fetchall("""
            SELECT complexity_tier, COUNT(*) as count
            FROM requests
            GROUP BY complexity_tier
            ORDER BY complexity_tier
        """)
        tier_dist = {f"tier_{r['complexity_tier']}": r["count"] for r in tier_rows}

    total_cost = totals["total_cost"]
    total_hypothetical = totals["total_cost_if_gpt4o"]
    total_saved = total_hypothetical - total_cost
    pct_saved = (total_saved / total_hypothetical * 100) if total_hypothetical > 0 else 0.0

    return {
        "total_requests": totals["total_requests"],
        "total_cost": round(total_cost, 6),
        "total_cost_if_gpt4o": round(total_hypothetical, 6),
        "total_saved": round(total_saved, 6),
        "cost_reduction_pct": round(pct_saved, 2),
        "avg_quality_score": round(totals["avg_quality_score"], 2),
        "total_escalations": totals["total_escalations"],
        "model_distribution": model_dist,
        "tier_distribution": tier_dist,
    }


async def get_recent_requests(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("""
            SELECT * FROM requests
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in rows]