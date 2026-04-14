"""
CSV-MP Python Implementation
Version: 0.2.0-alpha
License: CC0 1.0 (Public Domain)
"""

from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
import re


class BaseType(IntEnum):
    """BaseTypes - Define o que o dado é"""
    Any = 0
    String = 1
    Number = 2
    Long = 3
    Int = 4
    Boolean = 5
    Date = 6
    DateTime = 7
    Object = 8
    Reference = 9


class CollectionType(IntEnum):
    """CollectionTypes - Define como o dado é organizado"""
    Single = 0
    Array = 1
    Tuple = 2
    File = 3
    Text = 4


class PartFormat:
    """Part formats supported by CSV-MP"""
    TEXT_CSV = 'text/csv'
    IMAGE_PNG = 'image/png'
    IMAGE_JPEG = 'image/jpeg'
    APPLICATION_JSON = 'application/json'
    TEXT_PLAIN = 'text/plain'
    APPLICATION_PDF = 'application/pdf'


@dataclass
class ManifestEntry:
    """Manifest entry representing a part in the CSV-MP file"""
    index: int
    type: str
    count: int
    contentType: str
    version: str
    description: Optional[str] = None
    author: Optional[str] = None
    hash: Optional[str] = None


@dataclass
class ColumnDef:
    """Column definition in a table header"""
    name: str
    base_type: BaseType
    collection_type: CollectionType
    tuple_types: Optional[List[BaseType]] = None


@dataclass
class Table:
    """Parsed table from CSV-MP"""
    name: str
    columns: List[ColumnDef]
    rows: List[List[Any]]
    manifest_entry: ManifestEntry


@dataclass
class BinaryPart:
    """Binary part from CSV-MP"""
    name: str
    index: int
    mime_type: str
    size: int
    data: bytes
    manifest_entry: ManifestEntry


@dataclass
class TextPart:
    """Text part from CSV-MP"""
    name: str
    index: int
    mime_type: str
    content: str
    manifest_entry: ManifestEntry


@dataclass
class ValidationConfig:
    """Validation configuration for different scenarios"""
    validate_on_write: bool = True
    validate_on_read: bool = True
    verify_hash: bool = False
    throw_on_error: bool = True


class ValidationScenarios:
    """Default validation configurations for different use cases"""
    
    DEFAULT = ValidationConfig(
        validate_on_write=True,
        validate_on_read=True,
        verify_hash=False,
        throw_on_error=True
    )
    
    GAME_SAVE = ValidationConfig(
        validate_on_write=True,
        validate_on_read=False,
        verify_hash=False,
        throw_on_error=False
    )
    
    IOT_TELEMETRY = ValidationConfig(
        validate_on_write=False,
        validate_on_read=True,
        verify_hash=False,
        throw_on_error=False
    )
    
    DATA_PIPELINE = ValidationConfig(
        validate_on_write=True,
        validate_on_read=False,
        verify_hash=True,
        throw_on_error=True
    )
    
    SECURITY_MAX = ValidationConfig(
        validate_on_write=True,
        validate_on_read=True,
        verify_hash=True,
        throw_on_error=True
    )


class CsvMpException(Exception):
    """Base exception for CSV-MP errors"""
    pass


class ReferenceException(CsvMpException):
    """Reference validation error"""
    pass


class IndexException(CsvMpException):
    """Index sequence error"""
    pass


class TypeException(CsvMpException):
    """Type validation error"""
    pass


class IntegrityException(CsvMpException):
    """Data integrity error"""
    pass


class FormatException(CsvMpException):
    """Format parsing error"""
    pass
