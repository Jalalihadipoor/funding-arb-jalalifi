import time
import requests

# ——— تنظیمات شما ———
TELEGRAM_TOKEN = "7448804929:AAGg4w7OcLdsH2QZN7K7Q0lWlHTEAMDAH10"
CHAT_ID         = "-1001564864231"
MIN_DIFF        = 0.5  # درصد اختلاف حداقل

EXCHANGES = {
    "tobit": {
        "funding_url": "https://api.toobit.com/v1/funding_rates"
    },
    "lbank": {
        "funding_url": "https://api.lbank.info/v2/funding_rate"
    },
    "xt": {
        "funding_url": "https://api.xt.com/api/v2/funding_rate"
    }
}

def fetch_funding(exchange):
    url = EXCHANGES[exchange]["funding_url"]
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    # فرض: data لیستی از دیکشنری‌های {"symbol": "...", "funding_rate": float}
    return { item["symbol"]: float(item["funding_rate"]) for item in data }

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()

def main():
    # اجرا فقط از ساعت 08:00 UTC به بعد
    if time.gmtime().tm_hour < 8:
        return

    # واکشی نرخ فاندینگ هر صرافی
    rates = {}
    for ex in EXCHANGES:
        try:
            rates[ex] = fetch_funding(ex)
        except Exception as e:
            print(f"Error fetching {ex}: {e}")

    # تقاطع نمادها
    symbols = set.intersection(*(set(d.keys()) for d in rates.values()))
    alerts = []

    for sym in symbols:
        vals = [(ex, rates[ex][sym]) for ex in rates]
        vals_sorted = sorted(vals, key=lambda x: x[1])
        low_ex, low_rate   = vals_sorted[0]
        high_ex, high_rate = vals_sorted[-1]
        diff = (high_rate - low_rate) * 100
        if diff >= MIN_DIFF:
            msg = (
                f"*{sym}*: اختلاف فاندینگ `{diff:.2f}%`\n"
                f"لانگ ➡️ {high_ex} ({high_rate:.4f})\n"
                f"شورت ➡️ {low_ex} ({low_rate:.4f})"
            )
            alerts.append(msg)

    if alerts:
        send_telegram("\n\n".join(alerts))

if __name__ == "__main__":
    main()
