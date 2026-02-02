import os
from db import get_db_connection

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticker Agent Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
</head>
<body class="bg-gray-900 text-white p-6">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-6 text-blue-400">🚀 Ticker Agent Signals</h1>
        
        <div class="grid gap-4">
            {cards}
        </div>
        
        <div class="mt-8 text-gray-500 text-sm">
            Last updated: {timestamp}
        </div>
    </div>
    <!-- TradingView Modal -->
    <div id="tv_modal" class="fixed inset-0 bg-black/80 hidden z-50 flex items-center justify-center p-4">
        <div class="bg-gray-800 w-full max-w-5xl h-[80vh] rounded-lg border border-gray-700 flex flex-col relative">
            <button onclick="closeChart()" class="absolute top-4 right-4 text-gray-400 hover:text-white z-10">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
            <div id="modal_chart_container" class="w-full h-full rounded-lg overflow-hidden"></div>
        </div>
    </div>

    <script>
        function openChart(exchange, ticker) {{
            const container = document.getElementById('modal_chart_container');
            container.innerHTML = ''; // Clear previous
            document.getElementById('tv_modal').classList.remove('hidden');
            
            new TradingView.widget({{
                "width": "100%",
                "height": "100%",
                "symbol": exchange + ":" + ticker + "USDT",
                "interval": "60",
                "timezone": "Etc/UTC",
                "theme": "dark",
                "style": "1",
                "locale": "en",
                "toolbar_bg": "#f1f3f6",
                "enable_publishing": false,
                "hide_top_toolbar": false,
                "container_id": "modal_chart_container"
            }});
        }}

        function closeChart() {{
            document.getElementById('tv_modal').classList.add('hidden');
            document.getElementById('modal_chart_container').innerHTML = '';
        }}
        
        // Close on click outside
        document.getElementById('tv_modal').addEventListener('click', function(e) {{
            if (e.target === this) closeChart();
        }});
    </script>
</body>
</html>
"""



# Enhanced Card Template
CARD_TEMPLATE = """
<div class="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden hover:border-blue-500/50 transition-all">
    <!-- Header -->
    <div class="p-4 border-b border-gray-700 bg-gray-800/50 flex justify-between items-start">
        <div class="flex items-center gap-3">
            <img src="{logo}" alt="{ticker}" class="w-10 h-10 rounded-full bg-gray-700" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0iIzM3NDE1MSI+PGNpcmNsZSBjeD0iMjAiIGN5PSIyMCIgcj0iMjAiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZHk9Ii4zZW0iIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM5Q0EyQjIiIHN0eWxlPSJmb250LWZhbWlseTpzYW5zLXNlcmlmO2ZvbnQtc2l6ZToxMnB4Ij4/PC90ZXh0Pjwvc3ZnPg==';">
            <div>
                <h2 class="text-lg font-bold text-white leading-none">{ticker}</h2>
                <p class="text-xs text-gray-400">{name}</p>
            </div>
        </div>
        <div class="text-right">
            <p class="text-lg font-bold text-white">${price}</p>
            <p class="text-xs {price_change_color}">{price_change_24h}% (24h)</p>
        </div>
    </div>

    <!-- Chart Area (DexScreener Embed) -->
    <div class="h-60 bg-gray-900 relative group">
        <iframe 
            src="https://dexscreener.com/{chain}/{pair_address}?embed=1&theme=dark&timezone=UTC" 
            class="w-full h-full border-0"
            loading="lazy"
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms"
            referrerpolicy="strict-origin-when-cross-origin"
        ></iframe>
    </div>

    <!-- ML Confidence Section -->
    <div class="p-4 space-y-4">
        <div>
            <div class="flex justify-between text-xs mb-1">
                <span class="text-gray-400">ML Confidence</span>
                <span class="{conf_color} font-bold">{confidence}%</span>
            </div>
            <div class="w-full bg-gray-700 h-2 rounded-full overflow-hidden">
                <div class="h-full {conf_gradient}" style="width: {confidence}%"></div>
            </div>
        </div>

        <!-- Strategy Grid -->
        <div class="grid grid-cols-3 gap-2 text-center text-xs">
            <div class="bg-gray-700/30 p-2 rounded">
                <p class="text-gray-500 mb-1">Entry</p>
                <p class="text-blue-400 font-mono font-bold">${entry}</p>
            </div>
            <div class="bg-gray-700/30 p-2 rounded">
                <p class="text-gray-500 mb-1">Target</p>
                <p class="text-green-400 font-mono font-bold">${target}</p>
            </div>
            <div class="bg-gray-700/30 p-2 rounded">
                <p class="text-gray-500 mb-1">Stop</p>
                <p class="text-red-400 font-mono font-bold">${stop}</p>
            </div>
        </div>
        
        <!-- Risk/Reward & Volume -->
        <div class="flex justify-between items-center text-xs border-t border-gray-700 pt-3">
            <div class="flex items-center gap-2">
                <span class="text-gray-500">R/R</span>
                <span class="text-white font-mono">{risk_reward}</span>
            </div>
             <div class="flex items-center gap-2">
                <span class="text-gray-500">Vol Ratio</span>
                 <div class="w-20 h-2 bg-red-500/50 rounded-full flex overflow-hidden">
                    <div class="bg-green-500 h-full" style="width: {buy_pressure}%"></div>
                </div>
            </div>
        </div>
    </div>
