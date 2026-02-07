#!/usr/bin/env python3
"""
Generate web dashboard HTML from usage data.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path("/root/.openclaw/workspace/mimir.db")
OUTPUT_PATH = Path("/root/.openclaw/workspace/dashboard/index.html")


# Consistent color mapping for all sources
SOURCE_COLORS = {
    # Models (blues/purples)
    'gemini-3-pro-image-preview': '#60a5fa',
    'nano_banana_pro': '#60a5fa',
    'qwen-portal/qwen-max': '#a78bfa',
    'qwen-portal/qwen-plus': '#818cf8',
    'qwen-portal/qwen-turbo': '#c084fc',
    'qwen-max': '#a78bfa',
    'qwen-plus': '#818cf8',
    'qwen-turbo': '#c084fc',
    # APIs (warm colors)
    'brave_search': '#fbbf24',
    'nano_banana_pro_api': '#f87171',
    'openai_whisper_api': '#34d399',
    'sag': '#22d3ee',
    'elevenlabs_tts': '#fb923c',
    'github_api': '#a3e635',
    'google_drive': '#e879f9',
    'rclone': '#f472b6',
    'sqlite': '#fbbf24',
}

def get_source_color(name):
    """Get consistent color for a source name."""
    # Try exact match first
    if name in SOURCE_COLORS:
        return SOURCE_COLORS[name]
    # Try short name
    short_name = name.split('/')[-1]
    if short_name in SOURCE_COLORS:
        return SOURCE_COLORS[short_name]
    # Fallback to hash-based color
    colors = ['#60a5fa', '#a78bfa', '#f472b6', '#fbbf24', '#34d399', '#f87171', '#22d3ee', '#fb923c', '#a3e635', '#e879f9']
    hash_val = sum(ord(c) for c in name)
    return colors[hash_val % len(colors)]


def get_dashboard_data():
    """Fetch all data needed for the dashboard."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Daily stats for last 30 days
    cursor.execute("""
        SELECT date(timestamp) as day,
               COUNT(*) as requests,
               SUM(input_tokens) as input_tokens,
               SUM(output_tokens) as output_tokens,
               SUM(total_tokens) as total_tokens,
               SUM(estimated_cost_usd) as cost
        FROM usage_logs
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY date(timestamp)
        ORDER BY day
    """)
    daily = [dict(row) for row in cursor.fetchall()]
    
    # Daily cost by model (for stacked chart) - exclude Kimi subscription models
    cursor.execute("""
        SELECT date(timestamp) as day,
               model as name,
               SUM(estimated_cost_usd) as cost,
               'model' as type
        FROM usage_logs
        WHERE timestamp >= date('now', '-30 days')
          AND model NOT LIKE 'kimi-coding/%'
          AND model NOT LIKE 'kimi/%'
        GROUP BY date(timestamp), model
    """)
    daily_by_model_raw = [dict(row) for row in cursor.fetchall()]
    
    # Daily usage count by model (for stacked chart) - exclude Kimi
    cursor.execute("""
        SELECT date(timestamp) as day,
               model as name,
               COUNT(*) as count
        FROM usage_logs
        WHERE timestamp >= date('now', '-30 days')
          AND model NOT LIKE 'kimi-coding/%'
          AND model NOT LIKE 'kimi/%'
        GROUP BY date(timestamp), model
    """)
    daily_usage_model_raw = [dict(row) for row in cursor.fetchall()]
    
    # Daily cost by API (for stacked chart)
    cursor.execute("""
        SELECT date(timestamp) as day,
               api_name as name,
               SUM(cost_usd) as cost,
               'api' as type
        FROM api_calls
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY date(timestamp), api_name
    """)
    daily_by_api_raw = [dict(row) for row in cursor.fetchall()]
    
    # Daily usage count by API (for stacked chart)
    cursor.execute("""
        SELECT date(timestamp) as day,
               api_name as name,
               COUNT(*) as count
        FROM api_calls
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY date(timestamp), api_name
    """)
    daily_usage_api_raw = [dict(row) for row in cursor.fetchall()]
    
    # Model stats (exclude Kimi) - all time
    cursor.execute("""
        SELECT model,
               COUNT(*) as requests,
               SUM(input_tokens) as input_tokens,
               SUM(output_tokens) as output_tokens,
               SUM(total_tokens) as total_tokens,
               SUM(estimated_cost_usd) as cost
        FROM usage_logs
        WHERE model NOT LIKE 'kimi-coding/%'
          AND model NOT LIKE 'kimi/%'
        GROUP BY model
        ORDER BY total_tokens DESC
    """)
    models = [dict(row) for row in cursor.fetchall()]
    
    # API stats - all time
    cursor.execute("""
        SELECT api_name,
               COUNT(*) as calls,
               SUM(cost_usd) as cost
        FROM api_calls
        GROUP BY api_name
        ORDER BY cost DESC
    """)
    apis = [dict(row) for row in cursor.fetchall()]
    
    # All-time costs for pie chart (models + APIs, exclude Kimi)
    cursor.execute("""
        SELECT model as name,
               SUM(estimated_cost_usd) as cost
        FROM usage_logs
        WHERE model NOT LIKE 'kimi-coding/%'
          AND model NOT LIKE 'kimi/%'
        GROUP BY model
    """)
    all_time_models = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("""
        SELECT api_name as name,
               SUM(cost_usd) as cost
        FROM api_calls
        GROUP BY api_name
    """)
    all_time_apis = [dict(row) for row in cursor.fetchall()]
    
    # Find most costly source (model or API)
    all_sources = all_time_models + all_time_apis
    most_costly = max(all_sources, key=lambda x: x['cost'] or 0) if all_sources else {'name': 'None', 'cost': 0}
    
    # Calculate total cost for percentage
    total_all_cost = sum(s['cost'] or 0 for s in all_sources)
    most_costly_pct = (most_costly['cost'] / total_all_cost * 100) if total_all_cost > 0 else 0
    
    # Find most used API by call count
    cursor.execute("""
        SELECT api_name as name,
               COUNT(*) as calls
        FROM api_calls
        GROUP BY api_name
        ORDER BY calls DESC
        LIMIT 1
    """)
    most_used_row = cursor.fetchone()
    most_used = {'name': most_used_row['name'], 'calls': most_used_row['calls']} if most_used_row else {'name': 'None', 'calls': 0}
    
    # Calculate total calls for percentage
    cursor.execute("""
        SELECT COUNT(*) as total_calls
        FROM api_calls
    """)
    total_calls_row = cursor.fetchone()
    total_api_calls = total_calls_row['total_calls'] if total_calls_row else 0
    most_used_pct = (most_used['calls'] / total_api_calls * 100) if total_api_calls > 0 else 0
    
    # Combine for pie chart
    pie_chart_data = all_time_models + all_time_apis
    
    # Totals - include all API costs (models are subscription, APIs are pay-as-you-go)
    cursor.execute("""
        SELECT 
            COUNT(*) as total_requests,
            SUM(input_tokens) as total_input,
            SUM(output_tokens) as total_output,
            SUM(total_tokens) as total_tokens,
            SUM(estimated_cost_usd) as total_cost
        FROM usage_logs
        WHERE model NOT LIKE 'kimi-coding/%'
          AND model NOT LIKE 'kimi/%'
    """)
    model_totals = dict(cursor.fetchone())
    
    # Get total API costs separately
    cursor.execute("""
        SELECT SUM(cost_usd) as api_total_cost
        FROM api_calls
    """)
    api_total = cursor.fetchone()[0] or 0
    
    # Combine for true total cost
    totals = model_totals
    totals['total_cost'] = (model_totals['total_cost'] or 0) + api_total
    
    # Process daily costs into stacked chart format (models + APIs, no Kimi)
    all_daily_raw = daily_by_model_raw + daily_by_api_raw
    days = sorted(set(d['day'] for d in all_daily_raw))
    all_names = sorted(set(d['name'] for d in all_daily_raw))
    
    # Create datasets for each model/API using consistent colors
    daily_by_source = {}
    
    for name in all_names:
        source_data = []
        for day in days:
            cost = next((d['cost'] for d in all_daily_raw 
                        if d['day'] == day and d['name'] == name), 0)
            source_data.append(cost)
            
        daily_by_source[name] = {
            'data': source_data,
            'color': get_source_color(name)
        }
    
    # Process daily usage counts into stacked chart format
    all_usage_raw = daily_usage_model_raw + daily_usage_api_raw
    usage_by_source = {}
    
    for name in all_names:
        source_data = []
        for day in days:
            count = next((d['count'] for d in all_usage_raw 
                         if d['day'] == day and d['name'] == name), 0)
            source_data.append(count)
            
        usage_by_source[name] = {
            'data': source_data,
            'color': get_source_color(name)
        }
    
    conn.close()
    
    return {
        "daily": daily,
        "daily_by_source": daily_by_source,
        "usage_by_source": usage_by_source,
        "days": days,
        "models": models,
        "apis": apis,
        "pie_chart_data": pie_chart_data,
        "totals": totals,
        "most_costly": most_costly,
        "most_costly_pct": most_costly_pct,
        "most_used": most_used,
        "most_used_pct": most_used_pct,
        "generated_at": datetime.now().strftime('%d-%b-%y %H:%M')
    }


