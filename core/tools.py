import urllib.request
import json
from datetime import datetime

def get_fx_rate(base_currency: str, target_currency: str) -> dict:
    try:
        base = base_currency.lower()
        target = target_currency.lower()
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json"
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            rate = data[base][target]
            return {
                "base": base_currency.upper(),
                "target": target_currency.upper(),
                "rate": round(rate, 4),
                "timestamp": datetime.utcnow().isoformat(),
                "source": "fawazahmed0/currency-api",
                "status": "LIVE"
            }
    except Exception as e:
        return {
            "base": base_currency.upper(),
            "target": target_currency.upper(),
            "rate": None,
            "error": str(e),
            "status": "FAILED"
        }

def get_shipping_estimate(origin_country: str, destination_port: str, container_type: str = "20ft") -> dict:
    estimates = {
        ("china", "apapa"): {"min": 1800, "max": 2800, "transit_days": "25-35"},
        ("china", "tin can island"): {"min": 1900, "max": 2900, "transit_days": "25-35"},
        ("china", "cotonou"): {"min": 1600, "max": 2400, "transit_days": "22-30"},
        ("china", "tema"): {"min": 1700, "max": 2500, "transit_days": "24-32"},
        ("india", "apapa"): {"min": 1200, "max": 2000, "transit_days": "18-25"},
        ("india", "cotonou"): {"min": 1100, "max": 1800, "transit_days": "16-22"},
        ("uk", "apapa"): {"min": 800, "max": 1400, "transit_days": "12-18"},
        ("usa", "apapa"): {"min": 1500, "max": 2500, "transit_days": "20-28"},
    }
    key = (origin_country.lower(), destination_port.lower())
    estimate = estimates.get(key, {"min": 1500, "max": 3000, "transit_days": "20-40"})
    return {
        "origin": origin_country,
        "destination_port": destination_port,
        "container_type": container_type,
        "freight_usd_min": estimate["min"],
        "freight_usd_max": estimate["max"],
        "transit_days": estimate["transit_days"],
        "status": "ESTIMATED",
        "note": "Estimates based on typical market rates. Always obtain live quotes from freight forwarders."
    }

def get_trade_context(product: str, origin: str, destination: str) -> dict:
    fx_usd_ngn = get_fx_rate("USD", "NGN")
    fx_usd_cny = get_fx_rate("USD", "CNY")
    fx_cny_ngn = get_fx_rate("CNY", "NGN")
    shipping = get_shipping_estimate(origin, destination)
    return {
        "fx_rates": {
            "USD_NGN": fx_usd_ngn,
            "USD_CNY": fx_usd_cny,
            "CNY_NGN": fx_cny_ngn,
        },
        "shipping_estimate": shipping,
        "trade_lane": f"{origin} to {destination}",
        "product": product,
        "data_timestamp": datetime.utcnow().isoformat(),
        "data_quality": "LIVE_FX_RATES + ESTIMATED_SHIPPING"
    }
