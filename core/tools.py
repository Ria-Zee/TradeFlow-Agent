import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import json
from datetime import datetime

def get_fx_rate(base_currency: str, target_currency: str) -> dict:
    base = base_currency.lower()
    target = target_currency.lower()
    providers = [
        (
            "fawazahmed0/currency-api",
            f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base}.json",
            lambda data: data[base][target],
        ),
        (
            "open.er-api.com",
            f"https://open.er-api.com/v6/latest/{base_currency.upper()}",
            lambda data: data["rates"][target_currency.upper()],
        ),
    ]
    errors = []
    for source, url, extractor in providers:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TradeFlow/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
                rate = extractor(data)
                return {
                    "base": base_currency.upper(),
                    "target": target_currency.upper(),
                    "rate": round(rate, 4),
                    "timestamp": datetime.now().isoformat(),
                    "source": source,
                    "status": "LIVE"
                }
        except Exception as e:
            errors.append(f"{source}: {e}")
    return {
        "base": base_currency.upper(),
        "target": target_currency.upper(),
        "rate": None,
        "error": " | ".join(errors),
        "status": "FAILED"
    }

def get_trade_news(product: str = "", origin: str = "", destination: str = "Nigeria") -> dict:
    search_terms = [
        f"Nigeria import {product} trade" if product else "Nigeria import trade",
        "Apapa port Lagos shipping Nigeria",
        "naira exchange rate Nigeria CBN",
    ]
    articles = []
    for term in search_terms[:2]:
        try:
            encoded = urllib.parse.quote(term)
            url = f"https://news.google.com/rss/search?q={encoded}&hl=en-NG&gl=NG&ceid=NG:en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 TradeFlow/1.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                content = response.read().decode("utf-8", errors="ignore")
                root = ET.fromstring(content)
                items = root.findall(".//item")[:3]
                for item in items:
                    title = item.findtext("title", "")
                    pub_date = item.findtext("pubDate", "")
                    if title:
                        articles.append({
                            "title": title[:150],
                            "published": pub_date,
                            "query": term
                        })
        except Exception:
            continue
    return {
        "articles": articles[:6],
        "count": len(articles),
        "timestamp": datetime.now().isoformat(),
        "status": "LIVE" if articles else "NO_RESULTS",
        "source": "Google News RSS Nigeria"
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
        "note": "Estimates based on typical market rates. Get live quotes from freight forwarders."
    }

def check_disruption_signals(origin: str = "China", destination_port: str = "apapa") -> dict:
    fx = get_fx_rate("USD", "NGN")
    news = get_trade_news(destination=destination_port)
    
    disruption_signals = []
    risk_level = "LOW"
    
    if fx["status"] == "LIVE" and fx["rate"]:
        rate = fx["rate"]
        if rate > 1500:
            disruption_signals.append(f"CRITICAL: USD/NGN at {rate} - extreme Naira depreciation")
            risk_level = "HIGH"
        elif rate > 1400:
            disruption_signals.append(f"WARNING: USD/NGN at {rate} - significant Naira weakness")
            risk_level = "MEDIUM"

    port_risk_keywords = ["strike", "closure", "shutdown", "congestion", "block", "suspend", "halt"]
    for article in news.get("articles", []):
        title_lower = article["title"].lower()
        for keyword in port_risk_keywords:
            if keyword in title_lower:
                disruption_signals.append(f"NEWS ALERT: {article['title'][:100]}")
                risk_level = "HIGH"
                break

    return {
        "risk_level": risk_level,
        "disruption_signals": disruption_signals,
        "current_usd_ngn": fx.get("rate"),
        "news_headlines": [a["title"] for a in news.get("articles", [])[:3]],
        "timestamp": datetime.now().isoformat(),
        "status": "LIVE_MONITORING"
    }

def get_trade_context(product: str, origin: str, destination: str) -> dict:
    fx_usd_ngn = get_fx_rate("USD", "NGN")
    fx_usd_cny = get_fx_rate("USD", "CNY")
    fx_cny_ngn = get_fx_rate("CNY", "NGN")
    shipping = get_shipping_estimate(origin, destination)
    news = get_trade_news(product, origin, destination)
    disruptions = check_disruption_signals(origin, destination)
    
    fx_statuses = [fx_usd_ngn.get("status"), fx_usd_cny.get("status"), fx_cny_ngn.get("status")]
    fx_quality = "LIVE_FX" if all(status == "LIVE" for status in fx_statuses) else "FX_UNAVAILABLE"
    news_quality = "LIVE_NEWS" if news.get("status") == "LIVE" else "NEWS_UNAVAILABLE"

    return {
        "fx_rates": {
            "USD_NGN": fx_usd_ngn,
            "USD_CNY": fx_usd_cny,
            "CNY_NGN": fx_cny_ngn,
        },
        "shipping_estimate": shipping,
        "trade_news": news,
        "disruption_monitor": disruptions,
        "trade_lane": f"{origin} to {destination}",
        "product": product,
        "data_timestamp": datetime.now().isoformat(),
        "data_quality": f"{fx_quality} + {news_quality} + ESTIMATED_SHIPPING"
    }

if __name__ == "__main__":
    print("Testing all TradeFlow tools...")
    ctx = get_trade_context("Samsung smartphones", "China", "apapa")
    print(f"USD/NGN: {ctx['fx_rates']['USD_NGN']['rate']} (LIVE)")
    print(f"News articles: {ctx['trade_news']['count']}")
    print(f"Disruption risk: {ctx['disruption_monitor']['risk_level']}")
    print(f"Disruption signals: {len(ctx['disruption_monitor']['disruption_signals'])}")
    for headline in ctx['trade_news']['articles'][:3]:
        print(f"  - {headline['title'][:80]}")