def generate_html(data):
    """Generate the dashboard HTML."""
    
    # Build datasets for stacked chart (models + APIs)
    days = data['days']
    # Format days as DD-Mmm-YY
    formatted_days = [datetime.strptime(d, '%Y-%m-%d').strftime('%d-%b-%y') for d in days]
    daily_labels = json.dumps(formatted_days)
    
    datasets = []
    for name, info in data['daily_by_source'].items():
        name_short = name.split('/')[-1]
        datasets.append({
            'label': name_short,
            'data': info['data'],
            'backgroundColor': info['color'],
        })
    
    datasets_json = json.dumps(datasets)
    
    # Build datasets for usage chart
    usage_datasets = []
    for name, info in data['usage_by_source'].items():
        name_short = name.split('/')[-1]
        usage_datasets.append({
            'label': name_short,
            'data': info['data'],
            'backgroundColor': info['color'],
        })
    
    usage_datasets_json = json.dumps(usage_datasets)
    
    # Pie chart data (models + APIs, all-time, no Kimi) with consistent colors
    pie_data = data['pie_chart_data']
    pie_names = json.dumps([p['name'].split('/')[-1] for p in pie_data])
    pie_costs = json.dumps([p['cost'] for p in pie_data])
    pie_colors = json.dumps([get_source_color(p['name']) for p in pie_data])
    
    # API chart data with consistent colors
    api_data = data['apis']
    api_names = json.dumps([a['api_name'] for a in api_data])
    api_costs = json.dumps([a['cost'] for a in api_data])
    api_colors = json.dumps([get_source_color(a['api_name']) for a in api_data])
    
    totals = data['totals']
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mimir Usage Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #64748b; margin-bottom: 2rem; }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .card {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #334155;
        }}
        .card h3 {{
            font-size: 0.875rem;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}
        .card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: #f8fafc;
        }}
        .card .subvalue {{
            font-size: 0.875rem;
            color: #64748b;
            margin-top: 0.25rem;
        }}
        .chart-container {{
            background: #1e293b;
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid #334155;
            margin-bottom: 1rem;
        }}
        .chart-container h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            color: #f8fafc;
        }}
        .chart-wrapper {{ height: 300px; }}
        .two-col {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
        }}
        @media (max-width: 768px) {{
            body {{ padding: 1rem; }}
            h1 {{ font-size: 1.5rem; }}
            .grid {{ grid-template-columns: repeat(2, 1fr); }}
            .card {{ padding: 1rem; }}
            .card .value {{ font-size: 1.5rem; }}
            .two-col {{ grid-template-columns: 1fr; }}
            .chart-wrapper {{ height: 250px; }}
            .header-row {{ flex-direction: column; align-items: flex-start; }}
        }}
        @media (max-width: 480px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
        .updated {{
            text-align: center;
            color: #64748b;
            margin-top: 2rem;
            font-size: 0.875rem;
        }}
        .refresh-btn {{
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            cursor: pointer;
            margin-bottom: 1rem;
            transition: opacity 0.2s;
        }}
        .refresh-btn:hover {{ opacity: 0.9; }}
        .refresh-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .header-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-row">
            <div>
                <h1>🦉 Mimir Usage Dashboard</h1>
                <p class="subtitle">Track API costs, token usage, and model performance</p>
            </div>
            <button class="refresh-btn" onclick="refreshDashboard()" id="refreshBtn">🔄</button>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Total Cost</h3>
                <div class="value">${totals.get('total_cost', 0):.4f}</div>
                <div class="subvalue">All time</div>
            </div>
            <div class="card">
                <h3>Most Costly API</h3>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.25rem;">
                    <span style="font-size: 1.25rem; font-weight: 600; color: #f8fafc;">{data['most_costly']['name'].split('/')[-1]}</span>
                    <span style="font-size: 2rem; font-weight: 700; color: #f8fafc;">${data['most_costly']['cost']:.4f}</span>
                </div>
                <div class="subvalue">{data['most_costly_pct']:.1f}% of total cost</div>
            </div>
            <div class="card">
                <h3>Most Used API</h3>
                <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 0.25rem;">
                    <span style="font-size: 1.25rem; font-weight: 600; color: #f8fafc;">{data['most_used']['name'].split('/')[-1]}</span>
                    <span style="font-size: 2rem; font-weight: 700; color: #f8fafc;">{data['most_used']['calls']}</span>
                </div>
                <div class="subvalue">{data['most_used_pct']:.1f}% of total calls</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 Daily Cost (Last 30 Days)</h2>
            <div class="chart-wrapper">
                <canvas id="costChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📊 Daily Usage Count (Last 30 Days)</h2>
            <div class="chart-wrapper">
                <canvas id="usageChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>🔌 Cost by API (All-Time)</h2>
            <div class="chart-wrapper">
                <canvas id="apiChart"></canvas>
            </div>
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>📊 All-Time Cost by Source (excludes subscription models)</h2>
                <div class="chart-wrapper">
                    <canvas id="modelChart"></canvas>
                </div>
            </div>
        </div>
        
        <p class="updated">Last updated: {data['generated_at']}</p>
    </div>
    
    <script>
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = '#334155';
        
        // Daily cost chart (stacked by model)
        new Chart(document.getElementById('costChart'), {{
            type: 'bar',
            data: {{
                labels: {daily_labels},
                datasets: {datasets_json}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top' }},
                    tooltip: {{
                        callbacks: {{
                            footer: function(tooltipItems) {{
                                let total = 0;
                                tooltipItems.forEach(function(tooltipItem) {{
                                    total += tooltipItem.parsed.y;
                                }});
                                return 'Total: $' + total.toFixed(4);
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ 
                        stacked: true,
                        grid: {{ display: false }}
                    }},
                    y: {{ 
                        stacked: true,
                        beginAtZero: true,
                        grid: {{ color: '#334155' }}
                    }}
                }}
            }}
        }});
        
        // Daily usage count chart (stacked by source)
        new Chart(document.getElementById('usageChart'), {{
            type: 'bar',
            data: {{
                labels: {daily_labels},
                datasets: {usage_datasets_json}
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'top' }},
                    tooltip: {{
                        callbacks: {{
                            footer: function(tooltipItems) {{
                                let total = 0;
                                tooltipItems.forEach(function(tooltipItem) {{
                                    total += tooltipItem.parsed.y;
                                }});
                                return 'Total: ' + total + ' calls';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ 
                        stacked: true,
                        grid: {{ display: false }}
                    }},
                    y: {{ 
                        stacked: true,
                        beginAtZero: true,
                        grid: {{ color: '#334155' }},
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        
        // Cost by Source chart (pie chart with models + APIs, all-time)
        new Chart(document.getElementById('modelChart'), {{
            type: 'doughnut',
            data: {{
                labels: {pie_names},
                datasets: [{{
                    data: {pie_costs},
                    backgroundColor: {pie_colors}
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right' }}
                }}
            }}
        }});
        
        // API cost chart
        new Chart(document.getElementById('apiChart'), {{
            type: 'bar',
            data: {{
                labels: {api_names},
                datasets: [{{
                    label: 'Cost ($)',
                    data: {api_costs},
                    backgroundColor: {api_colors}
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ display: false }} }},
                scales: {{
                    y: {{ beginAtZero: true }}
                }}
            }}
        }});
        
        // Refresh function
        async function refreshDashboard() {{
            const btn = document.getElementById('refreshBtn');
            btn.disabled = true;
            btn.textContent = '⏳';
            
            try {{
                const response = await fetch('/refresh', {{ method: 'POST' }});
                if (response.ok) {{
                    location.reload();
                }} else {{
                    // Fallback: just reload anyway
                    location.reload();
                }}
            }} catch (err) {{
                // Fallback: just reload
                location.reload();
            }}
        }}
    </script>
</body>
</html>'''
    
    return html


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    data = get_dashboard_data()
    html = generate_html(data)
    
    OUTPUT_PATH.write_text(html)
    print(f"Dashboard generated: {OUTPUT_PATH}")
    print(f"Open in browser: file://{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
