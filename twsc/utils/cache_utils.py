"""
Cache coverage utilities for IBKR historical data.

This module provides functions for determining if cached data is sufficient 
for a request using market-hours-based logic.
"""

import pandas as pd
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def get_cache_expected_range(
    bar_size: str,
    end_date_time: str,
    duration: str,
    timezone: str,
    exchange: str = "SMART",
    current_time: Optional[pd.Timestamp] = None
) -> Tuple[pd.Timestamp, pd.Timestamp]:
    """
    Calculate the expected market hours range for a cache request.
    
    Determines what market hours IBKR would return for the requested duration,
    based on market status and trading calendar.
    
    Args:
        bar_size: Bar size (e.g., "5 mins", "1 hour")
        end_date_time: End date time string or empty for current time
        duration: Duration string in IBKR format (e.g., "1 D")
        timezone: Client timezone
        exchange: Exchange name for market hours determination
        current_time: Override current time for testing (optional)
        
    Returns:
        Tuple[pd.Timestamp, pd.Timestamp]: (expected_start, expected_end)
    """
    from .market_utils import MARKET_CONFIGS, is_market_open
    
    # Get market configuration
    config = MARKET_CONFIGS.get(exchange, MARKET_CONFIGS["SMART"])
    market_tz = config["timezone"]
    
    # Determine end time
    if end_date_time == "":
        if current_time is not None:
            end_time = current_time.tz_convert(market_tz)
        else:
            end_time = pd.Timestamp.now(tz=timezone).tz_convert(market_tz)
    else:
        try:
            # Parse IBKR datetime format 
            end_time = pd.to_datetime(end_date_time, utc=True).tz_convert(market_tz)
        except Exception:
            if current_time is not None:
                end_time = current_time.tz_convert(market_tz)
            else:
                end_time = pd.Timestamp.now(tz=timezone).tz_convert(market_tz)
    
    # Calculate the expected market hours range based on current market status
    if is_market_open(end_time, exchange):
        # Market is open - expect current day's data up to current time
        trading_date = end_time.date()
        market_end = end_time
    else:
        # Market is closed - expect the most recent complete trading day
        current_date = end_time.date()
        
        # Handle weekends
        if end_time.weekday() == 5:  # Saturday
            trading_date = current_date - pd.Timedelta(days=1)  # Friday
        elif end_time.weekday() == 6:  # Sunday  
            trading_date = current_date - pd.Timedelta(days=2)  # Friday
        else:
            # Weekday - determine which trading day's data to expect
            if end_time.time() >= pd.Timestamp("16:00:00").time():
                # After market close - expect same day's complete data
                trading_date = current_date
            else:
                # Before market open - expect previous trading day's complete data
                # This handles early morning requests correctly
                trading_date = current_date - pd.Timedelta(days=1)
        
        # Market end is the close of the trading day
        market_end = pd.Timestamp(f"{trading_date} 16:00:00", tz=market_tz)
    
    # Parse duration to determine how many trading days to expect
    try:
        # Parse IBKR duration format (e.g., "1 D", "2 D", "1 W", "1 M")
        duration_parts = duration.strip().split()
        if len(duration_parts) == 2:
            duration_value = int(duration_parts[0])
            duration_unit = duration_parts[1].upper()
            
            if duration_unit == 'D':
                # For "X D", expect X trading days
                trading_days = duration_value
            elif duration_unit == 'W':
                # For "X W", expect X weeks * 5 trading days
                trading_days = duration_value * 5
            elif duration_unit == 'M':
                # For "X M", expect approximately X months * 22 trading days
                trading_days = duration_value * 22
            else:
                # Default to 1 day for unknown units
                trading_days = 1
        else:
            # Default to 1 day if parsing fails
            trading_days = 1
    except Exception:
        # Default to 1 day if any parsing error
        trading_days = 1
    
    # Calculate start time based on number of trading days
    if trading_days == 1:
        # For 1 day, use the logic we already have
        market_start = pd.Timestamp(f"{trading_date} 09:30:00", tz=market_tz)
    else:
        # For multiple days, go back the appropriate number of trading days
        start_date = trading_date
        days_back = trading_days - 1  # -1 because we already have the end trading day
        
        while days_back > 0:
            start_date = start_date - pd.Timedelta(days=1)
            # Skip weekends
            if start_date.weekday() < 5:  # Monday=0, Friday=4
                days_back -= 1
        
        market_start = pd.Timestamp(f"{start_date} 09:30:00", tz=market_tz)
    
    logger.debug(f"Expected market hours range: {market_start} to {market_end}")
    return market_start, market_end


def is_cache_sufficient(
    cached_start: pd.Timestamp,
    cached_end: pd.Timestamp,
    expected_start: pd.Timestamp,
    expected_end: pd.Timestamp,
    duration: str,
    bar_size: str,
    exchange: str = "SMART"
) -> bool:
    """
    Check if cached data is sufficient for the expected data range.
    
    Compares cached data coverage against expected market hours range
    to determine if a new API request is needed.
    
    Args:
        cached_start: Start timestamp of cached data
        cached_end: End timestamp of cached data
        expected_start: Expected start timestamp (from get_cache_expected_range)
        expected_end: Expected end timestamp (from get_cache_expected_range)
        duration: Requested duration (currently unused)
        bar_size: Bar size (currently unused)
        exchange: Exchange name (currently unused)
        
    Returns:
        bool: True if cache covers the expected market hours
    """
    # Simple coverage check: Does cache cover the expected market hours?
    
    # Allow small tolerance for market open variations (e.g., 9:30 vs 9:35)
    start_tolerance = pd.Timedelta(minutes=15)
    start_covered = cached_start <= (expected_start + start_tolerance)
    
    # Allow small tolerance for market close variations (e.g., early close, missing last few bars)
    end_tolerance = pd.Timedelta(minutes=10)
    end_covered = cached_end >= (expected_end - end_tolerance)
    
    logger.debug(f"Cache: {cached_start} to {cached_end}")
    logger.debug(f"Expected: {expected_start} to {expected_end}")
    logger.debug(f"Start covered: {start_covered} (tolerance: 15min)")
    logger.debug(f"End covered: {end_covered} (tolerance: 10min)")
    
    result = start_covered and end_covered
    
    if result:
        logger.debug("Cache covers expected market hours - using cached data")
    else:
        logger.debug("Cache insufficient for expected market hours - fetching new data")
    
    return result
