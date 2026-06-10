import json
import math
import sys

def calc_sma(data, period):
    result = [None] * len(data)
    for i in range(period-1, len(data)):
        result[i] = sum(d["close"] for d in data[i-period+1:i+1]) / period
    return result

def calc_ema(data, period):
    result = [None] * len(data)
    multiplier = 2 / (period + 1)
    sma = sum(d["close"] for d in data[:period]) / period
    result[period-1] = sma
    for i in range(period, len(data)):
        result[i] = (data[i]["close"] - result[i-1]) * multiplier + result[i-1]
    return result

def calc_macd(data, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(data, fast)
    ema_slow = calc_ema(data, slow)
    macd_line = [None] * len(data)
    for i in range(len(data)):
        if ema_fast[i] is not None and ema_slow[i] is not None:
            macd_line[i] = ema_fast[i] - ema_slow[i]
    
    valid_macd = [(i, v) for i, v in enumerate(macd_line) if v is not None]
    signal_line = [None] * len(data)
    multiplier = 2 / (signal + 1)
    first_idx = valid_macd[signal-1][0]
    signal_line[first_idx] = sum(v for _, v in valid_macd[:signal]) / signal
    for j in range(signal, len(valid_macd)):
        i = valid_macd[j][0]
        prev_i = valid_macd[j-1][0]
        signal_line[i] = (macd_line[i] - signal_line[prev_i]) * multiplier + signal_line[prev_i]
    
    histogram = [None] * len(data)
    for i in range(len(data)):
        if macd_line[i] is not None and signal_line[i] is not None:
            histogram[i] = macd_line[i] - signal_line[i]
    
    return macd_line, signal_line, histogram

def calc_rsi(data, period=14):
    result = [None] * len(data)
    gains, losses = [], []
    for i in range(1, len(data)):
        change = data[i]["close"] - data[i-1]["close"]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    for i in range(period, len(gains)):
        if avg_loss == 0:
            result[i + 1] = 100
        else:
            rs = avg_gain / avg_loss
            result[i + 1] = 100 - (100 / (1 + rs))
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    return result

def calc_bollinger(data, period=20, std_dev=2):
    sma = calc_sma(data, period)
    upper = [None] * len(data)
    lower = [None] * len(data)
    for i in range(period-1, len(data)):
        window = [d["close"] for d in data[i-period+1:i+1]]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        upper[i] = mean + std_dev * std
        lower[i] = mean - std_dev * std
    return sma, upper, lower

def calc_atr(data, period=14):
    result = [None] * len(data)
    tr = [None] * len(data)
    for i in range(1, len(data)):
        hl = data[i]["high"] - data[i]["low"]
        hc = abs(data[i]["high"] - data[i-1]["close"])
        lc = abs(data[i]["low"] - data[i-1]["close"])
        tr[i] = max(hl, hc, lc)
    result[period] = sum(tr[1:period+1]) / period
    for i in range(period+1, len(data)):
        result[i] = (result[i-1] * (period-1) + tr[i]) / period
    return result

def analyze(name, code, data):
    closes = [d["close"] for d in data]
    volumes = [d["volume"] for d in data]
    highs = [d["high"] for d in data]
    lows = [d["low"] for d in data]
    n = len(data)
    latest = closes[-1]
    
    ma5 = calc_sma(data, 5)
    ma10 = calc_sma(data, 10)
    ma20 = calc_sma(data, 20)
    ma60 = calc_sma(data, 60)
    
    macd_line, signal_line, histogram = calc_macd(data)
    rsi = calc_rsi(data, 14)
    bb_mid, bb_upper, bb_lower = calc_bollinger(data, 20)
    atr = calc_atr(data, 14)
    
    avg_vol_5 = sum(volumes[-5:]) / 5
    avg_vol_20 = sum(volumes[-20:]) / 20
    vol_ratio = avg_vol_5 / avg_vol_20
    
    chg_5d = (closes[-1] / closes[-6] - 1) * 100 if n >= 6 else 0
    chg_10d = (closes[-1] / closes[-11] - 1) * 100 if n >= 11 else 0
    chg_20d = (closes[-1] / closes[-21] - 1) * 100 if n >= 21 else 0
    chg_60d = (closes[-1] / closes[0] - 1) * 100
    
    above_ma5 = latest > ma5[-1] if ma5[-1] else None
    above_ma10 = latest > ma10[-1] if ma10[-1] else None
    above_ma20 = latest > ma20[-1] if ma20[-1] else None
    above_ma60 = latest > ma60[-1] if ma60[-1] else None
    
    ma_align = "neutral"
    if ma5[-1] and ma10[-1] and ma20[-1]:
        if ma5[-1] > ma10[-1] > ma20[-1]:
            ma_align = "bullish"
        elif ma5[-1] < ma10[-1] < ma20[-1]:
            ma_align = "bearish"
    
    macd_val = macd_line[-1] or 0
    signal_val = signal_line[-1] or 0
    hist_val = histogram[-1] or 0
    macd_bull = macd_val > signal_val
    
    rsi_val = rsi[-1] or 50
    
    bb_pos = "middle"
    if bb_upper[-1] and bb_lower[-1]:
        if latest > bb_upper[-1]:
            bb_pos = "above_upper"
        elif latest < bb_lower[-1]:
            bb_pos = "below_lower"
        elif latest > bb_mid[-1]:
            bb_pos = "upper_half"
        else:
            bb_pos = "lower_half"
    
    atr_pct = (atr[-1] / latest * 100) if atr[-1] else 0
    
    rh20 = max(highs[-20:])
    rl20 = min(lows[-20:])
    pct_h = (latest / rh20 - 1) * 100
    pct_l = (latest / rl20 - 1) * 100
    
    # Scoring
    score = 5.0
    ma_signals = sum(1 for x in [above_ma5, above_ma10, above_ma20, above_ma60] if x)
    score += (ma_signals - 2) * 0.5
    
    if ma_align == "bullish": score += 1.0
    elif ma_align == "bearish": score -= 1.0
    
    if macd_bull: score += 0.5
    if macd_val > 0: score += 0.5
    if hist_val > 0: score += 0.3
    
    if 40 <= rsi_val <= 60: score += 0.5
    elif 30 <= rsi_val < 40: score += 0.3
    elif 60 < rsi_val <= 70: score -= 0.3
    elif rsi_val > 70: score -= 1.0
    elif rsi_val < 30: score -= 0.5
    
    if vol_ratio > 1.5: score += 0.3
    elif vol_ratio < 0.5: score -= 0.3
    
    if chg_20d > 20: score -= 1.0
    elif chg_20d > 10: score -= 0.3
    elif chg_20d < -20: score -= 1.5
    elif chg_20d < -10: score -= 0.5
    
    if pct_h > -5: score += 0.5
    elif pct_h < -20: score -= 1.0
    
    score = max(0, min(10, score))
    
    return {
        "latest_close": latest,
        "ma5": round(ma5[-1], 3) if ma5[-1] else None,
        "ma10": round(ma10[-1], 3) if ma10[-1] else None,
        "ma20": round(ma20[-1], 3) if ma20[-1] else None,
        "ma60": round(ma60[-1], 3) if ma60[-1] else None,
        "ma_alignment": ma_align,
        "above_ma5": above_ma5, "above_ma10": above_ma10,
        "above_ma20": above_ma20, "above_ma60": above_ma60,
        "macd": round(macd_val, 3), "macd_signal": round(signal_val, 3),
        "macd_histogram": round(hist_val, 3), "macd_bullish": macd_bull,
        "rsi": round(rsi_val, 1),
        "bb_position": bb_pos, "atr_pct": round(atr_pct, 2),
        "vol_ratio": round(vol_ratio, 2),
        "change_5d": round(chg_5d, 1), "change_10d": round(chg_10d, 1),
        "change_20d": round(chg_20d, 1), "change_60d": round(chg_60d, 1),
        "pct_from_20d_high": round(pct_h, 1),
        "pct_from_20d_low": round(pct_l, 1),
        "technical_score": round(score, 1),
    }

# Load all data from the JSON files we already fetched
# For brevity, I'll process each one

if __name__ == "__main__":
    # Read data from stdin
    all_input = json.load(sys.stdin)
    results = {}
    for key, val in all_input.items():
        if "data" in val:
            results[key] = analyze(val["name"], val.get("code", key), val["data"])
            results[key]["name"] = val["name"]
            results[key]["code"] = val.get("code", key)
    print(json.dumps(results, ensure_ascii=False, indent=2))
