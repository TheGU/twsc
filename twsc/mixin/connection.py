"""
Connection Mixin for IBKR Trading Client.

Handles all connection-related operations including:
- Connection establishment and management
- Connection lifecycle and state tracking
- Reconnection logic
- Connection configuration
"""

import logging
import threading
import time
from typing import Optional, cast, TYPE_CHECKING

from .base import BaseMixin

if TYPE_CHECKING:
    from .base import EClientProtocol

logger = logging.getLogger(__name__)


class ConnectionMixin(BaseMixin):
    """
    Mixin that handles connection management for the IBKR client.
    
    This mixin provides all connection-related functionality including
    connecting to TWS/Gateway, managing connection state, and handling
    disconnection cleanup.
    """
    
    def __init__(self):
        """Initialize the connection mixin."""
        super().__init__()
        
        # Connection configuration
        self.config = {
            'host': "127.0.0.1",
            'port': 7497,
            'client_id': 1,
            'timeout': 10,
            'max_retries': 3,
            'retry_delay': 1.0
        }
        
        # Connection state
        self.is_connected = False
        self._api_thread: Optional[threading.Thread] = None
        self.next_valid_id: Optional[int] = None
    
    def set_connection_config(self, host: Optional[str] = None, port: Optional[int] = None, 
                             client_id: Optional[int] = None, timeout: Optional[int] = None,
                             max_retries: Optional[int] = None, retry_delay: Optional[float] = None):
        """
        Update connection configuration.
        
        Args:
            host: Host address
            port: Port number
            client_id: Client identifier
            timeout: Connection timeout in seconds
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retry attempts
        """
        if host is not None:
            self.config['host'] = host
        if port is not None:
            self.config['port'] = port
        if client_id is not None:
            self.config['client_id'] = client_id
        if timeout is not None:
            self.config['timeout'] = timeout
        if max_retries is not None:
            self.config['max_retries'] = max_retries
        if retry_delay is not None:
            self.config['retry_delay'] = retry_delay
            
        logger.debug(f"Updated connection config: {self.config}")
    
    def connect_to_tws(self, host: Optional[str] = None, port: Optional[int] = None, 
                      client_id: Optional[int] = None, timeout: Optional[int] = None) -> bool:
        """
        Connect to TWS or Gateway. Automatically runs the client message loop.
        
        This method handles connection retries and timeouts. It will attempt to
        connect using the provided parameters or fall back to the configured defaults.
        
        Args:
            host: Host address (default: from config)
            port: Port number (default: from config)
            client_id: Unique client identifier (default: from config)
            timeout: Connection timeout in seconds (default: from config)
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        # Use config defaults if not specified
        host = host or self.config["host"]
        port = port or self.config["port"]
        client_id = client_id or self.config["client_id"]
        timeout = timeout or self.config["timeout"] 
        
        logger.debug(f"Attempting connection to {host}:{port} with client ID {client_id}")
        connection_start = time.time()
        
        try:
            # This requires the client to have EClient methods
            client = cast('EClientProtocol', self)
            client.connect(host, port, client_id)
            
            self._api_thread = threading.Thread(target=client.run, daemon=True)
            self._api_thread.start()
            logger.info(f"Started API thread for client ID {client_id}")
            
            while time.time() - connection_start < timeout:
                if client.isConnected():
                    self.is_connected = True
                    elapsed = time.time() - connection_start
                    logger.info(f"✅ Client {client_id}: successfully connected to TWS/Gateway in {elapsed:.2f}s")
                    
                    # Initialize all mixins after successful connection
                    self._initialize_all_mixins()
                    return True
                time.sleep(0.5)
            
            client.disconnect()
            self.is_connected = False
            raise TimeoutError("Connection to TWS/Gateway timed out")
        
        except Exception as conn_ex:
            # Connection attempt itself failed
            elapsed = time.time() - connection_start
            logger.error(f"Connection attempt failed after {elapsed:.2f}s: {conn_ex}")
            return False

    def disconnect_from_tws(self) -> None:
        """
        Disconnect from TWS/Gateway and clean up resources properly.
        """
        try:
            logger.info("Disconnecting from TWS/Gateway")
            
            # Cleanup all mixins before disconnecting
            self._cleanup_all_mixins()
            
            # Small delay to let cancellations process
            time.sleep(1)
            
            # Disconnect from IB API
            cast('EClientProtocol', self).disconnect()
            self.is_connected = False
            
            # Wait for thread to finish with timeout
            if self._api_thread and self._api_thread.is_alive():
                self._api_thread.join(timeout=3)
                if self._api_thread.is_alive():
                    logger.warning("API thread did not terminate within timeout")
                else:
                    logger.info("API thread terminated cleanly")
                    
            logger.info("⛓️‍💥 Disconnected successfully")
            
        except Exception as e:
            logger.error(f"Error during disconnection: {e}")
            # Force cleanup even if error occurred
            self.is_connected = False
    
    def get_connection_status(self) -> dict:
        """
        Get current connection status information.
        
        Returns:
            dict: Connection status details
        """
        return {
            "is_connected": self.is_connected,
            "eclient_connected": cast('EClientProtocol', self).isConnected(),
            "next_valid_id": self.next_valid_id,
            "api_thread_alive": self._api_thread.is_alive() if self._api_thread else False,
            "config": self.config.copy()
        }
    
    def _initialize_all_mixins(self):
        """Initialize all mixins after successful connection."""
        # Initialize each mixin's initialize_mixin method on this instance
        for mixin_class in self.__class__.__mro__:
            if hasattr(mixin_class, 'initialize_mixin') and mixin_class is not object:
                try:
                    # Only call if the class defines its own initialize_mixin (not inherited)
                    if 'initialize_mixin' in mixin_class.__dict__:
                        mixin_class.initialize_mixin(self)
                except Exception as e:
                    logger.error(f"Error initializing mixin {mixin_class.__name__}: {e}")
    
    def _cleanup_all_mixins(self):
        """Cleanup all mixins before disconnection.""" 
        # Track which mixins have been cleaned up to avoid duplicates
        cleaned_mixins = set()
        
        # Cleanup each mixin's cleanup_mixin method on this instance
        for mixin_class in self.__class__.__mro__:
            if hasattr(mixin_class, 'cleanup_mixin') and mixin_class is not object:
                try:
                    # Only call if the class defines its own cleanup_mixin (not inherited)
                    # and hasn't been cleaned up yet
                    if ('cleanup_mixin' in mixin_class.__dict__ and 
                        mixin_class.__name__ not in cleaned_mixins):
                        
                        logger.debug(f"Cleaning up mixin: {mixin_class.__name__}")
                        mixin_class.cleanup_mixin(self)
                        cleaned_mixins.add(mixin_class.__name__)
                        
                except Exception as e:
                    logger.error(f"Error cleaning up mixin {mixin_class.__name__}: {e}")
    

    # ===============================================================
    # EWrapper Callbacks for Connection Management
    # ===============================================================
    def nextValidId(self, orderId: int) -> None:
        """
        EWrapper callback that provides the next valid order ID.
        This is typically called after successful connection.
        
        Args:
            orderId: The next valid order ID
        """
        self.next_valid_id = orderId
        logger.info(f"Next Valid Order ID: {orderId}")

    def error(self, reqId: int, errorTime: int, errorCode: int, errorString: str, advancedOrderRejectJson: str = "") -> None:
        """
        Handle error messages from TWS/Gateway.
        
        Args:
            reqId: The request ID that caused the error (-1 for system errors)
            errorTime: Timestamp of the error (Unix timestamp)
            errorCode: The error code
            errorString: Human readable error message
            advancedOrderRejectJson: Advanced order rejection details (if applicable)
        """
        if errorCode in [2104, 2106, 2158] and reqId == -1:  # Informational messages
            logger.info(f"Info {errorCode}: {errorString}")
        elif errorCode < 2000:  # Warning messages
            logger.warning(f"Warning {errorCode}: {errorString} (ReqId: {reqId})")
        else:  # Error messages
            logger.error(f"Error {errorCode}: {errorString} (ReqId: {reqId})")
