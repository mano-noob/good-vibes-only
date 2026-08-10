from app.services.trading_service import TradingService

TOP_RS_STOCKS = [

    "HINDALCO.NS",
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "NESTLEIND.NS",
    "TATASTEEL.NS",
    "APOLLOHOSP.NS",
    "JSWSTEEL.NS",
    "COALINDIA.NS",
    "BAJAJ-AUTO.NS",
    "GRASIM.NS",
    "EICHERMOT.NS",
    "ASIANPAINT.NS",
    "SHRIRAMFIN.NS",
    "SBIN.NS"

]


class ScannerService:

    @staticmethod
    def scan_market():

        results = []

        for symbol in TOP_RS_STOCKS:

            try:

                print(f"Scanning {symbol}")

                analysis = (
                    TradingService
                    .analyze_stock(symbol)
                )

                results.append(analysis)

            except Exception as e:

                results.append({

                    "symbol": symbol,

                    "error": str(e)

                })

        return results