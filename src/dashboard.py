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
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="bg-gray-800 p-4 rounded-lg border border-gray-700">
    <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold">{ticker}</h2>
        <span class="px-2 py-1 rounded text-xs {badge_color}">{signal_type}</span>
    </div>
    
    <!-- TradingView Widget -->
    <div class="h-64 mb-4 rounded overflow-hidden" id="tv_chart_{clean_ticker}"></div>
    <script>
    new TradingView.widget(
    {{
        "width": "100%",
        "height": 250,
        "symbol": "{exchange}:{clean_ticker}USD",
        "interval": "60",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "hide_top_toolbar": true,
        "container_id": "tv_chart_{clean_ticker}"
    }}
    );
    </script>

    <div class="grid grid-cols-2 gap-4 text-sm mb-4">
        <div>
            <p class="text-gray-400">Sentiment Z</p>
            <p class="font-mono">{sentiment_z:.2f}</p>
        </div>
        <div>
            <p class="text-gray-400">Volume Z</p>
            <p class="font-mono">{volume_z:.2f}</p>
        </div>
    </div>
    
    <div class="border-t border-gray-700 pt-2 grid grid-cols-3 gap-2 text-xs text-center">
        <div>
            <p class="text-gray-500">Entry</p>
            <p class="text-blue-400 font-bold">${entry_price}</p>
        </div>
        <div>
            <p class="text-gray-500">Target</p>
            <p class="text-green-400 font-bold">${target_price}</p>
        </div>
        <div>
            <p class="text-gray-500">Stop</p>
            <p class="text-red-400 font-bold">${stop_price}</p>
        </div>
    </div>

    <div class="mt-2 text-xs text-gray-500 text-right">
        Confidence: {confidence:.0%}
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

def generate_dashboard(defi_stats=None):
    """Generates the index.html file in the public/ directory."""
    # Ensure we are using absolute paths relative to CWD
    cwd = os.getcwd()
    public_dir = os.path.join(cwd, "public")
    file_path = os.path.join(public_dir, "index.html")
    
    print(f"Generating dashboard in: {public_dir}")
    
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
        print(f"Created directory: {public_dir}")
        
    # For now, we'll mock the data fetching since we don't have a populated DB in this env
    # In production, this would query `signals` table
    cards_html = ""
    
    # Example card
    cards_html += CARD_TEMPLATE.format(
        ticker="$SOL",
        clean_ticker="SOL",
        exchange="BINANCE",
        signal_type="PUMP",
        badge_color="bg-green-900 text-green-300",
        sentiment_z=2.5,
        volume_z=3.1,
        confidence=0.85,
        entry_price="145.20",
        target_price="166.98",
        stop_price="137.94"
    )
    
    # Generate DeFi Stats HTML
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
            
        top_yield = defi_stats['yields'][0] if defi_stats['yields'] else {}
        
        defi_html = DEFI_STATS_TEMPLATE.format(
            tvl=f"{defi_stats.get('tvl', 0):,.0f}",
            stablecoins=f"{defi_stats.get('stablecoins', 0):,.0f}",
            top_yield_apy=top_yield.get('apy', 0),
            top_yield_pool=f"{top_yield.get('project')} ({top_yield.get('symbol')})",
            yield_rows=yield_rows
        )

    html = HTML_TEMPLATE.format(
        cards=defi_html + cards_html,
        timestamp="Just now"
    )
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Dashboard generated at: {file_path}")
    # Verify file exists
    if os.path.exists(file_path):
        print(f"File successfully created. Size: {os.path.getsize(file_path)} bytes")
    else:
        print("ERROR: File was not created!")

if __name__ == "__main__":
    generate_dashboard()
