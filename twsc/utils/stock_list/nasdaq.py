import httpx
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# Get list of strong buy/sell stocks from API
"""
https://api.nasdaq.com/api/screener/stocks?tableonly=false&limit=250&exchange=NASDAQ&exsubcategory=NCM&marketcap=mega|large|mid|small&recommendation=strong_buy|strong_sell
    "data": {
        "filters": {
            "region": [ { "name": "Africa", "value": "africa" }, ... ],
            "country": [ { "name": "United States", "value": "united_states" }, ... ],
            "exchange": [ { "name": "NASDAQ", "value": "NASDAQ" }, { "name": "NYSE", "value": "NYSE" }, ... ],
            "sector": [ { "name": "Technology", "value": "technology" }, ... ],
            "recommendation": [ { "name": "Strong Buy", "value": "strong_buy" }, { "name": "Buy", "value": "buy" }, ... ],
            "marketcap": [ { "name": "Mega (>$200B)", "value": "mega" }, { "name": "Large ($10B-$200B)", "value": "large" }, ... ],
            "exsubcategory": [ { "name": "Global Select", "value": "NGS" }, { "name": "Global Market", "value": "NGM" }, ... ]
        },
        "table": {
            "asOf": null,
            "headers": {
                "symbol": "Symbol",
                "name": "Name",
                "lastsale": "Last Sale",
                "netchange": "Net Change",
                "pctchange": "% Change",
                "marketCap": "Market Cap"
            },
            "rows": [
                {
                    "symbol": "RKLB",
                    "name": "Rocket Lab Corporation Common Stock",
                    "lastsale": "$39.10",
                    "netchange": "-0.04",
                    "pctchange": "-0.102%",
                    "marketCap": "18,042,006,566",
                    "url": "/market-activity/stocks/rklb"
                },
                ...
            ]
        },
        "totalrecords": 127,
        "asof": "Last price as of Jul 10, 2025"
    },
    "message": null,
    "status": {
        "rCode": 200,
        "bCodeMessage": null,
        "developerMessage": null
    }
}
"""

"""
https://api.nasdaq.com/api/screener/stocks?tableonly=false&limit=250&exchange=NASDAQ&exsubcategory=NCM&marketcap=mega|large|mid|small&recommendation=strong_buy|strong_sell&download=true
{
    "data": {
        "asOf": null,
        "headers": {
            "symbol": "Symbol",
            "name": "Name",
            "lastsale": "Last Sale",
            "netchange": "Net Change",
            "pctchange": "% Change",
            "marketCap": "Market Cap",
            "country": "Country",
            "ipoyear": "IPO Year",
            "volume": "Volume",
            "sector": "Sector",
            "industry": "Industry",
            "url": "Url"
        },
        "rows": [
            {
                "symbol": "ABL",
                "name": "Abacus Global Management Inc. Class A Common Stock",
                "lastsale": "$5.20",
                "netchange": "0.00",
                "pctchange": "0.00%",
                "volume": "587836",
                "marketCap": "503635803.00",
                "country": "United States",
                "ipoyear": "2020",
                "industry": "Investment Managers",
                "sector": "Finance",
                "url": "/market-activity/stocks/abl"
            },
            ...
        ]
    },
    "message": null,
    "status": {
        "rCode": 200,
        "bCodeMessage": null,
        "developerMessage": null
    }
}
"""

def get_nasdaq_stocks_list(
    exchange: list = ["NASDAQ"],
    exsubcategory: list = ["NCM"],  # NCM for NASDAQ
    marketcap: list = ["mega","large","mid","small"],
    recommendation: list = ["strong_buy","strong_sell"],
    limit: int = 250
    
):
    """
    Fetch strong buy/sell stocks from NASDAQ screener API.
    Returns:
        pd.DataFrame: DataFrame containing stock information
    """
    screener_url = "https://api.nasdaq.com/api/screener/stocks?tableonly=false"
    screener_url += f"&limit={limit}" if limit else ""
    screener_url += f"&exchange={'|'.join(exchange)}" if exchange else ""
    screener_url += f"&exsubcategory={'|'.join(exsubcategory)}" if exsubcategory else ""
    screener_url += f"&marketcap={'|'.join(marketcap)}" if marketcap else ""
    screener_url += f"&recommendation={'|'.join(recommendation)}" if recommendation else ""
    screener_url += "&download=true"  # To get the full data including headers and rows
    
    # Set headers to mimic a browser request
    # old user-agent might cause timeout, so use a more recent one https://www.whatismybrowser.com/detect/what-http-headers-is-my-browser-sending/
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
    }

    try:
        response = httpx.get(screener_url, headers=headers)
        response.raise_for_status()

        data = response.json()
        rows = data['data']['rows']
        '''
            Example row structure download=true:
                "symbol": "ABL",
                "name": "Abacus Global Management Inc. Class A Common Stock",
                "lastsale": "$5.20",
                "netchange": "0.00",
                "pctchange": "0.00%",
                "volume": "587836",
                "marketCap": "503635803.00",
                "country": "United States",
                "ipoyear": "2020",
                "industry": "Investment Managers",
                "sector": "Finance",
                "url": "/market-activity/stocks/abl"
        '''
        df = pd.DataFrame(rows)
        df = df[["symbol", "lastsale", "netchange", "pctchange", "marketCap", "volume", "sector", "industry"]]
        df['lastsale'] = df['lastsale'].str.replace('$', '').astype(float)
        df['netchange'] = df['netchange'].str.replace('$', '').astype(float)
        df['pctchange'] = df['pctchange'].str.replace('%', '').astype(float) / 100.0
        df['volume'] = df['volume'].str.replace(',', '').astype(int)
        df['marketCap'] = df['marketCap'].str.replace(',', '').astype(float)

        return df
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        return pd.DataFrame()
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
        return pd.DataFrame()