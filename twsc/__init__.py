"""
twsc: which stands for "Interactive Brokers TWS API Client". A Pythonic Framework for Algorithmic Trading

This package provides a high-level, event-driven framework for building, backtesting,
and deploying algorithmic trading strategies with Interactive Brokers.
"""

__version__ = "0.1.0"
__author__ = "ibtrade Development Team"


from .client import IBKRClient
from .contract import Contract

from .utils.log import setup_logging


__all__ = [
    "IBKRClient",
    "setup_logging",
    
    "Contract"
]
