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
