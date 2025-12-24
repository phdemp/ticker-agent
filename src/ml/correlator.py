from typing import List, Dict
from loguru import logger
from .stats import calculate_z_score, is_anomaly
from .indicators import calculate_rsi, calculate_macd

class SignalCorrelator:
    def __init__(self):
        pass

    def correlate(self, ticker: str, sentiment_history: List[float], volume_history: List[float], price_history: List[float], current_sentiment: float, current_volume: float, current_price: float = 0.0, chain: str = "", chain_flows: List[Dict] = None) -> Dict:
        """
        Analyzes if there is a correlation between sentiment, volume spikes, and technical indicators.
        Returns a signal dict with entry/exit levels.
        """
        sent_z = calculate_z_score(current_sentiment, sentiment_history)
        vol_z = calculate_z_score(current_volume, volume_history)
        
        # Calculate Technical Indicators
        # We need at least some price history. If mocked, we might get empty lists.
        rsi = 50.0
        macd_data = {"macd": 0.0, "signal": 0.0, "hist": 0.0}
        
        if price_history and len(price_history) > 10:
             rsi = calculate_rsi(price_history)
             macd_data = calculate_macd(price_history)

        # Base confidence derived from Z-scores (0-60 points)
        confidence_score = 0.0
        if sent_z > 0 and vol_z > 0:
            confidence_score += (min(sent_z, 3.0) + min(vol_z, 3.0)) / 6.0 * 60
            
        # Refine with Indicators (0-40 points)
        # RSI Oversold (<30) is bullish (+20 points)
        # RSI Overbought (>70) is bearish (but for momentum strategies, maybe neutral/watch)
        if rsi < 30:
            confidence_score += 20
        elif rsi < 45: 
            confidence_score += 10
            
        # MACD Bullish Crossover (Hist > 0)
        if macd_data["hist"] > 0:
             confidence_score += 10
        
        # BOOST: Stablecoin Inflows (Chain Ecosystem Growth)
        # If the chain is receiving massive stablecoin inflows, tokens on it are likely to pump.
        inflow_boost = 0
        if chain and chain_flows:
            # find chain stats
            # Normalize chain names roughly (e.g. 'solana' -> 'Solana')
            chain_stat = next((c for c in chain_flows if c['chain'].lower() == chain.lower()), None)
            if chain_stat:
                net_flow = chain_stat.get('change_7d', 0)
                if net_flow > 50_000_000: # > $50M inflow
                    inflow_boost = 15
                elif net_flow > 10_000_000: # > $10M inflow
                    inflow_boost = 10
                elif net_flow > 0:
                    inflow_boost = 5
                    
                if inflow_boost > 0:
                     confidence_score += inflow_boost
                     logger.info(f"BOOST: {ticker} on {chain} gets +{inflow_boost} conf due to stablecoin inflows (${net_flow/1_000_000:.1f}M)")

        # Cap at 99
        confidence_score = min(confidence_score, 99.0)
            
        # Default Strategy Levels
        entry, target, stop = 0.0, 0.0, 0.0
        risk_reward = "1:2"
        direction = "NEUTRAL"
        
        if current_price > 0:
            # Dynamic targets based on volatility (width of bands? or just simple %)
            entry = current_price
            target = current_price * 1.10 
            stop = current_price * 0.95
            
        signal = {
            "ticker": ticker,
            "sentiment_z": sent_z,
            "volume_z": vol_z,
            "rsi": rsi,
            "macd": macd_data,
            "confidence": int(confidence_score),
            "entry": entry,
            "target": target,
            "stop": stop,
            "risk_reward": risk_reward,
            "direction": direction
        }
        
        # Logic: High Sentiment AND High Volume = Strong Buy Signal
        if confidence_score > 70:
            signal["direction"] = "BULLISH"
            signal["risk_reward"] = "1:3"
            
            if current_price > 0:
                signal["target"] = current_price * 1.25 # +25%
                signal["stop"] = current_price * 0.92   # -8%
            
            logger.info(f"SIGNAL DETECTED: {ticker} (Conf: {confidence_score:.0f}%, RSI: {rsi:.1f})")
            
        return signal
