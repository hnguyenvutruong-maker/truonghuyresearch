import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import requests

# Current day data from CafeF (to verify the API works)
url = 'https://banggia.cafef.vn/stockhandler.ashx?center=1'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Fetching current HOSE data from CafeF...")
resp = requests.get(url, headers=headers, timeout=10)
data = resp.json()

# Aggregate foreign buy/sell
foreign_net_vnd = 0.0
foreign_buy_vnd = 0.0
foreign_sell_vnd = 0.0
count = 0

for item in data:
    if isinstance(item, dict):
        price_vnd = item.get('e', 0) * 1000
        fb = item.get('x', 0)
        fs = item.get('y', 0)
        if price_vnd > 0:
            foreign_net_vnd += (fb - fs) * price_vnd
            foreign_buy_vnd += fb * price_vnd
            foreign_sell_vnd += fs * price_vnd
            count += 1

net_bn = round(foreign_net_vnd / 1e9, 2)
buy_bn = round(foreign_buy_vnd / 1e9, 2)
sell_bn = round(foreign_sell_vnd / 1e9, 2)

print(f"Today's HOSE foreign flow (current session):")
print(f"  Net: {net_bn:+,.2f} bn VND")
print(f"  Buy (In): {buy_bn:,.2f} bn VND")
print(f"  Sell (Out): {sell_bn:,.2f} bn VND")
print(f"  Stocks counted: {count}")

# Now try to get historical data
# Try HSX (Ho Chi Minh Stock Exchange) foreign trading report
print("\nTrying HSX historical foreign trading data...")

# Try different HSX endpoints
hsx_urls = [
    'https://www.hsx.vn/Modules/RsDealing/Report/ForeignTransaction.aspx?date=20260515',
    'https://www.hsx.vn/Modules/RsDealing/Report/ForeignTransaction.aspx',
]

for hurl in hsx_urls:
    try:
        hresp = requests.get(hurl, headers=headers, timeout=10)
        print(f"  {hurl[:60]}... Status: {hresp.status_code}, Length: {len(hresp.text)}")
    except Exception as e:
        print(f"  Failed: {e}")

# Try CafeF historical data API
print("\nTrying CafeF historical foreign trading data...")
cafef_hist_urls = [
    'https://scafefapi.cafef.vn/StockHandler/GetForeignTradeByDate?center=1&date=20260515',
    'https://scafefapi.cafef.vn/StockHandler/GetForeignTrade?center=1&from=20260511&to=20260516',
]

for curl in cafef_hist_urls:
    try:
        cresp = requests.get(curl, headers=headers, timeout=10)
        print(f"  {curl[:80]}... Status: {cresp.status_code}")
    except Exception as e:
        print(f"  Failed: {type(e).__name__}")

# Try vnstock with different approaches
print("\nTrying vnstock Trading with individual stock...")
try:
    from vnstock.api.trading import Trading
    
    # Try with a specific stock (SSI is the biggest broker)
    t = Trading(symbol='SSI', source='VCI')
    df = t.foreign_trade(start='2026-05-11', end='2026-05-16')
    print(f"  SSI foreign_trade: SUCCESS")
    print(f"  Columns: {df.columns.tolist()}")
    print(df.head())
except Exception as e:
    print(f"  SSI foreign_trade failed: {type(e).__name__}: {str(e)[:150]}")

# Try with ACB
try:
    t2 = Trading(symbol='ACB', source='VCI')
    df2 = t2.foreign_trade(start='2026-05-11', end='2026-05-16')
    print(f"  ACB foreign_trade: SUCCESS")
    print(df2.head())
except Exception as e:
    print(f"  ACB foreign_trade failed: {type(e).__name__}: {str(e)[:150]}")