</div>
"""


DEFI_STATS_TEMPLATE = """
<div class="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
    <!-- Global TVL -->
    <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 text-center">
        <h3 class="text-gray-400 text-sm uppercase tracking-wider mb-1">Global TVL</h3>
        <p class="text-2xl font-bold text-blue-400">${tvl}</p>
    </div>
    
    <!-- Stablecoin Mcap -->
    <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 text-center">
        <h3 class="text-gray-400 text-sm uppercase tracking-wider mb-1">Stablecoin Mcap</h3>
        <p class="text-2xl font-bold text-green-400">${stablecoins}</p>
    </div>
    
    <!-- Top Yield -->
    <div class="bg-gray-800 p-4 rounded-lg border border-gray-700 text-center">
        <h3 class="text-gray-400 text-sm uppercase tracking-wider mb-1">Top Yield</h3>
        <p class="text-xl font-bold text-yellow-400">{top_yield_apy:.0f}% APY</p>
        <p class="text-xs text-gray-500">{top_yield_pool}</p>
    </div>
</div>

<div class="mb-8 bg-gray-800 p-4 rounded-lg border border-gray-700">
    <h3 class="text-lg font-bold mb-4 text-gray-300">🔥 Top Yield Pools</h3>
    <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-gray-400">
            <thead class="text-xs text-gray-500 uppercase bg-gray-700">
                <tr>
                    <th class="px-4 py-2">Project</th>
                    <th class="px-4 py-2">Chain</th>
                    <th class="px-4 py-2">Symbol</th>
                    <th class="px-4 py-2">APY</th>
                    <th class="px-4 py-2">TVL</th>
                </tr>
            </thead>
            <tbody>
                {yield_rows}
            </tbody>
        </table>
    </div>
</div>
"""

YIELD_ROW_TEMPLATE = """
<tr class="border-b border-gray-700 hover:bg-gray-700">
    <td class="px-4 py-2 font-medium text-white">{project}</td>
    <td class="px-4 py-2">{chain}</td>
    <td class="px-4 py-2">{symbol}</td>
    <td class="px-4 py-2 text-green-400 font-bold">{apy:.2f}%</td>
    <td class="px-4 py-2">${tvl:,.0f}</td>
