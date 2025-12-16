from typing import List, Dict
from loguru import logger
from .stats import calculate_z_score, is_anomaly

class SignalCorrelator:
    def __init__(self):
        pass

    def correlate(self, ticker: str, sentiment_history: List[float], volume_history: List[float], current_sentiment: float, current_volume: float, current_price: float = 0.0) -> Dict:
        """
        Analyzes if there is a correlation between sentiment and volume spikes.
        Returns a signal dict with entry/exit levels.
        """
        sent_z = calculate_z_score(current_sentiment, sentiment_history)
        vol_z = calculate_z_score(current_volume, volume_history)
        
        signal = {
            "ticker": ticker,
            "sentiment_z": sent_z,
            "volume_z": vol_z,
            "is_pump": False,
            "confidence": 0.0,
            "entry": 0.0,
            "target": 0.0,
            "stop": 0.0
        }
        
        # Logic: High Sentiment AND High Volume = Strong Buy Signal
        if is_anomaly(sent_z, 1.5) and is_anomaly(vol_z, 1.5):
            signal["is_pump"] = True
            signal["confidence"] = (abs(sent_z) + abs(vol_z)) / 2.0
            
            # Calculate Levels (Simple Strategy)
            # Entry: Current Price
            # Target: +15%
            # Stop: -5%
            if current_price > 0:
                signal["entry"] = current_price
                signal["target"] = current_price * 1.15
                signal["stop"] = current_price * 0.95
            
            logger.info(f"PUMP SIGNAL DETECTED: {ticker} (Conf: {signal['confidence']:.2f})")
            
        return signal

    def correlate(self, ticker: str, sentiment_history: List[float], volume_history: List[float], current_sentiment: float, current_volume: float, current_price: float = 0.0) -> Dict:
        """
        Analyzes if there is a correlation between sentiment and volume spikes.
        Returns a signal dict with entry/exit levels.
        """
        sent_z = calculate_z_score(current_sentiment, sentiment_history)
        vol_z = calculate_z_score(current_volume, volume_history)
        
        # Base confidence derived from Z-scores
        confidence_score = 0.0
        if sent_z > 0 and vol_z > 0:
            confidence_score = (min(sent_z, 3.0) + min(vol_z, 3.0)) / 6.0 * 100 # Normalize to 0-100
            
        # Default Strategy Levels (Neutral/Potential)
        entry, target, stop = 0.0, 0.0, 0.0
        risk_reward = "1:2"
        direction = "NEUTRAL"
        
        if current_price > 0:
            # Default levels (even for neutral signals, to show on dashboard)
            entry = current_price
            target = current_price * 1.10 # +10% target
            stop = current_price * 0.95   # -5% stop (tight stop for non-signals)
            
        signal = {
            "ticker": ticker,
            "sentiment_z": sent_z,
            "volume_z": vol_z,
            "is_pump": False,
            "confidence": int(confidence_score),
            "entry": entry,
            "target": target,
            "stop": stop,
            "risk_reward": risk_reward,
            "direction": direction
        }
        
        # Logic: High Sentiment AND High Volume = Strong Buy Signal
        if sent_z > 1.0 and vol_z > 1.0: 
            signal["is_pump"] = True
            signal["direction"] = "BULLISH"
            signal["risk_reward"] = "1:2"
            
            # Stronger levels for pump signals
            if current_price > 0:
                signal["entry"] = current_price
                signal["target"] = current_price * 1.20 # +20%
                signal["stop"] = current_price * 0.90   # -10% stop (wider stop for volatility)
            
            logger.info(f"SIGNAL DETECTED: {ticker} (Conf: {confidence_score:.0f}%)")
            
        return signal
