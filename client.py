import math, sys
sys.stdout.reconfigure(encoding='utf-8')

class AutonomousFxHedgingRateRouterClient:
    """
    Autonomous multi-currency FX router that triangulates foreign exchange rates,
    applies dynamic volatility buffers based on settlement maturity, models card scheme fees,
    and calculates forward lock hedging parity.
    """
    def __init__(self):
        # Base benchmark rates relative to USD (USD = 1.0)
        self.usd_base_rates = {
            "USD": 1.0000,
            "EUR": 1.0850,
            "GBP": 1.2950,
            "JPY": 0.0066,
            "CNY": 0.1380,
            "CAD": 0.7250,
            "AUD": 0.6550,
            "SGD": 0.7600,
            "CHF": 1.1350
        }
        # Annualized volatility index
        self.annual_volatility = {
            ("EUR", "USD"): 0.065, ("USD", "EUR"): 0.065,
            ("GBP", "USD"): 0.082, ("USD", "GBP"): 0.082,
            ("JPY", "USD"): 0.115, ("USD", "JPY"): 0.115,
            ("CNY", "USD"): 0.038, ("USD", "CNY"): 0.038,
            ("CAD", "USD"): 0.052, ("USD", "CAD"): 0.052,
            ("AUD", "USD"): 0.089, ("USD", "AUD"): 0.089,
            ("EUR", "GBP"): 0.055, ("GBP", "EUR"): 0.055
        }
        # Risk-free interest rates (annualized) for forward parity
        self.interest_rates = {
            "USD": 0.0475, "EUR": 0.0325, "GBP": 0.0450,
            "JPY": 0.0025, "CNY": 0.0210, "CAD": 0.0400,
            "AUD": 0.0410, "SGD": 0.0310, "CHF": 0.0125
        }
        # Interchange / scheme markups
        self.scheme_markups = {
            "domestic_debit": 0.003,
            "domestic_credit": 0.012,
            "international_debit": 0.018,
            "international_credit": 0.025,
            "commercial_corporate": 0.029
        }

    def get_cross_rate(self, src, tgt):
        src = src.upper()
        tgt = tgt.upper()
        if src not in self.usd_base_rates or tgt not in self.usd_base_rates:
            raise ValueError(f"Unsupported currency pair: {src}/{tgt}")
        # Rate: units of target currency per 1 unit of source currency
        # Since base_rates are USD per 1 unit of Currency:
        # 1 Unit Src = usd_base_rates[src] USD
        # 1 USD = (1.0 / usd_base_rates[tgt]) Tgt
        # Hence: 1 Src = usd_base_rates[src] / usd_base_rates[tgt] Tgt
        return self.usd_base_rates[src] / self.usd_base_rates[tgt]

    def route_fx_transaction(self, source_currency, target_currency, amount, settlement_days=0, card_type="international_credit"):
        src = source_currency.upper()
        tgt = target_currency.upper()
        
        mid_market_rate = self.get_cross_rate(src, tgt)
        base_target_amount = amount * mid_market_rate
        
        vol = self.annual_volatility.get((src, tgt), self.annual_volatility.get((tgt, src), 0.075))
        time_factor = math.sqrt(max(1, settlement_days) / 365.0)
        # 95% confidence volatility spread (Z = 1.96) scaled by half spread
        vol_buffer_rate = vol * time_factor * 1.96 * 0.5
        
        scheme_fee_rate = self.scheme_markups.get(card_type, 0.025)
        total_spread_rate = round(0.0040 + vol_buffer_rate + scheme_fee_rate, 5) # 40 bps base spread
        
        customer_exchange_rate = mid_market_rate * (1.0 - total_spread_rate)
        converted_net_amount = amount * customer_exchange_rate
        spread_fee_target = base_target_amount - converted_net_amount
        
        # Forward Contract Parity Pricing
        t_years = max(1, settlement_days) / 365.0
        r_src = self.interest_rates.get(src, 0.035)
        r_tgt = self.interest_rates.get(tgt, 0.035)
        forward_rate = mid_market_rate * ((1.0 + r_tgt * t_years) / (1.0 + r_src * t_years))
        
        recommend_hedge = settlement_days >= 7 and (vol >= 0.06 or (amount * self.usd_base_rates[src]) >= 10000.0)
        hedge_strategy = "EXECUTE_FORWARD_LOCK" if recommend_hedge else "SPOT_EXECUTION"
        
        return {
            "status": "success",
            "source_currency": src,
            "target_currency": tgt,
            "source_amount": round(amount, 2),
            "mid_market_rate": round(mid_market_rate, 6),
            "effective_customer_rate": round(customer_exchange_rate, 6),
            "converted_net_amount": round(converted_net_amount, 2),
            "total_spread_bps": int(total_spread_rate * 10000),
            "spread_breakdown": {
                "base_market_spread_bps": 40,
                "volatility_buffer_bps": int(vol_buffer_rate * 10000),
                "interchange_scheme_fee_bps": int(scheme_fee_rate * 10000)
            },
            "settlement_window_days": settlement_days,
            "forward_parity_rate": round(forward_rate, 6),
            "recommended_hedge_action": hedge_strategy,
            "estimated_fx_fee_saved": round(spread_fee_target * 0.40, 2) if recommend_hedge else 0.0
        }