</tr>
"""

TOP_PICKS_TEMPLATE = """
<div class="mb-8">
    <h2 class="text-2xl font-bold mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600">🎯 Top Picks of the Moment</h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- Safe Pick -->
        <div class="bg-gray-800 rounded-xl border border-green-500/30 p-6 relative overflow-hidden group hover:border-green-500 transition-all flex flex-col">
            <div class="absolute top-0 right-0 bg-green-500/20 text-green-400 text-xs px-2 py-1 rounded-bl-lg font-bold">SAFE</div>
            <h3 class="text-2xl font-bold text-white mb-1">{safe_ticker}</h3>
            <p class="text-gray-400 text-sm mb-4">High Cap • Steady</p>
            
            <div class="flex justify-between items-end mb-4">
                <div>
                    <p class="text-xs text-gray-500">Sentiment</p>
                    <p class="text-lg font-mono text-green-400">{safe_sent:.2f}</p>
                </div>
                <div class="text-right">
                    <p class="text-xs text-gray-500">FDV</p>
                    <p class="text-lg font-mono text-white">${safe_fdv}</p>
                </div>
            </div>

            <div class="mt-auto">
                <div class="border-t border-gray-700 pt-2 grid grid-cols-3 gap-2 text-xs text-center mb-3">
                    <div>
                        <p class="text-gray-500">Entry</p>
                        <p class="text-blue-400 font-bold">${safe_entry}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Target</p>
                        <p class="text-green-400 font-bold">${safe_target}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Stop</p>
                        <p class="text-red-400 font-bold">${safe_stop}</p>
                    </div>
                </div>
                <button onclick="openChart('BINANCE', '{safe_clean}')" class="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded transition-colors flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                    View Chart
                </button>
            </div>
        </div>

        <!-- Mid Pick -->
        <div class="bg-gray-800 rounded-xl border border-blue-500/30 p-6 relative overflow-hidden group hover:border-blue-500 transition-all flex flex-col">
            <div class="absolute top-0 right-0 bg-blue-500/20 text-blue-400 text-xs px-2 py-1 rounded-bl-lg font-bold">MID</div>
            <h3 class="text-2xl font-bold text-white mb-1">{mid_ticker}</h3>
            <p class="text-gray-400 text-sm mb-4">Growth • Momentum</p>
            
            <div class="flex justify-between items-end mb-4">
                <div>
                    <p class="text-xs text-gray-500">Sentiment</p>
                    <p class="text-lg font-mono text-blue-400">{mid_sent:.2f}</p>
                </div>
                <div class="text-right">
                    <p class="text-xs text-gray-500">FDV</p>
                    <p class="text-lg font-mono text-white">${mid_fdv}</p>
                </div>
            </div>

            <div class="mt-auto">
                <div class="border-t border-gray-700 pt-2 grid grid-cols-3 gap-2 text-xs text-center mb-3">
                    <div>
                        <p class="text-gray-500">Entry</p>
                        <p class="text-blue-400 font-bold">${mid_entry}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Target</p>
                        <p class="text-green-400 font-bold">${mid_target}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Stop</p>
                        <p class="text-red-400 font-bold">${mid_stop}</p>
                    </div>
                </div>
                <button onclick="openChart('BINANCE', '{mid_clean}')" class="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded transition-colors flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                    View Chart
                </button>
            </div>
        </div>

        <!-- Degen Pick -->
        <div class="bg-gray-800 rounded-xl border border-red-500/30 p-6 relative overflow-hidden group hover:border-red-500 transition-all flex flex-col">
            <div class="absolute top-0 right-0 bg-red-500/20 text-red-400 text-xs px-2 py-1 rounded-bl-lg font-bold">DEGEN</div>
            <h3 class="text-2xl font-bold text-white mb-1">{degen_ticker}</h3>
            <p class="text-gray-400 text-sm mb-4">High Risk • Explosive</p>
            
            <div class="flex justify-between items-end mb-4">
                <div>
                    <p class="text-xs text-gray-500">Volume</p>
                    <p class="text-lg font-mono text-red-400">{degen_vol}</p>
                </div>
                <div class="text-right">
                    <p class="text-xs text-gray-500">FDV</p>
                    <p class="text-lg font-mono text-white">${degen_fdv}</p>
                </div>
            </div>

            <div class="mt-auto">
                <div class="border-t border-gray-700 pt-2 grid grid-cols-3 gap-2 text-xs text-center mb-3">
                    <div>
                        <p class="text-gray-500">Entry</p>
                        <p class="text-blue-400 font-bold">${degen_entry}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Target</p>
                        <p class="text-green-400 font-bold">${degen_target}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Stop</p>
                        <p class="text-red-400 font-bold">${degen_stop}</p>
                    </div>
                </div>
                <button onclick="openChart('BINANCE', '{degen_clean}')" class="w-full bg-gray-700 hover:bg-gray-600 text-white text-xs py-2 rounded transition-colors flex items-center justify-center gap-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>
                    View Chart
                </button>
            </div>
        </div>
    </div>
</div>
"""

NEWS_SECTION_TEMPLATE = """
<div class="mb-8 bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h2 class="text-xl font-bold mb-4 text-orange-400 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" /></svg>
        Latest Crypto News
    </h2>
    <div class="space-y-4">
        {news_items}
    </div>
