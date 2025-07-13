import logging
from typing import Optional

from ibapi.client import EClient
from ibapi.wrapper import EWrapper

from .mixin import (
    ConnectionMixin,
    HistoricalDataMixin,
)

logger = logging.getLogger(__name__)


class IBKRClient(
    ConnectionMixin,
    HistoricalDataMixin,
    EWrapper,
    EClient,
):
    """
    Modular IBKR client using mixins for different functionality areas.
    
    This client separates concerns into specialized mixins:
    - ConnectionMixin: Connection management
    """
     
    def __init__(
            self, 
            host: str = "127.0.0.1", 
            port: int = 7497,
            client_id: int = 1,
            timeout: int = 10,
            max_retries: int = 3,
            retry_delay: float = 1.0,
            log_level: str = "INFO",
            timezone: str = "Asia/Bangkok",
        ) -> None:
        """
        Initialize the modular IBKR client.
        
        Args:
            host: Host address for connection
            port: Port number for connection
            client_id: Unique client identifier
            timeout: Connection timeout in seconds
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retry attempts
            log_level: Logging level
            timezone: Timezone for data formatting
        """
        # Initialize EClient and EWrapper
        EClient.__init__(self, self)
        EWrapper.__init__(self)
        
        # Initialize all mixins
        ConnectionMixin.__init__(self)
        HistoricalDataMixin.__init__(self, timezone=timezone)
        
        # Set connection configuration
        self.set_connection_config(
            host=host,
            port=port,
            client_id=client_id,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        self.log_level = log_level
        self.timezone = timezone
        
        logger.info(f"Initialized modular IBKRClient with timezone: {timezone}")
    
    # Context manager support
    def __enter__(self):
        """Context manager entry."""
        self.connect_to_tws()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        logger.info("Cleaning up IBKRClient resources")
        try:
            self.disconnect_from_tws()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
        
        logger.info("IBKRClient cleanup complete")
        return False
    
    def clear_data(self):
        """Clear all data storage (backward compatibility method)."""
        logger.debug("Cleared all data storage")
