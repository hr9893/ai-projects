from langchain.tools import tool
from langchain_groq import ChatGroq
import yfinance as yt
from pandas.core.window.doc import template_returns


@tool
def get_stock_fundamentals(ticker : str)-> dict:
    """Get current stock pice, P/E ratio, market cap, and revenue growth for a ticker."""
    stock = yt.Ticker(ticker)
    info = stock.info()

    return {"price":info.get("currentPrice"),
            "pe_ratio":info.get("trailingPE"),
            "market_cap":info.get("revenueGrowth"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            }


def llm():
    llms = ChatGroq(model="openai/gpt-oss-20b",
                    api_key="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",
                    temperature=0,
                    max_tokens=None,
                    reasoning_format="parsed",
                    timeout=None,
                    max_retries=3)
    return llms