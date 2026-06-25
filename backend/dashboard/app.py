import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import aiosqlite
import asyncio

from db.database import DB_PATH

st.set_page_config(
    page_title="LLM Cost Autopilot",
    page_icon="🚀",
    layout="wide",
)


def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


async def fetch_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        row = await db.execute_fetchall("""
            SELECT
                COUNT(*)                        AS total_requests,
                COALESCE(SUM(cost), 0)          AS total_cost,
                COALESCE(SUM(cost_if_gpt4o), 0) AS total_cost_if_gpt4o,
                COALESCE(AVG(quality_score), 0) AS avg_quality_score,
                COALESCE(SUM(escalated), 0)     AS total_escalations
            FROM requests
        """)
        return dict(row[0])


async def fetch_all_requests() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("""
            SELECT * FROM requests ORDER BY id DESC
        """)
        return [dict(r) for r in rows]


async def fetch_recent_requests(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("""
            SELECT * FROM requests ORDER BY id DESC LIMIT ?
        """, (limit,))
        return [dict(r) for r in rows]


def load_data():
    stats = run_async(fetch_stats())
    all_requests = run_async(fetch_all_requests())
    recent = run_async(fetch_recent_requests(20))
    return stats, all_requests, recent


st.sidebar.title("LLM Cost Autopilot")
st.sidebar.markdown("Intelligent LLM routing — minimize cost, maintain quality")
st.sidebar.divider()

page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Routing", "Quality", "Config"],
    index=0,
)

auto_refresh = st.sidebar.toggle("Auto-refresh (30s)", value=False)
if auto_refresh:
    time.sleep(0.1)
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("Refresh Now"):
    st.rerun()


stats, all_requests, recent_requests = load_data()
df = pd.DataFrame(all_requests) if all_requests else pd.DataFrame()

total_cost = stats["total_cost"]
total_hypothetical = stats["total_cost_if_gpt4o"]
total_saved = total_hypothetical - total_cost
pct_saved = (total_saved / total_hypothetical * 100) if total_hypothetical > 0 else 0.0
avg_quality = stats["avg_quality_score"]
total_requests = stats["total_requests"]
total_escalations = stats["total_escalations"]
escalation_rate = (total_escalations / total_requests * 100) if total_requests > 0 else 0.0