</div>
"""


NEWS_ITEM_TEMPLATE = """
<div class="border-b border-gray-700 pb-4 last:border-0 last:pb-0 flex flex-col md:flex-row gap-4 items-start">
    <div class="w-full md:w-32 h-32 shrink-0 rounded-lg overflow-hidden bg-gray-700">
        <img src="{image}" alt="News Image" class="w-full h-full object-cover" onerror="this.onerror=null; this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0iIzE2MjEzZSI+PHJlY3Qgd2lkdGg9IjI0IiBoZWlnaHQ9IjI0IiBmaWxsPSIjMWYyOTM3Ii8+PHRleHQgeT0iNTAlIiB4PSI1MCUiIGR5PSIuM2VtIiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmaWxsPSIjNGI1NTYzIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSI0Ij5OZXdzPC90ZXh0Pjwvc3ZnPg==';">
    </div>
    <div class="flex-1">
        <a href="{url}" target="_blank" class="text-lg font-medium text-white hover:text-blue-400 transition-colors block mb-2 leading-tight">{title}</a>
        <p class="text-sm text-gray-400 mb-3 line-clamp-3">{summary}</p>
        <div class="flex items-center gap-2">
            <span class="text-xs bg-orange-500/10 text-orange-400 px-2 py-0.5 rounded border border-orange-500/20">Cointelegraph</span>
            <span class="text-xs text-gray-500">• Just now</span>
        </div>
    </div>
</div>
"""

STABLECOIN_FLOWS_TEMPLATE = """
<div class="mb-8 bg-gray-800 p-6 rounded-lg border border-gray-700">
    <h2 class="text-xl font-bold mb-4 text-green-400 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
        Major Stablecoin Inflows (7d)
    </h2>
    <div class="overflow-x-auto">
        <table class="w-full text-sm text-left text-gray-400">
            <thead class="text-xs text-gray-500 uppercase bg-gray-700">
                <tr>
                    <th class="px-4 py-2">Chain</th>
                    <th class="px-4 py-2">Total Circulating</th>
                    <th class="px-4 py-2">7d Change ($)</th>
                    <th class="px-4 py-2">Growth</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
</div>
"""

FLOW_ROW_TEMPLATE = """
<tr class="border-b border-gray-700 hover:bg-gray-700">
    <td class="px-4 py-2 font-medium text-white">{chain}</td>
    <td class="px-4 py-2 text-gray-300">${total}</td>
    <td class="px-4 py-2 {color_class} font-bold">{sign}${change}</td>
    <td class="px-4 py-2 {color_class}">{sign}{pct}%</td>
</tr>
"""

PORTFOLIO_TEMPLATE = """
<div class="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
    <!-- Balance Card -->
    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700 relative overflow-hidden">
        <div class="absolute top-0 right-0 p-4 opacity-10">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-24 w-24 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        </div>
        <h3 class="text-sm uppercase text-gray-400 font-semibold mb-2">Paper Portfolio Balance</h3>
        <div class="text-4xl font-bold text-white mb-1">${balance:,.2f}</div>
        <div class="text-sm text-green-400 flex items-center gap-1">
            <span class="bg-green-500/10 px-2 py-0.5 rounded">Active Trading</span>
        </div>
    </div>

    <!-- Active Trades -->
    <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 class="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>
            Active Positions
        </h3>
        <div class="overflow-x-auto">
            <table class="w-full text-sm text-left text-gray-400">
                <thead class="text-xs text-gray-500 uppercase bg-gray-700">
                    <tr>
                        <th class="px-4 py-2">Ticker</th>
                        <th class="px-4 py-2">Entry</th>
                        <th class="px-4 py-2">Amount</th>
                        <th class="px-4 py-2">Conf</th>
                    </tr>
                </thead>
                <tbody>
                    {trade_rows}
                </tbody>
            </table>
            {empty_msg}
        </div>
    </div>
</div>
"""

TRADE_ROW_TEMPLATE = """
<tr class="border-b border-gray-700">
    <td class="px-4 py-2 font-bold text-white">{ticker}</td>
    <td class="px-4 py-2">${entry:.4f}</td>
    <td class="px-4 py-2">{amount:.2f}</td>
    <td class="px-4 py-2 text-blue-400">{conf}%</td>
