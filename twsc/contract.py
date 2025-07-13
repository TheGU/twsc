from datetime import datetime
from dataclasses import dataclass
from typing import Any

from ibapi.contract import Contract as IBContract

# from .const import SEC_TYPES

@dataclass
class Contract:
    """
    Represents a financial contract/instrument.
    
    This is a simplified wrapper around the IBKR Contract object
    that provides a more Pythonic interface.
    """
    symbol: str
    sec_type: str = "STK"
    exchange: str = "SMART"
    currency: str = "USD"
    primary_exchange: str = ""
    local_symbol: str = ""
    con_id: int = 0
    
    def to_ib(self) -> Any:
        """Convert to IBKR Contract object."""
        
        contract = IBContract()
        contract.symbol = self.symbol
        contract.secType = self.sec_type
        contract.exchange = self.exchange
        contract.currency = self.currency
        contract.primaryExchange = self.primary_exchange
        contract.localSymbol = self.local_symbol
        contract.conId = self.con_id
        
        return contract
    
    @classmethod
    def from_ib(cls, ib_contract: Any) -> 'Contract':
        """Create from IBKR Contract object."""
        if not isinstance(ib_contract, IBContract):
            raise ValueError("Expected an instance of IBContract")
        
        return cls(
            symbol=ib_contract.symbol,
            sec_type=ib_contract.secType,
            exchange=ib_contract.exchange,
            currency=ib_contract.currency,
            primary_exchange=ib_contract.primaryExchange,
            local_symbol=ib_contract.localSymbol,
            con_id=ib_contract.conId
        )
    
    @classmethod
    def stock(cls, symbol: str, exchange: str = "SMART", currency: str = "USD"):
        """Create a stock contract."""
        return cls(
            symbol=symbol,
            sec_type="STK",
            exchange=exchange,
            currency=currency
        )

