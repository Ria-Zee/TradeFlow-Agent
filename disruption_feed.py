import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.tools import check_disruption_signals, get_fx_rate
from datetime import datetime

FX_SPIKE_THRESHOLD = 0.03
FX_BASELINE = None

def monitor_once(origin="China", destination_port="apapa", product="goods") -> dict:
    global FX_BASELINE
    signals = check_disruption_signals(origin, destination_port)
    fx = get_fx_rate("USD", "NGN")
    current_rate = fx.get("rate", 0)

    auto_alerts = []

    if not current_rate:
        auto_alerts.append("FX ALERT: USD/NGN live rate unavailable — re-analysis recommended when data returns")
    elif FX_BASELINE is None or FX_BASELINE == 0:
        FX_BASELINE = current_rate
    else:
        change_pct = abs(current_rate - FX_BASELINE) / FX_BASELINE
        if change_pct >= FX_SPIKE_THRESHOLD:
            direction = "spiked UP" if current_rate > FX_BASELINE else "dropped DOWN"
            auto_alerts.append(
                f"FX ALERT: USD/NGN {direction} {change_pct*100:.1f}% "
                f"from {FX_BASELINE:.2f} to {current_rate:.2f} — re-analysis recommended"
            )
            FX_BASELINE = current_rate

    all_signals = signals.get("disruption_signals", []) + auto_alerts
    risk_level = signals.get("risk_level", "LOW")
    if auto_alerts:
        risk_level = "HIGH"

    return {
        "timestamp": datetime.now().isoformat(),
        "risk_level": risk_level,
        "current_usd_ngn": current_rate,
        "fx_baseline": FX_BASELINE,
        "disruption_signals": all_signals,
        "news_headlines": signals.get("news_headlines", []),
        "requires_reanalysis": len(all_signals) > 0
    }

def run_disruption_monitor(origin="China", destination_port="apapa",
                            product="goods", cycles=3, interval_seconds=5):
    print("\n" + "="*60)
    print("TRADEFLOW REAL-TIME DISRUPTION FEED")
    print("="*60)
    print(f"Monitoring: {origin} → {destination_port.upper()}")
    print(f"Product: {product}")
    print(f"Checking every {interval_seconds}s for {cycles} cycles")
    print("="*60)

    for cycle in range(1, cycles + 1):
        print(f"\n[Cycle {cycle}/{cycles}] {datetime.now().strftime('%H:%M:%S')}")
        result = monitor_once(origin, destination_port, product)
        print(f"  USD/NGN: {result['current_usd_ngn']} | Risk: {result['risk_level']}")

        if result['disruption_signals']:
            print("  ⚠️  ACTIVE SIGNALS:")
            for s in result['disruption_signals']:
                print(f"    ! {s}")
        else:
            print("  ✅ No disruption signals detected")

        if result['news_headlines']:
            print("  📰 Live Headlines:")
            for h in result['news_headlines'][:2]:
                print(f"    → {h[:80]}")

        if result['requires_reanalysis']:
            print("\n  🔴 PROACTIVE ALERT: Conditions changed — TradeFlow recommends re-running analysis")

        if cycle < cycles:
            time.sleep(interval_seconds)

    print("\n" + "="*60)
    print("DISRUPTION MONITORING COMPLETE")
    print("="*60)

if __name__ == "__main__":
    run_disruption_monitor(
        origin="China",
        destination_port="apapa",
        product="Samsung smartphones",
        cycles=3,
        interval_seconds=3
    )
