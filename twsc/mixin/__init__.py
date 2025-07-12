"""
Mixins package for IBKR Trading Client.

This package contains all mixin classes that provide specific functionality
to the main IBKRClient. Each mixin handles a specific domain of operations:

- ConnectionMixin: Connection management and lifecycle
"""

from .base import BaseMixin
from .connection import ConnectionMixin


__all__ = [
    'BaseMixin',
    'ConnectionMixin',
]
