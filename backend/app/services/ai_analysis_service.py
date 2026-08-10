import ollama


class AIAnalysisService:

    @staticmethod
    def generate_trade_analysis(data: dict):

        signal = data["signal"]["signal"]

        # Deterministic interpretation
        trend = (
            "bullish"
            if data["close_price"] > data["ema20"]
            else "bearish"
        )

        momentum = (
            "strong"
            if data["rsi"] > 55
            else "weak"
        )

        prompt = f"""
You are an English-speaking swing trading assistant.

STRICT RULES:
- Respond ONLY in English.
- Do NOT use Chinese or any other language.
- Keep response under 50 words.
- Do NOT contradict provided facts.

Facts:
- Current trend is {trend}
- Momentum is {momentum}
- RSI is {data['rsi']}
- Signal is {signal}

Generate:
- short interpretation
- risk comment
- concise outlook
"""

        try:

            response = ollama.chat(
                model="qwen2.5:3b",
                options={
                    "temperature": 0.1
                },
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            return response["message"]["content"]

        except Exception as e:

            return f"AI analysis failed: {str(e)}"