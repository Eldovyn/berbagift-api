import urllib.request
import json
import jwt
from utils.jwt import verify_access_token

class TokenController:
    def __init__(self):
        pass

    def get_market_stats(self):
        import requests
        try:
            url = "https://indodax.com/api/summaries"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            harga_sekarang = float(data['tickers']['xlm_idr']['last'])
            harga_24j_lalu = float(data['prices_24h']['xlmidr'])
            persentase = ((harga_sekarang - harga_24j_lalu) / harga_24j_lalu) * 100
            return {
                "message": "Market stats retrieved successfully",
                "data": {
                    "XLM": {
                        "price": int(harga_sekarang),
                        "change_24h": persentase
                    }
                },
                "errors": None
            }, 200
        except Exception as e_indodax:
            try:
                url = "https://api.coingecko.com/api/v3/simple/price"
                params = {"ids": "stellar", "vs_currencies": "idr", "include_24hr_change": "true"}
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers, params=params, timeout=5)
                response.raise_for_status()
                data = response.json()
                harga_sekarang = data['stellar']['idr']
                persentase = data['stellar']['idr_24h_change']
                return {
                    "message": "Market stats retrieved successfully (fallback to CoinGecko)",
                    "data": {
                        "XLM": {
                            "price": int(harga_sekarang),
                            "change_24h": persentase
                        }
                    },
                    "errors": None
                }, 200
            except Exception as e_coingecko:
                return {
                    "message": "Failed to fetch market stats",
                    "data": None,
                    "errors": {"indodax_error": str(e_indodax), "coingecko_error": str(e_coingecko)}
                }, 500

    def get_prices_waterfall(self):
        providers = [
            ("Pyth Oracle", self._fetch_pyth),
            ("CoinGecko", self._fetch_coingecko),
            ("Indodax", self._fetch_indodax)
        ]
        for name, fetch_func in providers:
            try:
                data = fetch_func()
                if data and data.get("XLM", 0) > 0:
                    return data, name
            except Exception as e:
                print(f"[!] Fallback Warning: Failed to fetch from {name}. Error: {e}")
                continue
        raise Exception("All pricing providers failed to return valid data.")

    def get_prices(self, authorization: str | None):
        if not authorization or not authorization.startswith("Bearer "):
            return {
                "message": "Authentication failed: Missing or invalid Authorization header",
                "data": None,
                "errors": None
            }, 401
        token = authorization.split(" ")[1]
        try:
            payload = verify_access_token(token)
        except jwt.ExpiredSignatureError:
            return {
                "message": "Token has expired",
                "data": None,
                "errors": None
            }, 401
        except jwt.InvalidTokenError:
            return {
                "message": "Invalid token",
                "data": None,
                "errors": None
            }, 401
        user_id_str = payload.get("sub")
        if not user_id_str:
            return {
                "message": "Invalid token payload",
                "data": None,
                "errors": None
            }, 401

        try:
            data, name = self.get_prices_waterfall()
            return {
                "message": f"Successfully retrieved token prices from {name}",
                "data": data,
                "provider": name,
                "errors": None
            }, 200
        except Exception as e:
            return {
                "message": str(e),
                "data": None,
                "provider": None,
                "errors": {
                    "api_error": "Pricing Service Unavailable"
                }
            }, 500



    def _fetch_pyth(self):
        import requests
        url = "https://hermes.pyth.network/v2/updates/price/latest"
        params = {
            "ids[]": [
                "0xb7a8eba68a997cd0210c2e1e4ee811ad2d174b3611c22d9ebf16f4cb7e9ba850",
                "0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a"
            ],
            "parsed": "true"
        }
        res = requests.get(url, params=params, timeout=10)
        res.raise_for_status()
        data = res.json().get("parsed", [])
        harga_usd = {}
        for item in data:
            feed_id = item["id"]
            price_data = item["price"]
            raw_price = int(price_data["price"])
            expo = int(price_data["expo"])
            harga_usd[feed_id] = raw_price * (10 ** expo)

        xlm_usd = harga_usd.get("b7a8eba68a997cd0210c2e1e4ee811ad2d174b3611c22d9ebf16f4cb7e9ba850", 0)
        usdc_usd = harga_usd.get("eaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a", 0)
        res_kurs = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
        res_kurs.raise_for_status()
        kurs_usd_idr = float(res_kurs.json().get("rates", {}).get("IDR", 16200))
        return {
            "XLM": int(round(xlm_usd * kurs_usd_idr)),
            "USDC": int(round(usdc_usd * kurs_usd_idr))
        }

    def _fetch_coingecko(self):
        import requests
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "stellar,usd-coin", "vs_currencies": "idr"}
        headers = {'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        res = requests.get(url, headers=headers, params=params, timeout=10)
        res.raise_for_status()
        data = res.json()
        return {
            "XLM": int(round(float(data.get("stellar", {}).get("idr", 0)))),
            "USDC": int(round(float(data.get("usd-coin", {}).get("idr", 0))))
        }

    def _fetch_indodax(self):
        import requests
        url = "https://indodax.com/api/tickers"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        tickers = res.json().get("tickers", {})
        return {
            "XLM": int(round(float(tickers.get("xlm_idr", {}).get("last", 0)))),
            "USDC": int(round(float(tickers.get("usdc_idr", {}).get("last", 0))))
        }
