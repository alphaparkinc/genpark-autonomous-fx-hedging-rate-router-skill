from client import AutonomousFxHedgingRateRouterClient
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

def main():
    client = AutonomousFxHedgingRateRouterClient()
    
    print("=== AUTONOMOUS FX HEDGING RATE ROUTER ===")
    scenarios = [
        ("EUR", "USD", 15000.0, 30, "international_credit"),
        ("GBP", "JPY", 8500.0, 3, "domestic_debit"),
        ("USD", "CNY", 50000.0, 60, "commercial_corporate")
    ]
    
    for src, tgt, amt, days, card in scenarios:
        res = client.route_fx_transaction(src, tgt, amt, settlement_days=days, card_type=card)
        print(f"
Transaction: {amt:,.2f} {src} -> {tgt} (Settlement: {days} days, Card: {card})")
        print(f"  - Mid-Market Rate: {res['mid_market_rate']} | Customer Rate: {res['effective_customer_rate']}")
        print(f"  - Converted Net: {res['converted_net_amount']:,.2f} {tgt}")
        print(f"  - Total Spread: {res['total_spread_bps']} bps (Vol Buffer: {res['spread_breakdown']['volatility_buffer_bps']} bps)")
        print(f"  - Forward Rate: {res['forward_parity_rate']} | Action: {res['recommended_hedge_action']}")

if __name__ == "__main__":
    main()
