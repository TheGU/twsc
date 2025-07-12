"""
Base mixin and Protocols class for IBKR Trading Client mixins.

This provides the foundation for all mixin classes that extend IBKRClient functionality.

These protocols define the interfaces that mixins expect to be available
from the final composed client class.
"""

import logging
from typing import Dict, Any, Optional, Callable, Protocol
from threading import Thread

from ibapi.contract import Contract as IBContract
from ibapi.order import Order as IBOrder
from ibapi.order_cancel import OrderCancel


logger = logging.getLogger(__name__)


class BaseMixin:
    """
    Base class for all IBKR client mixins.
    
    This class provides common functionality and interface patterns
    that all mixins should follow.
    """
    
    def __init__(self):
        """Initialize the base mixin."""
        self._initialized = False
        self._request_id_counter = getattr(self, '_request_id_counter', 1000)
        
    def _get_next_request_id(self) -> int:
        """
        Get next available request ID.
        
        Returns:
            int: Next request ID
        """
        self._request_id_counter += 1
        return self._request_id_counter
    
    def _register_callback(self, callback_type: str, req_id: int, callback: Callable):
        """
        Register a callback for EWrapper events.
        
        Args:
            callback_type: Type of callback (e.g., 'tick', 'historical_data')
            req_id: Request ID associated with the callback
            callback: Callback function
        """
        if not hasattr(self, '_callbacks'):
            self._callbacks = {}
        
        if callback_type not in self._callbacks:
            self._callbacks[callback_type] = {}
            
        self._callbacks[callback_type][req_id] = callback
        logger.debug(f"Registered {callback_type} callback for request {req_id}")
    
    def _unregister_callback(self, callback_type: str, req_id: int):
        """
        Unregister a callback.
        
        Args:
            callback_type: Type of callback
            req_id: Request ID to unregister
        """
        if hasattr(self, '_callbacks') and callback_type in self._callbacks:
            if req_id in self._callbacks[callback_type]:
                del self._callbacks[callback_type][req_id]
                logger.debug(f"Unregistered {callback_type} callback for request {req_id}")
    
    def _execute_callback(self, callback_type: str, req_id: int, *args, **kwargs):
        """
        Execute a registered callback.
        
        Args:
            callback_type: Type of callback
            req_id: Request ID
            *args: Positional arguments to pass to callback
            **kwargs: Keyword arguments to pass to callback
        """
        if (hasattr(self, '_callbacks') and 
            callback_type in self._callbacks and 
            req_id in self._callbacks[callback_type]):
            try:
                callback = self._callbacks[callback_type][req_id]
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error executing {callback_type} callback for request {req_id}: {e}")
    
    def initialize_mixin(self):
        """
        Initialize the mixin. Called when the client is fully set up.
        Override this method in subclasses to perform initialization.
        """
        if not self._initialized:
            logger.debug(f"Initializing {self.__class__.__name__}")
            self._initialized = True
    
    def cleanup_mixin(self):
        """
        Cleanup mixin resources. Called when the client is disconnecting.
        Override this method in subclasses to perform cleanup.
        """
        if hasattr(self, '_callbacks'):
            self._callbacks.clear()
        logger.debug(f"Cleaned up {self.__class__.__name__}")



class EClientProtocol(Protocol):
    """Protocol defining EClient methods used by mixins."""
    
    def connect(self, host: str, port: int, client_id: int) -> None:
        """Connect to TWS/Gateway."""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from TWS/Gateway."""
        ...
    
    def isConnected(self) -> bool:
        """Check if connected."""
        ...
    
    def run(self) -> None:
        """Run the client message loop."""
        ...
    
    def reqIds(self, num_ids: int) -> None:
        """Request next valid order IDs."""
        ...
    
    def placeOrder(self, order_id: int, contract: IBContract, order: IBOrder) -> None:
        """Place an order."""
        ...
    
    def cancelOrder(self, order_id: int, order_cancel: OrderCancel) -> None:
        """Cancel an order."""
        ...
    
    def reqGlobalCancel(self, order_cancel: OrderCancel) -> None:
        """Cancel all orders."""
        ...
    
    def reqHistoricalData(
        self,
        reqId: int,
        contract: IBContract,
        endDateTime: str,
        durationStr: str,
        barSizeSetting: str,
        whatToShow: str,
        useRTH: int,
        formatDate: int,
        keepUpToDate: bool,
        chartOptions: Any
    ) -> None:
        """Request historical data."""
        ...
    
    def cancelHistoricalData(self, req_id: int) -> None:
        """Cancel historical data request."""
        ...
    
    def reqMktData(
        self,
        reqId: int,
        contract: IBContract,
        genericTickList: str,
        snapshot: bool,
        regulatorySnapshot: bool,
        mktDataOptions: Any
    ) -> None:
        """Request market data."""
        ...
    
    def cancelMktData(self, req_id: int) -> None:
        """Cancel market data request."""
        ...
    
    def reqAccountSummary(self, req_id: int, group: str, tags: str) -> None:
        """Request account summary."""
        ...
    
    def cancelAccountSummary(self, req_id: int) -> None:
        """Cancel account summary request."""
        ...
    
    def reqPositions(self) -> None:
        """Request positions."""
        ...
    
    def cancelPositions(self) -> None:
        """Cancel positions request."""
        ...
    
    def reqExecutions(self, req_id: int, execution_filter: Any) -> None:
        """Request executions."""
        ...
    
    def reqContractDetails(self, req_id: int, contract: IBContract) -> None:
        """Request contract details."""
        ...
    
    def reqPnLSingle(self, req_id: int, account: str, model_code: str, con_id: int) -> None:
        """Request PnL for a single position."""
        ...
    
    def cancelPnLSingle(self, req_id: int) -> None:
        """Cancel PnL single request."""
        ...
    
    def reqAllOpenOrders(self) -> None:
        """Request all open orders."""
        ...
    
    def reqOpenOrders(self) -> None:
        """Request open orders."""
        ...


class ConnectionStateProtocol(Protocol):
    """Protocol defining connection state attributes used by mixins."""
    
    is_connected: bool
    next_valid_id: Optional[int]
    _api_thread: Optional[Thread]
