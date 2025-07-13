from typing import Literal

SEC_TYPES = Literal[
    "STK",      # Stock
    "OPT",      # Option
    "FUT",      # Future
    "FOREX",    # Forex
    "CFD",      # Contract for Difference
    "BOND",     # Bond
    "IND",      # Index
    "FUND",     # Mutual Fund
    "BAG",      # Combination (e.g., spread)
    "WAR",      # Warrant
    "CRYPTO",  # Cryptocurrency
    "UNKNOWN"   # Unknown security type
]


# Historical Bar whatToShowCopy Location
# The historical bar types listed below can be used as the whatToShow value for historical bars. 
# These values are used to request different data such as Trades, Midpoint, Bid_Ask data and more. 
# Some bar types support more products than others. 
# Please note the Supported Products section for each bar type below.
HISTORICAL_BAR_TYPES = Literal[
    "TRADES",
    "MIDPOINT",
    "BID_ASK",
    "BID",
    "ASK",
    "OPTION_IMPLIED_VOLATILITY",
    "OPTION_VOLUME",
    "OPTION_OPEN_INTEREST",
]

DATA_COLUMNS = [
    'timestamp', 'open', 'high', 'low', 'close', 'volume', 'wap', 'bar_count'
]

# ============================================================================
# Trading Constants
# ============================================================================

# Order Types
ORDER_TYPES = Literal[
    "MKT",      # Market Order
    "LMT",      # Limit Order
    "STP",      # Stop Order
    "STP LMT",  # Stop Limit Order
    "TRAIL",    # Trailing Stop
    "TRAIL LIMIT", # Trailing Stop Limit
    "REL",      # Relative Order
    "VWAP",     # Volume Weighted Average Price
    "TWAP",     # Time Weighted Average Price
    "MIDPRICE", # Midprice Order
]

# Order Actions
ORDER_ACTIONS = Literal["BUY", "SELL"]

# Time in Force
TIME_IN_FORCE = Literal[
    "DAY",      # Day Order
    "GTC",      # Good Till Cancelled
    "IOC",      # Immediate or Cancel
    "GTD",      # Good Till Date
    "FOK",      # Fill or Kill
    "DTC",      # Day Till Cancelled
]

# Position Side
POSITION_SIDE = Literal["LONG", "SHORT", "FLAT"]

# Execution Side
EXECUTION_SIDE = Literal["BOT", "SLD"]  # Bought, Sold

# Order Status
ORDER_STATUS = Literal[
    "PendingSubmit",
    "PendingCancel", 
    "PreSubmitted",
    "Submitted",
    "Cancelled",
    "Filled",
    "Inactive",
    "PartiallyFilled",
    "ApiCancelled",
    "Unknown"
]

# Tick Types for Live Data
TICK_TYPES = {
    0: "BID_SIZE",
    1: "BID_PRICE", 
    2: "ASK_PRICE",
    3: "ASK_SIZE",
    4: "LAST_PRICE",
    5: "LAST_SIZE",
    6: "HIGH",
    7: "LOW", 
    8: "VOLUME",
    9: "CLOSE_PRICE",
    14: "OPEN_PRICE",
    # Add more tick types as needed
}