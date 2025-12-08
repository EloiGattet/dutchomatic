"""Storage abstraction layer for Dutch-o-matic."""

from .interface import StorageInterface
from .json_storage import JSONStorage

__all__ = ['StorageInterface', 'JSONStorage']
