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

def generate_dashboard():
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
    
    html = HTML_TEMPLATE.format(
        cards=cards_html,
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
