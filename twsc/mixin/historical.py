"""
Historical Data Mixin for IBKR Trading Client.

Handles historical data operations including:
- Historical data requests and management
- Data validation and formatting
- Cache integration for historical data
"""

import logging
import time
from typing import List, Any, Dict, Set, TYPE_CHECKING, cast
from decimal import Decimal

import pandas as pd
from ibapi.common import BarData

from .base import BaseMixin
from ..cache import CacheHandler
from ..const import DATA_COLUMNS

if TYPE_CHECKING:
    from .base import EClientProtocol
    from ..contract import Contract

logger = logging.getLogger(__name__)


class HistoricalDataMixin(BaseMixin):
    """
    Mixin that handles historical data operations for the IBKR client.
    
    This mixin provides functionality for historical data requests,
    data formatting, and cache integration.
    """
    
    def __init__(self, timezone: str = "Asia/Bangkok"):
        """
        Initialize the historical data mixin.
        
        Args:
            timezone: Timezone for data formatting
        """
        super().__init__()
        self.timezone = timezone
        
        # Data storage for historical requests
        # Dictionary to hold historical data by request ID
        self.historical_data: Dict[int, List[Dict[str, Any]]] = {} 
        # Set to track finished historical data requests
        self.historical_data_finished: Set[int] = set()
    
    def get_historical_data(
            self, 
            contract: 'Contract',
            end_date_time: str = "",
            duration: str = "1 D",
            bar_size: str = "1 hour",
            what_to_show: str = "TRADES",
            use_rth: bool = True,
            format_date: bool = True,
            keep_up_to_date: bool = False,
            chart_options=None,
            use_cache: bool = True,
            timeout: int = 60
        ) -> pd.DataFrame:
        """
        Request historical data for a given contract.
        
        Args:
            contract: The contract to request data for
            end_date_time: End date and time for the request (empty string for current time)
            duration: Duration string (e.g., "1 D", "1 W")
            bar_size: Size of each bar (e.g., "1 hour", "5 mins")
            what_to_show: Type of data to retrieve (e.g., "TRADES", "MIDPOINT")
            use_rth: Whether to use Regular Trading Hours only
            format_date: Whether to format date in yyyyMMdd format
            keep_up_to_date: Whether to keep receiving updates for real-time bars
            chart_options: Additional options for charting (if any)
            use_cache: Whether to use cached data if available
            timeout: Timeout in seconds
            
        Returns:
            pd.DataFrame: Historical data as DataFrame
        """
        if chart_options is None:
            chart_options = []
            
        if not getattr(self, 'is_connected', False) or not cast('EClientProtocol', self).isConnected():
            raise ConnectionError("Not connected to TWS/Gateway. Please connect first.")
        
        cache = CacheHandler(
            client=self,
            symbol=contract.symbol,
            bar_size=bar_size,
            what_to_show=what_to_show,
            exchange=contract.exchange,
            currency=contract.currency,
        )

        if use_cache:
            cached_df = cache.load()
            if cached_df is not None and not cached_df.empty:
                # Check if cached data provides sufficient coverage for the request
                if cache.check_coverage(end_date_time, duration, self.timezone):
                    logger.info(f"Returning cached data for {contract.symbol} - cache covers requested timeframe")
                    return cached_df
                else:
                    logger.info(f"Cache data exists but doesn't cover requested timeframe for {contract.symbol} - fetching new data")
            
        req_id = self._get_next_request_id()
        logger.info(f"Requesting historical data for {contract.symbol} with request ID {req_id}")
        
        cast('EClientProtocol', self).reqHistoricalData(
            reqId=req_id,
            contract=contract.to_ib(),
            endDateTime=end_date_time,
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=int(use_rth),
            formatDate=int(format_date),
            keepUpToDate=keep_up_to_date,
            chartOptions=chart_options
        )

        # Wait for data to be collected and convert to DataFrame
        try:
            data = self.wait_for_historical_data(req_id, timeout)
            df = self.convert_to_dataframe(data)
            
            if use_cache and not df.empty:
                cache_df = cache.save(data=df)
                if cache_df is not None:
                    df = cache_df
                    
            return df
            
        except TimeoutError as e:
            # Clean up the failed request
            # Type cast to get access to EClient methods
            cast('EClientProtocol', self).cancelHistoricalData(req_id)
            if req_id in self.historical_data:
                del self.historical_data[req_id]
            self.historical_data_finished.discard(req_id)
            raise e

    def wait_for_historical_data(self, req_id: int, timeout: int = 60) -> List[Dict[str, Any]]:
        """
        Wait for historical data request to complete and return the data.
        
        Args:
            req_id: Request ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            List[Dict[str, Any]]: List of bar data dictionaries
            
        Raises:
            TimeoutError: If request times out
        """
        start_time = time.time()
        
        logger.debug(f"[{req_id}] Waiting for historical data to complete")
        
        while req_id not in self.historical_data_finished:
            if time.time() - start_time > timeout:
                logger.error(f"Timeout waiting for historical data request {req_id}")
                raise TimeoutError(f"Historical data request {req_id} timed out")
            time.sleep(0.1)

        # Return the collected data for this request
        data = self.historical_data.get(req_id, [])
        logger.debug(f"[{req_id}] Returning {len(data)} bars of historical data")
        return data

    def convert_to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert list of bar data to pandas DataFrame.
        
        Args:
            data: List of bar data dictionaries
            
        Returns:
            pd.DataFrame: DataFrame with bar data
        """
        if not data:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume', 'bar_count', 'wap'])
        
        df = pd.DataFrame(data)
        
        # Convert date to datetime if it's not already
        if 'date' in df.columns:
            try:
                # IBKR date format: "20250710 09:30:00 US/Eastern" 
                # Tell pandas the exact format and let it handle timezone conversion
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d %H:%M:%S %Z')
                
                # Convert to user's timezone
                df['date'] = df['date'].dt.tz_convert(self.timezone)
                df.set_index('date', inplace=True)
                
            except Exception as e:
                logger.warning(f"Could not convert date column to datetime: {e}")
                # Try fallback - just set the string date as index
                try:
                    df.set_index('date', inplace=True)
                except Exception:
                    pass
        
        # Ensure numeric columns are properly typed for Parquet compatibility
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'bar_count', 'wap']
        for col in numeric_columns:
            if col in df.columns:
                # Convert to float64 for consistent Parquet schema
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float64')
        
        logger.debug(f"Converted {len(df)} bars to DataFrame")
        return df

    def clear_pending_historical_requests(self) -> List[int]:
        """
        Clear all pending historical data requests and return their IDs.
        
        Returns:
            List[int]: List of request IDs that were cleared
        """
        pending_req_ids = []
        
        # Find requests that are pending (not finished)
        for req_id in list(self.historical_data.keys()):
            if req_id not in self.historical_data_finished:
                pending_req_ids.append(req_id)
        
        # Clear the data
        self.historical_data.clear()
        self.historical_data_finished.clear()
        
        logger.debug(f"Cleared {len(pending_req_ids)} pending historical data requests")
        return pending_req_ids

    def clear_historical_data_storage(self):
        """Clear all historical data storage."""
        self.historical_data.clear()
        self.historical_data_finished.clear()
        logger.debug("Cleared historical data storage")

    def cleanup_mixin(self):
        """Cleanup historical data mixin resources."""
        # Prevent multiple cleanup calls
        if getattr(self, '_historical_mixin_cleaned_up', False):
            return
        self._historical_mixin_cleaned_up = True
        
        # Cancel any pending requests
        req_ids_to_cancel = self.clear_pending_historical_requests()
        for req_id in req_ids_to_cancel:
            try:
                logger.debug(f"Cancelling historical data request {req_id}")
                cast('EClientProtocol', self).cancelHistoricalData(req_id)
            except Exception as e:
                logger.warning(f"Error canceling historical data request {req_id}: {e}")
        
        # Clear all historical data storage
        self.clear_historical_data_storage()

    # ==================== EWRAPPER CALLBACKS ====================

    def historicalData(self, reqId: int, bar: BarData) -> None:
        """
        EWrapper callback for historical data bars.
        
        Args:
            reqId: Request ID
            bar: Bar data from IB API
        """
        if reqId not in self.historical_data:
            self.historical_data[reqId] = []
        
        bar_dict = {
            'date': bar.date,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': int(bar.volume),
            'wap': float(bar.wap),
            'bar_count': int(bar.barCount)
        }
        
        self.historical_data[reqId].append(bar_dict)
        logger.debug(f"[{reqId}] Received historical bar: {bar.date}")

    def historicalDataEnd(self, reqId: int, start: str, end: str) -> None:
        """
        EWrapper callback indicating historical data request is complete.
        
        Args:
            reqId: Request ID
            start: Start date of data
            end: End date of data
        """
        self.historical_data_finished.add(reqId)
        bars_count = len(self.historical_data.get(reqId, []))
        logger.info(f"[{reqId}] Historical data complete: {bars_count} bars from {start} to {end}")
