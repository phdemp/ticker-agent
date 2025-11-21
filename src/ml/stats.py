import pandas as pd
import numpy as np

def calculate_z_score(current_value: float, history: list) -> float:
    """
    Calculates the Z-Score of the current value against a history of values.
    Z = (X - Mean) / StdDev
    """
    if not history or len(history) < 2:
        return 0.0
    
    series = pd.Series(history)
    mean = series.mean()
    std = series.std()
    
    if std == 0:
        return 0.0
        
    return (current_value - mean) / std

def is_anomaly(z_score: float, threshold: float = 2.0) -> bool:
    """
    Returns True if the Z-Score is above the threshold (statistically significant).
    """
    return abs(z_score) > threshold