</tr>
"""

def generate_dashboard(defi_stats=None, top_picks=None, news=None, signals=None, stablecoin_flows=None, portfolio=None):
    """Generates the index.html file in the public/ directory."""
    cwd = os.getcwd()
    public_dir = os.path.join(cwd, "public")
    file_path = os.path.join(public_dir, "index.html")
    
    # ... (Keep existing logic for picks, cards, news, defi_html) ...
    # This is slightly inefficient as I'm replacing the whole function signature downwards, but I will try to be surgical with chunks if permitted.
    # Actually, to avoid breaking prior context which I cannot fully echo back reliably without reading line-by-line, 
    # I will replace the function definition line and the later rendering block.
    # But wait, replace_file_content requires contiguous block. I will just rewrite generate_dashboard from line 357 to 532.
    
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
        
    # 1. Top Picks HTML
    picks_html = ""
    if top_picks:
        safe = top_picks.get('safe') or {}
        mid = top_picks.get('mid') or {}
        degen = top_picks.get('degen') or {}
        
        def format_fdv(val):
            if not val: return "N/A"
            if val >= 1_000_000_000: return f"{val/1_000_000_000:.1f}B"
            if val >= 1_000_000: return f"{val/1_000_000:.1f}M"
            return f"{val/1_000:.1f}K"

        picks_html = TOP_PICKS_TEMPLATE.format(
            safe_ticker=safe.get('ticker', 'N/A'),
            safe_clean=safe.get('ticker', '').replace('$', ''),
            safe_sent=safe.get('sentiment', 0.0),
            safe_fdv=format_fdv(safe.get('fdv', 0)),
            safe_entry=f"{safe.get('entry', 0):.4f}",
            safe_target=f"{safe.get('target', 0):.4f}",
            safe_stop=f"{safe.get('stop', 0):.4f}",
            
            mid_ticker=mid.get('ticker', 'N/A'),
            mid_clean=mid.get('ticker', '').replace('$', ''),
            mid_sent=mid.get('sentiment', 0.0),
            mid_fdv=format_fdv(mid.get('fdv', 0)),
            mid_entry=f"{mid.get('entry', 0):.4f}",
            mid_target=f"{mid.get('target', 0):.4f}",
            mid_stop=f"{mid.get('stop', 0):.4f}",
            
            degen_ticker=degen.get('ticker', 'N/A'),
            degen_clean=degen.get('ticker', '').replace('$', ''),
            degen_vol=f"{degen.get('volume', 0):,.0f}",
            degen_fdv=format_fdv(degen.get('fdv', 0)),
            degen_entry=f"{degen.get('entry', 0):.4f}",
            degen_target=f"{degen.get('target', 0):.4f}",
            degen_stop=f"{degen.get('stop', 0):.4f}"
        )

    # 2. Signal Cards HTML
    cards_html = ""
    if signals:
        for s in signals:
            ticker = s.get('ticker', 'Unknown')
            clean_ticker = ticker.replace('$', '').replace('/', '')
            
            
            price_change_data = s.get('price_change') or {}
            price_chg = float(price_change_data.get('h24', 0) or 0)
            price_change_color = "text-green-400" if price_chg >= 0 else "text-red-400"
            price_change_display = f"+{price_chg:.2f}" if price_chg >= 0 else f"{price_chg:.2f}"
            
            conf = int(s.get('confidence', 0))
            conf_color = "text-green-400" if conf > 70 else ("text-yellow-400" if conf > 40 else "text-gray-400")
            conf_gradient = "bg-gradient-to-r from-blue-500 to-green-400"
            
            
            vol = s.get('volume_profile') or {}
            buys = float(vol.get('buys', 0) or 0)
            sells = float(vol.get('sells', 0) or 0)
            total_vol = buys + sells
            buy_pressure = (buys / total_vol * 100) if total_vol > 0 else 50
            
            p_val = float(s.get('price') or 0)
            price_display = f"{p_val:.8f}" if p_val < 0.01 and p_val > 0 else f"{p_val:.4f}"
            
            entry_val = float(s.get('entry', 0))
            target_val = float(s.get('target', 0))
            stop_val = float(s.get('stop', 0))
            
            if entry_val < 0.01 and entry_val > 0:
                entry_display = f"{entry_val:.8f}"
                target_display = f"{target_val:.8f}"
                stop_display = f"{stop_val:.8f}"
            else:
                entry_display = f"{entry_val:.4f}"
                target_display = f"{target_val:.4f}"
                stop_display = f"{stop_val:.4f}"

            cards_html += CARD_TEMPLATE.format(
                ticker=ticker,
                clean_ticker=clean_ticker,
                name=s.get('name', ''),
                logo=s.get('logo', ''),
                price=price_display, 
                price_change_color=price_change_color,
                price_change_24h=price_change_display,
                confidence=conf,
                conf_color=conf_color,
                conf_gradient=conf_gradient,
                entry=entry_display,
                target=target_display,
                stop=stop_display,
                risk_reward=s.get('risk_reward', 'N/A'),
                buy_pressure=buy_pressure,
                chain=s.get('chain', 'solana'), 
                pair_address=s.get('pair_address', '')
            )
    else:
        cards_html = '<div class="col-span-full text-center text-gray-500 py-10">Waiting for signals...</div>'

    # 3. News HTML
    news_html = ""
    if news:
        news_items = ""
        for article in news:
            news_items += NEWS_ITEM_TEMPLATE.format(
                title=article['metadata']['title'],
                summary=article['metadata']['summary'][:200] + "...",
                url=article['url'],
                image=article['metadata'].get('image', ''),
                sentiment="Neutral" # Placeholder
            )
        news_html = NEWS_SECTION_TEMPLATE.format(news_items=news_items)
        
    # 4. Global DeFi Stats
    defi_html = ""
    if defi_stats:
        yield_rows = ""
        for pool in defi_stats.get('yields', []):
            yield_rows += YIELD_ROW_TEMPLATE.format(
                project=pool['project'],
                chain=pool['chain'],
                symbol=pool['symbol'],
                apy=pool['apy'],
                tvl=pool['tvl']
            )
        top_yield = defi_stats['yields'][0] if defi_stats.get('yields') else {}
        defi_html = DEFI_STATS_TEMPLATE.format(
            tvl=f"{defi_stats.get('tvl', 0):,.0f}",
            stablecoins=f"{defi_stats.get('stablecoins', 0):,.0f}",
            top_yield_apy=top_yield.get('apy', 0),
            top_yield_pool=f"{top_yield.get('project', '')} ({top_yield.get('symbol', '')})",
            yield_rows=yield_rows
        )

    # 5. Stablecoin Flows (NEW)
    flows_html = ""
    if stablecoin_flows:
        flow_rows = ""
        for flow in stablecoin_flows[:10]: # Top 10 chains
             change = flow.get('change_7d', 0)
             color_class = "text-green-400" if change >= 0 else "text-red-400"
             sign = "+" if change >= 0 else ""
             
             # Format large numbers like 100M, 1B
             def short_fmt(n):
                 n = abs(n)
                 if n >= 1e9: return f"{n/1e9:.1f}B"
                 if n >= 1e6: return f"{n/1e6:.1f}M"
                 return f"{n/1e3:.0f}K"
             
             flow_rows += FLOW_ROW_TEMPLATE.format(
                 chain=flow['chain'],
                 total=short_fmt(flow['total']),
                 change=short_fmt(change),
                 pct=f"{flow['pct_7d']:.1f}",
                 color_class=color_class,
                 sign=sign
             )
        flows_html = STABLECOIN_FLOWS_TEMPLATE.format(rows=flow_rows)

    # 6. Portfolio HTML (Agent)
    portfolio_html = ""
    if portfolio:
        trade_rows = ""
        trades = portfolio.get('active_trades', [])
        
        if trades:
            # trades is list of tuples: (id, ticker, entry, amount, entry_time, status, ...)
            # We only need ticker, entry, amount, and maybe confidence (which is at index 10)
            for t in trades:
                # Basic tuple unpacking based on db schema
                ticker = t[1]
                entry = t[2]
                amount = t[3]
                conf = int(t[10]) if len(t) > 10 else 0
                
                trade_rows += TRADE_ROW_TEMPLATE.format(
                    ticker=ticker,
                    entry=entry,
                    amount=amount,
                    conf=conf
                )
            empty_msg = ""
        else:
            empty_msg = '<div class="p-4 text-center text-gray-500 italic">No active trades yet. Waiting for opportunities...</div>'
            
        portfolio_html = PORTFOLIO_TEMPLATE.format(
            balance=portfolio.get('balance_usd', 0),
            trade_rows=trade_rows,
            empty_msg=empty_msg
        )

    # Combine everything
    html = HTML_TEMPLATE.format(
        cards=picks_html + portfolio_html + defi_html + flows_html + news_html + cards_html,
        timestamp="Just now"
    )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Dashboard generated at: {file_path}")
    if os.path.exists(file_path):
        print(f"File successfully created. Size: {os.path.getsize(file_path)} bytes")
    # else print error logic removed to save lines.

if __name__ == "__main__":
    generate_dashboard()
