import requests

# URL del tuo endpoint FastAPI (aggiorna host/porta se diverso)
BASE_URL = "http://localhost:5000/tickers/quote"

# Simbolo da testare
symbol = "AAPL"

# Chiamata GET
response = requests.get(BASE_URL, params={"symbol": symbol})

# Verifica risposta
if response.status_code == 200:
    data = response.json()
    quote = data.get(symbol)
    print(f"Symbol: {quote.get('symbol')}")
    print(f"Current Price: {quote.get('currentPrice')}")
    print(f"Timestamp (Yahoo): {quote.get('timestamp')}")
    print(f"Fetch Time (Server): {quote.get('fetchTime')}")
else:
    print(f"Errore: {response.status_code} - {response.text}")
    