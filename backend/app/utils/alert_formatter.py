def format_trade_alert(result: dict):

    return f"""
🚨 SWING TRADE ALERT 🚨

Symbol: {result['symbol']}

Signal: {result['signal']['signal']}

Price: {result['close_price']}

EMA20: {result['ema20']}

RSI: {result['rsi']}

AI Analysis:
{result['ai_analysis']}
"""