if page == "Overview":
    st.title("Overview")
    st.caption("Real-time cost savings from intelligent LLM routing")
    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Requests", f"{total_requests:,}")
    col2.metric("Total Cost", f"${total_cost:.4f}")
    col3.metric("Saved vs GPT-4o", f"${total_saved:.4f}")
    col4.metric("Cost Reduction", f"{pct_saved:.1f}%")
    col5.metric("Avg Quality Score", f"{avg_quality:.2f} / 5.0")

    st.divider()

    if not df.empty:
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Cost: Actual vs Hypothetical (GPT-4o)")
            cost_comparison = pd.DataFrame({
                "Category": ["Actual Cost", "Hypothetical (All GPT-4o)", "Saved"],
                "Amount ($)": [total_cost, total_hypothetical, total_saved],
            })
            fig = px.bar(
                cost_comparison,
                x="Category",
                y="Amount ($)",
                color="Category",
                color_discrete_map={
                    "Actual Cost": "#e74c3c",
                    "Hypothetical (All GPT-4o)": "#e67e22",
                    "Saved": "#2ecc71",
                },
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col_b:
            st.subheader("Requests Over Time")
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df_time = df.set_index("timestamp").resample("1min").size().reset_index()
                df_time.columns = ["timestamp", "count"]
                fig2 = px.line(df_time, x="timestamp", y="count", markers=True)
                fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No requests yet. Send some prompts via the API to see data here.")


elif page == "Routing":
    st.title("Routing")
    st.caption("How requests are being distributed across models and tiers")
    st.divider()

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Model Distribution")
            model_counts = df["model_used"].value_counts().reset_index()
            model_counts.columns = ["model", "count"]
            fig = px.pie(model_counts, names="model", values="count", hole=0.4)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Tier Distribution")
            tier_counts = df["complexity_tier"].value_counts().sort_index().reset_index()
            tier_counts.columns = ["tier", "count"]
            tier_counts["tier"] = tier_counts["tier"].map({
                1: "Tier 1 - Simple",
                2: "Tier 2 - Moderate",
                3: "Tier 3 - Complex",
            })
            fig2 = px.bar(tier_counts, x="tier", y="count", color="tier")
            fig2.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        st.subheader("Recent Requests")
        display_cols = [
            "id", "timestamp", "prompt_preview", "complexity_tier",
            "classifier_confidence", "model_used", "cost", "cost_if_gpt4o",
            "latency_ms", "escalated",
        ]
        display_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(
            pd.DataFrame(recent_requests)[display_cols],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No requests yet.")


elif page == "Quality":
    st.title("Quality")
    st.caption("Verifier scores, escalation rate, routing failures")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("Avg Quality Score", f"{avg_quality:.2f} / 5.0")
    col2.metric("Total Escalations", f"{total_escalations:,}")
    col3.metric("Escalation Rate", f"{escalation_rate:.1f}%")

    st.divider()

    if not df.empty and "quality_score" in df.columns:
        verified_df = df[df["quality_score"].notna()]

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Quality Score Distribution")
            if not verified_df.empty:
                fig = px.histogram(
                    verified_df,
                    x="quality_score",
                    nbins=5,
                    range_x=[0.5, 5.5],
                    color_discrete_sequence=["#3498db"],
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No verified requests yet.")

        with col_b:
            st.subheader("Quality Score by Model")
            if not verified_df.empty:
                avg_by_model = verified_df.groupby("model_used")["quality_score"].mean().reset_index()
                fig2 = px.bar(
                    avg_by_model,
                    x="model_used",
                    y="quality_score",
                    color="model_used",
                    range_y=[0, 5],
                )
                fig2.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig2, use_container_width=True)

        escalated_df = df[df["escalated"] == 1]
        if not escalated_df.empty:
            st.subheader("Escalated Requests")
            st.dataframe(escalated_df, use_container_width=True, hide_index=True)
        else:
            st.success("No escalations — all models performing above threshold.")
    else:
        st.info("No requests yet.")

elif page == "Config":
    st.title("Config")
    st.caption("Live routing configuration — changes take effect immediately")
    st.divider()

    import yaml

    routing_config_path = os.path.join(os.path.dirname(__file__), "..", "models", "routing_config.yaml")

    with open(routing_config_path, "r") as f:
        current_config = f.read()

    st.subheader("routing_config.yaml")
    new_config = st.text_area(
        "Edit and save to hot-reload routing rules",
        value=current_config,
        height=400,
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("Save Config", type="primary"):
            try:
                yaml.safe_load(new_config)
                with open(routing_config_path, "w") as f:
                    f.write(new_config)
                st.success("Config saved. Next request uses new routing rules.")
            except yaml.YAMLError as e:
                st.error(f"Invalid YAML: {e}")

    with col2:
        if st.button("Retrain Classifier"):
            import subprocess
            backend_dir = os.path.join(os.path.dirname(__file__), "..")
            result = subprocess.run(
                [sys.executable, "classifier.py"],
                cwd=backend_dir,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                st.success("Classifier retrained successfully.")
                st.code(result.stdout)
            else:
                st.error("Retraining failed.")
                st.code(result.stderr)

    st.divider()
    st.subheader("Model Registry")
    from models.registry import MODEL_REGISTRY
    registry_data = [
        {
            "Key": k,
            "Provider": v.provider,
            "Model ID": v.model_id,
            "Tier": v.quality_tier,
            "Input $/M": f"${v.cost_per_input_token * 1_000_000:.2f}",
            "Output $/M": f"${v.cost_per_output_token * 1_000_000:.2f}",
            "Context": f"{v.context_window:,}",
        }
        for k, v in MODEL_REGISTRY.items()
    ]
    st.dataframe(pd.DataFrame(registry_data), use_container_width=True, hide_index=True)