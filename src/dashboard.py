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
    <div class="flex justify-between items-center">
        <h2 class="text-xl font-bold">{ticker}</h2>
        <span class="px-2 py-1 rounded text-xs {badge_color}">{signal_type}</span>
    </div>
    <div class="mt-2 grid grid-cols-2 gap-4 text-sm">
        <div>
            <p class="text-gray-400">Sentiment Z</p>
            <p class="font-mono">{sentiment_z:.2f}</p>
        </div>
        <div>
            <p class="text-gray-400">Volume Z</p>
            <p class="font-mono">{volume_z:.2f}</p>
        </div>
    </div>
    <div class="mt-2 text-xs text-gray-500">
        Confidence: {confidence:.0%}
    </div>
</div>
"""

def generate_dashboard():
    """Generates the index.html file in the public/ directory."""
    if not os.path.exists("public"):
        os.makedirs("public")
        
    # For now, we'll mock the data fetching since we don't have a populated DB in this env
    # In production, this would query `signals` table
    cards_html = ""
    
    # Example card
    cards_html += CARD_TEMPLATE.format(
        ticker="$SOL",
        signal_type="PUMP",
        badge_color="bg-green-900 text-green-300",
        sentiment_z=2.5,
        volume_z=3.1,
        confidence=0.85
    )
    
    html = HTML_TEMPLATE.format(
        cards=cards_html,
        timestamp="Just now"
    )
    
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print("Dashboard generated at public/index.html")

if __name__ == "__main__":
    generate_dashboard()
