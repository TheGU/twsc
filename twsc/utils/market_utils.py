"""
Market and time utilities for trading operations.

This module provides utilities for:
- Parsing IBKR duration strings
- Time range calculations for data requests
- Market hours checking (with multi-exchange support planned)
- Bar alignment and freshness thresholds

The functiondef get_market_timezone(exchange: str = "SMART") -> str:to be intuitive and broadly useful, not just for caching.
"""

import re
from datetime import datetime, timedelta
import pandas as pd
from typing import Tuple, Optional
import logging

# Optional exchange_calendars integration
try:
    import exchange_calendars as xcals
    from exchange_calendars import get_calendar
    HAS_EXCHANGE_CALENDARS = True
except ImportError:
    HAS_EXCHANGE_CALENDARS = False

logger = logging.getLogger(__name__)


# ============================================================================
# Duration and Time Parsing
# ============================================================================

def parse_ibkr_duration(duration: str) -> timedelta:
    """
    Parse IBKR duration string into Python timedelta.
    
    Valid IBKR duration formats:
    - S = seconds, D = days, W = weeks, M = months, Y = years
    - Examples: "1 D", "2 W", "1 M", "1 Y", "3600 S"
    
    Args:
        duration: IBKR duration string
        
    Returns:
        timedelta: Parsed duration
        
    Raises:
        ValueError: If duration format is invalid
    """
    duration = duration.strip().upper()
    
    # Parse the duration string using regex
    match = re.match(r'^(\d+)\s*([SDWMY])$', duration)
    if not match:
        raise ValueError(f"Invalid duration format: {duration}")
    
    amount, unit = match.groups()
    amount = int(amount)
    
    if unit == 'S':
        return timedelta(seconds=amount)
    elif unit == 'D':
        return timedelta(days=amount)
    elif unit == 'W':
        return timedelta(weeks=amount)
    elif unit == 'M':
        # Approximate months as 30 days
        return timedelta(days=amount * 30)
    elif unit == 'Y':
        # Approximate years as 365 days
        return timedelta(days=amount * 365)
    else:
        raise ValueError(f"Unsupported duration unit: {unit}")


def parse_end_time(end_date_time: str, timezone: str) -> pd.Timestamp:
    """
    Parse end_date_time string into a timezone-aware timestamp.
    
    This is a general utility for parsing IBKR-style end times.
    
    Args:
        end_date_time: End date time string or empty for current time
        timezone: Target timezone for the result
        
    Returns:
        pd.Timestamp: Parsed timestamp in specified timezone
    """
    if end_date_time == "":
        return pd.Timestamp.now(tz=timezone)
    else:
        try:
            return pd.to_datetime(end_date_time, format='%Y%m%d %H:%M:%S %Z', utc=True).tz_convert(timezone)
        except ValueError:
            # Fallback for different timezone formats
            return pd.to_datetime(end_date_time, utc=True).tz_convert(timezone)


# ============================================================================
# Time Range Calculations
# ============================================================================

