#!/usr/bin/env python3
"""
Usage tracking and dashboard for Mimir.
Log API calls and view cost/usage statistics.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

DB_PATH = Path("/root/.openclaw/workspace/mimir.db")

# Cost per 1K tokens (approximate)
MODEL_COSTS = {
    "kimi-coding/k2p5": {"input": 0.001, "output": 0.003},
    "kimi-coding/kimi-k2-thinking": {"input": 0.002, "output": 0.006},
    "qwen-portal/qwen-max": {"input": 0.001, "output": 0.003},
    "qwen-portal/qwen-plus": {"input": 0.0005, "output": 0.0015},
    "qwen-portal/qwen-turbo": {"input": 0.0002, "output": 0.0006},
    "gemini-3-pro-image-preview": {"input": 0.005, "output": 0.015},
}

# External API costs (per call or per unit)
API_COSTS = {
    "brave_search": {"type": "free", "cost": 0.0},
    "nano_banana_pro": {"type": "per_image", "cost": 0.05},  # Estimated
    "elevenlabs_tts": {"type": "per_1k_chars", "cost": 0.018},
    "openai_whisper": {"type": "per_minute", "cost": 0.006},
    "openai_whisper_api": {"type": "per_minute", "cost": 0.006},
    "google_drive": {"type": "free", "cost": 0.0},
    "github_api": {"type": "free", "cost": 0.0},
    "rclone": {"type": "free", "cost": 0.0},
    "sqlite": {"type": "free", "cost": 0.0},
}


def log_usage(
    session_key: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    tool_name: Optional[str] = None,
    description: Optional[str] = None
) -> None:
    """Log a usage entry to the database."""
    total_tokens = input_tokens + output_tokens
    
    # Calculate estimated cost
    costs = MODEL_COSTS.get(model, {"input": 0.001, "output": 0.003})
    estimated_cost = (input_tokens / 1000 * costs["input"]) + (output_tokens / 1000 * costs["output"])
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage_logs (session_key, model, input_tokens, output_tokens, total_tokens, 
                               estimated_cost_usd, tool_name, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_key, model, input_tokens, output_tokens, total_tokens, 
          estimated_cost, tool_name, description))
    conn.commit()
    conn.close()


def get_daily_stats(days: int = 7) -> list:
    """Get daily usage stats for the last N days."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            date(timestamp) as day,
            COUNT(*) as requests,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost_usd) as cost_usd
        FROM usage_logs
        WHERE timestamp >= date('now', '-{} days')
        GROUP BY date(timestamp)
        ORDER BY day DESC
    """.format(days))
    results = cursor.fetchall()
    conn.close()
    return results


def get_model_stats(days: int = 7) -> list:
    """Get usage stats grouped by model."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            model,
            COUNT(*) as requests,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost_usd) as cost_usd
        FROM usage_logs
        WHERE timestamp >= date('now', '-{} days')
        GROUP BY model
        ORDER BY total_tokens DESC
    """.format(days))
    results = cursor.fetchall()
    conn.close()
    return results


def get_total_stats() -> dict:
    """Get all-time totals."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost_usd) as total_cost
        FROM usage_logs
    """)
    result = cursor.fetchone()
    conn.close()
    return {
        "requests": result[0] or 0,
        "input_tokens": result[1] or 0,
        "output_tokens": result[2] or 0,
        "total_tokens": result[3] or 0,
        "total_cost_usd": result[4] or 0.0
    }


def print_dashboard(days: int = 7):
    """Print a formatted usage dashboard."""
    print("=" * 60)
    print("📊 MIMIR USAGE DASHBOARD")
    print("=" * 60)
    
    # Totals
    totals = get_total_stats()
    print(f"\n📈 ALL-TIME TOTALS")
    print(f"   Requests:     {totals['requests']:,}")
    print(f"   Input tokens: {totals['input_tokens']:,}")
    print(f"   Output tokens: {totals['output_tokens']:,}")
    print(f"   Total tokens: {totals['total_tokens']:,}")
    print(f"   Est. cost:    ${totals['total_cost_usd']:.4f}")
    
    # Daily stats
    print(f"\n📅 LAST {days} DAYS (by day)")
    print("-" * 60)
    daily = get_daily_stats(days)
    if daily:
        print(f"{'Date':<12} {'Reqs':>6} {'Input':>10} {'Output':>10} {'Cost':>8}")
        print("-" * 60)
        for row in daily:
            date, reqs, inp, out, total, cost = row
            print(f"{date:<12} {reqs:>6} {inp:>10,} {out:>10,} ${cost:>7.4f}")
    else:
        print("   No data yet")
    
    # Model stats
    print(f"\n🤖 LAST {days} DAYS (by model)")
    print("-" * 60)
    models = get_model_stats(days)
    if models:
        print(f"{'Model':<30} {'Reqs':>6} {'Tokens':>12} {'Cost':>8}")
        print("-" * 60)
        for row in models:
            model, reqs, inp, out, total, cost = row
            model_short = model.split('/')[-1][:28]
            print(f"{model_short:<30} {reqs:>6} {total:>12,} ${cost:>7.4f}")
    else:
        print("   No data yet")
    
    # API stats
    print(f"\n🔌 LAST {days} DAYS (API calls)")
    print("-" * 60)
    apis = get_api_stats(days)
    if apis:
        print(f"{'API':<30} {'Calls':>6} {'Cost':>8}")
        print("-" * 60)
        for row in apis:
            api, calls, cost = row
            print(f"{api:<30} {calls:>6} ${cost:>7.4f}")
    else:
        print("   No API calls logged yet")
    
    print("\n" + "=" * 60)


def log_api_call(api_name: str, endpoint: str = "", cost_usd: float = 0.0, metadata: str = "") -> None:
    """Log an external API call."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO api_calls (api_name, endpoint, cost_usd, metadata)
        VALUES (?, ?, ?, ?)
    """, (api_name, endpoint, cost_usd, metadata))
    conn.commit()
    conn.close()


def get_api_stats(days: int = 7) -> list:
    """Get API call stats for the last N days."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            api_name,
            COUNT(*) as calls,
            SUM(cost_usd) as total_cost
        FROM api_calls
        WHERE timestamp >= date('now', '-{} days')
        GROUP BY api_name
        ORDER BY total_cost DESC
    """.format(days))
    results = cursor.fetchall()
    conn.close()
    return results


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "dashboard":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print_dashboard(days)
    else:
        print("Usage: python usage_tracker.py dashboard [days]")
        print("       python usage_tracker.py (called programmatically)")
