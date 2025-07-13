import logging
from pathlib import Path
from typing import Optional

import pandas as pd

from .const import DATA_COLUMNS
from .utils.cache_utils import get_cache_expected_range, is_cache_sufficient

logger = logging.getLogger(__name__)


class CacheHandler:
    """
    High-level interface for requesting and managing historical market data with smart caching.
    
    This class provides intelligent caching using Parquet files to minimize API calls
    and dramatically speed up repeated data requests.
    """

    def __init__(
            self, 
            client, 
            
            symbol: str,
            bar_size: str,
            what_to_show: str = "TRADES",
            exchange: str = "SMART",
            currency: str = "USD",
            data_type: str = "HISTORICAL", 

            cache_dir: str = ".ibtrade_cache"
        ):
        """
        Initialize the DataHandler.
        
        Args:
            client: IBKRClient instance for making API requests
            cache_dir: Directory for storing cached data (default: .ibtrade_cache)
        """
        self.client = client
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_dir()

        self.symbol: str = symbol.upper()
        # TODO: validate bar_size against API documentation
        self.bar_size: str = bar_size
        self.exchange: str = exchange.upper()
        self.what_to_show: str = what_to_show.upper()
        self.currency: str = currency.upper()
        self.data_type: str = data_type.upper()

        self.cache_path: Path = self._create_cache_path()

        self.data: pd.DataFrame = pd.DataFrame(columns=DATA_COLUMNS)  # Initialize empty DataFrame for data storage

    def __str__(self) -> str:
        base = (f"CacheHandler(symbol={self.symbol}, bar_size={self.bar_size}, " +
                f"what_to_show={self.what_to_show}, exchange={self.exchange}, " +
                f"currency={self.currency}, data_type={self.data_type}, " +
                f"cache_path={self.cache_path})")
        if self.data is not None and not self.data.empty:
            base += f", data_shape={self.data.shape}, start_date={self.data['timestamp'].min()}, end_date={self.data['timestamp'].max()}"

        return base

    def __repr__(self) -> str:
        return f"<{self.__str__()}>"

    def _create_cache_path(self) -> Path:
        """
        Get the cache file path based on the current configuration.
        Generate the cache file path based on the timeframe as subdirectory.
        The cache file is named using a hash of the timeframe to ensure uniqueness.
        
        Returns:
            Path: Path to the cache file
        """
        # Normalize timeframe to create a unique cache file name
        filename = f"{self.symbol}_{self.exchange}_{self.what_to_show}_{self.currency}_{self.data_type}"
        subdir = self.bar_size.lower().replace(" ", "_").replace("/", "_")
        self._ensure_cache_dir(subdir)
        return Path(self.cache_dir, subdir, f"{filename}.parquet")


    def _ensure_cache_dir(self, subdir: Optional[str] = None) -> None:
        """Create cache directory structure if it doesn't exist."""
        
        # if cache_dir it not exists, create it and show log message
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created cache directory: {self.cache_dir}")

        if subdir:
            subdir_path = self.cache_dir / subdir
            if not subdir_path.exists():
                subdir_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created cache subdirectory: {subdir_path}")


    def save(self, data: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Save data to smart cache using Parquet format.
        Args:
            symbol: The symbol for the data
            timeframe: Timeframe for the data
            exchange: Exchange for the data (optional)
            currency: Currency for the data (optional)
            data_type: Type of data (optional)
            data: DataFrame containing the data to save
        """
        logger.debug(f"Saving data to cache: {self.cache_path}")

        # Ensure incoming data has proper index
        if 'timestamp' in data.columns and not isinstance(data.index, pd.DatetimeIndex):
            logger.debug("Setting timestamp as index on incoming data.")
            data = data.set_index('timestamp')
        elif not isinstance(data.index, pd.DatetimeIndex):
            logger.warning("Incoming data doesn't have timestamp column or datetime index.")
            return

        # Load existing data
        existing_data = self.load()
        
        # Combine data
        if existing_data.empty:
            logger.debug("No existing cache data - saving new data directly.")
            new_data = data.copy()
        else:
            logger.debug("Appending new data to existing cache data.")
            # Both should now have datetime indices
            new_data = pd.concat([existing_data, data]).drop_duplicates()
            
            # Additional deduplication by index (timestamp) to handle duplicate timestamps
            new_data = new_data[~new_data.index.duplicated(keep='last')]

        try:
            # Sort by index (timestamp)
            new_data = new_data.sort_index()

            logger.debug(f"Saving data to cache at: {self.cache_path}")
            # Save with index=True to preserve timestamp index
            new_data.to_parquet(self.cache_path, index=True)
            
            # Update our internal data
            self.data = new_data
            
            logger.info(f"Data saved to cache: {self.cache_path} with {len(new_data)} rows")
        except Exception as e:
            logger.error(f"Failed to save data to cache: {e}")
            raise RuntimeError(f"Failed to save data to cache: {e}") from e

        return self.data

    def load(self,) -> pd.DataFrame:
        """
        Load data from smart cache using Parquet format.
        Args:
            symbol: The symbol for the data
            timeframe: Timeframe for the data
            duration: Duration for the data
            what_to_show: Type of data to retrieve (e.g., "TRADES", "MIDPOINT")
            exchange: Exchange for the data (optional)
            currency: Currency for the data (optional)
        Returns:
            Optional[pd.DataFrame]: DataFrame containing the cached data, or None if not found
        """

        if self.cache_path.exists():
            try:
                self.data = pd.read_parquet(self.cache_path)
                
                # Ensure timestamp is the index
                if 'timestamp' in self.data.columns and not isinstance(self.data.index, pd.DatetimeIndex):
                    logger.debug("Converting timestamp column to index after loading from cache.")
                    self.data.set_index('timestamp', inplace=True)
                elif not isinstance(self.data.index, pd.DatetimeIndex):
                    logger.warning("Loaded cache data doesn't have timestamp column or datetime index.")
                
                logger.info(f"Data loaded from cache: {self.cache_path}")
                return self.data
            except Exception as e:
                logger.error(f"Failed to load data from cache: {e}")
                raise RuntimeError(f"Failed to load data from cache: {e}") from e
        else:
            logger.debug(f"No cached data found for: {self.cache_path}")
            
        return pd.DataFrame(columns=DATA_COLUMNS)  # Return empty DataFrame if no cache found


    @property
    def data_info(self) -> str:
        """
        Get a string representation of the cached data information.
        Returns:
            str: Information about the cached data, including shape and date range
        """
        if self.data is None:
            self.load()  # Ensure data is loaded before accessing info

        if self.data is not None and not self.data.empty:
            start_date = self.data['timestamp'].min()
            end_date = self.data['timestamp'].max()
            return (f"Cached data for {self.symbol} from {start_date} to {end_date}, "
                    f"shape: {self.data.shape}")
        else:
            return f"No cached data available for {self.symbol}."

    def check_coverage(self, end_date_time: str, duration: str, timezone: str) -> bool:
        """
        Check if cached data provides sufficient coverage for the requested timeframe.
        
        This function uses a simple, focused approach: calculate the expected data range
        and check if our cache is sufficient for that range.
        
        Args:
            end_date_time: Requested end date time
            duration: Requested duration
            timezone: Client timezone for calculations
            
        Returns:
            bool: True if cache provides sufficient coverage
        """
        # Load cached data if not already loaded
        if self.data.empty:
            self.data = self.load()
        
        if self.data.empty:
            logger.debug("No cached data available")
            return False
        
        # Ensure data has timestamp index
        if 'timestamp' in self.data.columns and not isinstance(self.data.index, pd.DatetimeIndex):
            logger.debug("Converting timestamp column to index for coverage check.")
            self.data.set_index('timestamp', inplace=True)
        elif not isinstance(self.data.index, pd.DatetimeIndex):
            logger.error("Cached data doesn't have proper datetime index or timestamp column.")
            return False
        
        # Get cached data time range
        cached_start = self.data.index.min()
        cached_end = self.data.index.max()
        
        # Calculate expected data range for this request
        expected_start, expected_end = get_cache_expected_range(
            bar_size=self.bar_size,
            end_date_time=end_date_time,
            duration=duration,
            timezone=timezone,
            exchange=self.exchange
        )
        
        # Check if cache is sufficient
        return is_cache_sufficient(
            cached_start=cached_start,
            cached_end=cached_end,
            expected_start=expected_start,
            expected_end=expected_end,
            duration=duration,
            bar_size=self.bar_size,
            exchange=self.exchange
        )