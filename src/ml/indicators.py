from typing import List, Dict, Union
import math

def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """
    Calculates the Relative Strength Index (RSI).
    Returns 50.0 if not enough data.
    """
    if len(prices) < period + 1:
        return 50.0

    # Calculate changes
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    # Get initial gains/losses
    seed = deltas[:period]
    up = sum(d for d in seed if d > 0) / period
    down = -sum(d for d in seed if d < 0) / period
    
    if down == 0:
        return 100.0
        
    rs = up / down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    
    # Smoothed calculation for the rest
    for i in range(period, len(deltas)):
        delta = deltas[i]
        gain = delta if delta > 0 else 0.0
        loss = -delta if delta < 0 else 0.0
        
        up = (up * (period - 1) + gain) / period
        down = (down * (period - 1) + loss) / period
        
        if down == 0:
            rsi = 100.0
        else:
            rs = up / down
            rsi = 100.0 - (100.0 / (1.0 + rs))
            
    return rsi

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """
    Calculates MACD, Signal line, and Histogram.
    Returns 0.0s if not enough data.
    """
    if len(prices) < slow + signal:
        return {"macd": 0.0, "signal": 0.0, "hist": 0.0}

    # Helper for EMA
    def calculate_ema(data: List[float], span: int) -> List[float]:
        alpha = 2 / (span + 1)
        ema = [data[0]]
        for price in data[1:]:
            ema.append(alpha * price + (1 - alpha) * ema[-1])
        return ema

    # Calculate EMAs
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)

    # Calculate MACD Line
    # We need to align the series. ema_slow is valid from index 'slow-1' conceptually, 
    # but the lists are same length.
    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        macd_line.append(f - s)
        
    # Calculate Signal Line (EMA of MACD)
    # signal line needs 'signal' amount of macd points
    if len(macd_line) < signal:
         return {"macd": macd_line[-1], "signal": 0.0, "hist": 0.0}

    signal_line_series = calculate_ema(macd_line, signal)
    
    current_macd = macd_line[-1]
    current_signal = signal_line_series[-1]
    current_hist = current_macd - current_signal
    
    return {
        "macd": current_macd,
        "signal": current_signal,
        "hist": current_hist
    }

def calculate_bollinger_bands(prices: List[float], period: int = 20, num_std: float = 2.0) -> Dict[str, float]:
    """
    Calculates Bollinger Bands (Upper, Middle, Lower).
    """
    if len(prices) < period:
        return {"upper": 0.0, "middle": 0.0, "lower": 0.0}
        
    recent = prices[-period:]
    sma = sum(recent) / period
    
    variance = sum((p - sma) ** 2 for p in recent) / period
    std_dev = math.sqrt(variance)
    
    return {
        "upper": sma + (std_dev * num_std),
        "middle": sma,
        "lower": sma - (std_dev * num_std)
    }