def get_time_range_for_request(
    end_date_time: str,
    duration: str,
    timezone: str,
    align_to_bars: bool = False,
    bar_size: str = "5 mins",
    exchange: str = "SMART"
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Calculate the time range for a data request.
    
    This is a general utility that can be used for any time range calculation,
    not just caching. The name is intuitive and the function is flexible.
    
    Args:
        end_date_time: End date time string or empty for current time
        duration: Duration string in IBKR format (e.g., "1 D", "7200 S")
        timezone: Client timezone
        align_to_bars: Whether to align end time to bar boundaries
        bar_size: Bar size for alignment (e.g., "5 mins", "1 hour")
        exchange: Exchange name for market hours determination
        
    Returns:
        Tuple[pd.Timestamp, pd.Timestamp]: (start_time, end_time)
    """
    # Determine the end time
    end_time = parse_end_time(end_date_time, timezone)
    
    # Optionally align to bar boundary (useful for real-time requests during market hours)
    if align_to_bars and end_date_time == "" and is_market_open(end_time, exchange):
        end_time = align_to_bar_boundary(end_time, bar_size)
    
    # Calculate start time
    duration_delta = parse_ibkr_duration(duration)
    start_time = end_time - duration_delta
    
    logger.debug(f"Time range: {start_time} to {end_time}")
    return start_time, end_time


def align_to_bar_boundary(timestamp: pd.Timestamp, bar_size: str) -> pd.Timestamp:
    """
    Align timestamp to the most recent bar boundary.
    
    This is a general utility for bar alignment, useful for many purposes.
    
    Args:
        timestamp: Timestamp to align
        bar_size: Bar size (e.g., "5 mins", "1 hour", "1 day")
        
    Returns:
        pd.Timestamp: Aligned timestamp
    """
    freq = _parse_bar_size_to_freq(bar_size)
    return timestamp.floor(freq)


# ============================================================================
# Market Hours and Exchange Support
# ============================================================================

# Market configurations for different exchanges
# Maps IBKR exchange names to exchange_calendars codes and basic config
MARKET_CONFIGS = {
    # US Markets
    "SMART": {
        "timezone": "US/Eastern", 
        "open": "09:30", 
        "close": "16:00",
        "calendar_code": "XNYS"  # NYSE for SMART routing
    },
    "NASDAQ": {
        "timezone": "US/Eastern", 
        "open": "09:30", 
        "close": "16:00",
        "calendar_code": "XNAS"
    },
    "NYSE": {
        "timezone": "US/Eastern", 
        "open": "09:30", 
        "close": "16:00",
        "calendar_code": "XNYS"
    },
    
    # International Markets
    "HKEX": {
        "timezone": "Asia/Hong_Kong", 
        "open": "09:30", 
        "close": "16:00",
        "calendar_code": "XHKG"
    },
    "LSE": {
        "timezone": "Europe/London", 
        "open": "08:00", 
        "close": "16:30",
        "calendar_code": "XLON"
    },
    "TSE": {
        "timezone": "Asia/Tokyo", 
        "open": "09:00", 
        "close": "15:00",
        "calendar_code": "XTKS"
    },
    "SSE": {
        "timezone": "Asia/Shanghai", 
        "open": "09:30", 
        "close": "15:00",
        "calendar_code": "XSHG"
    },
    "SGX": {
        "timezone": "Asia/Singapore", 
        "open": "09:00", 
        "close": "17:00",
        "calendar_code": "XSES"
    },
}


def is_market_open(timestamp: pd.Timestamp, exchange: str = "SMART") -> bool:
    """
    Check if a timestamp is within market hours for a given exchange.
    
    This function now uses exchange_calendars for accurate market hours
    including holidays and special sessions when available.
    
    Args:
        timestamp: Timestamp to check
        exchange: Exchange to check market hours for
        
    Returns:
        bool: True if timestamp is within market hours
        
    Note:
        When exchange_calendars is available, this provides accurate
        market hours including holidays. Otherwise falls back to
        basic timezone and hour checking.
    """
    # Get market configuration
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    
    # Try to use exchange_calendars for accurate market hours
    if HAS_EXCHANGE_CALENDARS and "calendar_code" in config:
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            
            # Check if the timestamp is during a trading session
            # exchange_calendars expects timezone-aware timestamps
            if timestamp.tz is None:
                # If timestamp is naive, assume it's in the market's timezone
                timestamp = timestamp.tz_localize(config["timezone"])
            
            return calendar.is_open_at_time(timestamp)
            
        except Exception as e:
            logger.debug(f"exchange_calendars failed for {exchange}: {e}, falling back to basic check")
    
    # Fallback to basic market hours checking
    return _is_market_open_basic(timestamp, config)


def _is_market_open_basic(timestamp: pd.Timestamp, config: dict) -> bool:
    """
    Basic market hours checking without holiday support.
    
    Args:
        timestamp: Timestamp to check
        config: Market configuration dictionary
        
    Returns:
        bool: True if timestamp is within basic market hours
    """
    market_tz = config["timezone"]
    
    # Convert timestamp to market timezone
    market_time = timestamp.tz_convert(market_tz)
    
    # Skip weekends
    if market_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check market hours
    time_of_day = market_time.time()
    market_open = datetime.strptime(config["open"], "%H:%M").time()
    market_close = datetime.strptime(config["close"], "%H:%M").time()
    
    return market_open <= time_of_day <= market_close


def get_market_timezone(exchange: str = "SMART") -> str:
    """
    Get the timezone for a given exchange.
    
    Args:
        exchange: Exchange code
        
    Returns:
        str: Timezone string
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    return config["timezone"]


def is_trading_day(date: pd.Timestamp, exchange: str = "SMART") -> bool:
    """
    Check if a date is a trading day for a given exchange.
    
    This function considers weekends and holidays when exchange_calendars
    is available, otherwise just checks weekends.
    
    Args:
        date: Date to check (timezone-naive)
        exchange: Exchange to check
        
    Returns:
        bool: True if it's a trading day
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    
    # Ensure date is timezone-naive for exchange_calendars
    if date.tz is not None:
        date = date.tz_localize(None)
    
    # Try to use exchange_calendars for accurate trading day check
    if HAS_EXCHANGE_CALENDARS and "calendar_code" in config:
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            return calendar.is_session(date)
        except Exception as e:
            logger.debug(f"exchange_calendars failed for {exchange}: {e}, falling back to basic check")
    
    # Fallback to basic weekend check
    return date.weekday() < 5


def get_next_trading_day(date: pd.Timestamp, exchange: str = "SMART") -> pd.Timestamp:
    """
    Get the next trading day for a given exchange.
    
    Args:
        date: Starting date (timezone-naive)
        exchange: Exchange to check
        
    Returns:
        pd.Timestamp: Next trading day
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    
    # Ensure date is timezone-naive for exchange_calendars
    if date.tz is not None:
        date = date.tz_localize(None)
    
    # Try to use exchange_calendars for accurate next trading day
    if HAS_EXCHANGE_CALENDARS and "calendar_code" in config:
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            return calendar.next_session(date)
        except Exception as e:
            logger.debug(f"exchange_calendars failed for {exchange}: {e}, falling back to basic check")
    
    # Fallback to basic next weekday logic
    next_day = date + pd.Timedelta(days=1)
    while next_day.weekday() >= 5:  # Skip weekends
        next_day += pd.Timedelta(days=1)
    return next_day


def get_market_hours(date: pd.Timestamp, exchange: str = "SMART") -> Optional[Tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Get market open and close times for a specific date and exchange.
    
    Args:
        date: Date to get market hours for (timezone-naive)
        exchange: Exchange to check
        
    Returns:
        Optional[Tuple[pd.Timestamp, pd.Timestamp]]: (open_time, close_time) in UTC,
        or None if market is closed that day
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    
    # Ensure date is timezone-naive
    if date.tz is not None:
        date = date.tz_localize(None)
    
    # Check if it's a trading day first
    if not is_trading_day(date, exchange):
        return None
    
    # Try to use exchange_calendars for accurate market hours
    if HAS_EXCHANGE_CALENDARS and "calendar_code" in config:
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            
            if calendar.is_session(date):
                open_time = calendar.session_open(date)
                close_time = calendar.session_close(date)
                return (open_time, close_time)
        except Exception as e:
            logger.debug(f"exchange_calendars failed for {exchange}: {e}, falling back to basic check")
    
    # Fallback to basic market hours
    market_tz = config["timezone"]
    open_time = pd.Timestamp(f"{date.strftime('%Y-%m-%d')} {config['open']}")
    close_time = pd.Timestamp(f"{date.strftime('%Y-%m-%d')} {config['close']}")
    
    # Localize to market timezone then convert to UTC
    open_time = open_time.tz_localize(market_tz).tz_convert('UTC')
    close_time = close_time.tz_localize(market_tz).tz_convert('UTC')
    
    return (open_time, close_time)


def is_market_holiday(date: pd.Timestamp, exchange: str = "SMART") -> bool:
    """
    Check if a date is a market holiday for a given exchange.
    
    Args:
        date: Date to check (timezone-naive)
        exchange: Exchange to check
        
    Returns:
        bool: True if it's a holiday, False otherwise or if unable to determine
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    
    # Ensure date is timezone-naive
    if date.tz is not None:
        date = date.tz_localize(None)
    
    # Only works with exchange_calendars
    if HAS_EXCHANGE_CALENDARS and "calendar_code" in config:
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            
            # A day is a holiday if it's a weekday but not a trading session
            if date.weekday() < 5:  # Monday-Friday
                return not calendar.is_session(date)
            
        except Exception as e:
            logger.debug(f"exchange_calendars failed for {exchange}: {e}")
    
    # Can't determine holidays without exchange_calendars
    return False


# ============================================================================
# Enhanced Market Utilities
# ============================================================================

def get_supported_exchanges() -> list:
    """
    Get list of supported exchanges.
    
    Returns:
        list: List of supported exchange codes
    """
    return list(MARKET_CONFIGS.keys())


def has_advanced_calendar_support(exchange: str = "SMART") -> bool:
    """
    Check if advanced calendar support (holidays, etc.) is available for an exchange.
    
    Args:
        exchange: Exchange to check
        
    Returns:
        bool: True if advanced calendar support is available
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    return HAS_EXCHANGE_CALENDARS and "calendar_code" in config


def get_calendar_info(exchange: str = "SMART") -> dict:
    """
    Get calendar information for an exchange.
    
    Args:
        exchange: Exchange to get info for
        
    Returns:
        dict: Calendar information
    """
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    info = {
        "exchange": exchange,
        "timezone": config["timezone"],
        "basic_open": config["open"],
        "basic_close": config["close"],
        "has_advanced_calendar": has_advanced_calendar_support(exchange),
        "calendar_code": config.get("calendar_code", "N/A")
    }
    
    if has_advanced_calendar_support(exchange):
        try:
            from exchange_calendars import get_calendar
            calendar = get_calendar(config["calendar_code"])
            info["calendar_name"] = calendar.name
            info["calendar_tz"] = str(calendar.tz)
        except Exception as e:
            logger.debug(f"Could not get calendar info for {exchange}: {e}")
    
    return info


# ============================================================================
# Data Freshness and Bar Utilities
# ============================================================================

def get_freshness_threshold(bar_size: str) -> timedelta:
    """
    Get the time threshold for considering data fresh enough based on bar size.
    
    This is a general utility that can be used for caching, real-time data
    validation, or any scenario where data freshness matters.
    
    Args:
        bar_size: The bar size (e.g., "5 mins", "1 hour", "1 day")
        
    Returns:
        timedelta: Time threshold for data freshness
        
    Note:
        Different bar sizes require different freshness tolerances:
        - 1 min bars: should be within 2-3 minutes
        - 5 min bars: should be within 5-10 minutes  
        - 1 hour bars: can be 15-30 minutes old
        - 1 day bars: can be hours old
    """
    bar_size_lower = bar_size.lower().strip()
    
    # Parse bar size more carefully to avoid "15 min" matching "5 min"
    if "1 min" in bar_size_lower and "15 min" not in bar_size_lower:
        return timedelta(minutes=3)
    elif "5 min" in bar_size_lower and "15 min" not in bar_size_lower:
        return timedelta(minutes=6)
    elif "15 min" in bar_size_lower:
        return timedelta(minutes=16)
    elif "30 min" in bar_size_lower:
        return timedelta(minutes=31)
    elif "min" in bar_size_lower:
        return timedelta(minutes=10)  # Default for other minute bars
    elif "hour" in bar_size_lower:
        return timedelta(minutes=15)
    elif "day" in bar_size_lower:
        return timedelta(hours=2)
    else:
        return timedelta(minutes=15)  # Default


def is_data_fresh_enough(
    data_timestamp: pd.Timestamp, 
    current_time: pd.Timestamp,
    bar_size: str,
    exchange: str = "SMART"
) -> bool:
    """
    Check if data is fresh enough for the given bar size and market conditions.
    
    This is a general utility for data freshness validation.
    
    Args:
        data_timestamp: Timestamp of the data
        current_time: Current timestamp
        bar_size: Bar size for freshness requirements
        exchange: Exchange for market hours context
        
    Returns:
        bool: True if data is fresh enough
    """
    time_since_data = current_time - data_timestamp
    market_open = is_market_open(current_time, exchange)
    
    if market_open:
        # Market is open - need fresh data
        threshold = get_freshness_threshold(bar_size)
        return time_since_data <= threshold
    else:
        # Market is closed - more lenient (up to 12 hours)
        return time_since_data <= timedelta(hours=12)


def get_data_sufficiency_threshold(duration: str) -> pd.Timedelta:
    """
    Get minimum data span required for a given request duration.
    
    This helps determine if available data is sufficient for analysis.
    
    Args:
        duration: Requested duration (e.g., "1 D", "7200 S", "2 W")
        
    Returns:
        pd.Timedelta: Minimum required data span
    """
    try:
        duration_delta = parse_ibkr_duration(duration)
        
        if duration_delta <= pd.Timedelta(hours=2):
            # For requests <= 2 hours, need at least 50%
            return pd.Timedelta(seconds=duration_delta.total_seconds() * 0.5)
        elif duration_delta <= pd.Timedelta(hours=8):
            # For requests <= 8 hours, need at least 40%
            return pd.Timedelta(seconds=duration_delta.total_seconds() * 0.4)
        elif duration_delta <= pd.Timedelta(days=1):
            # For daily requests, need at least 4 hours of trading data
            return pd.Timedelta(hours=4)
        elif duration_delta <= pd.Timedelta(days=7):
            # For weekly requests, need at least 1 day
            return pd.Timedelta(days=1)
        else:
            # For longer requests, need at least 2 days
            return pd.Timedelta(days=2)
            
    except ValueError:
        # Default to 1 hour if duration parsing fails
        return pd.Timedelta(hours=1)


# ============================================================================
# Private Helper Functions
# ============================================================================

def _parse_bar_size_to_freq(bar_size: str) -> str:
    """
    Convert bar size string to pandas frequency string.
    
    Args:
        bar_size: Bar size (e.g., "5 mins", "1 hour")
        
    Returns:
        str: Pandas frequency string
    """
    bar_size_lower = bar_size.lower().strip()
    
    # Parse more carefully to avoid conflicts
    if "1 min" in bar_size_lower and "15 min" not in bar_size_lower:
        return "1min"
    elif "5 min" in bar_size_lower and "15 min" not in bar_size_lower:
        return "5min"
    elif "15 min" in bar_size_lower:
        return "15min"
    elif "30 min" in bar_size_lower:
        return "30min"
    elif "hour" in bar_size_lower:
        return "1h"  # Use lowercase 'h' to avoid deprecation warning
    elif "day" in bar_size_lower:
        return "1D"
    else:
        return "5min"  # Default
