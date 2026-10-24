import sys, json
from client import AutonomousFxHedgingRateRouterClient
sys.stdout.reconfigure(encoding='utf-8')

def handle_mcp():
    client = AutonomousFxHedgingRateRouterClient()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(json.dumps({"status": "ready", "skill": "genpark-autonomous-fx-hedging-rate-router-skill"}))
        return
    req = json.loads(sys.stdin.read() or "{}")
    src = req.get("source_currency", "EUR")
    tgt = req.get("target_currency", "USD")
    amt = float(req.get("amount", 1000.0))
    days = int(req.get("settlement_days", 0))
    res = client.route_fx_transaction(src, tgt, amt, settlement_days=days)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    handle_mcp()
