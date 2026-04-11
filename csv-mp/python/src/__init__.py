"""
CSV-MP Python Package
Version: 0.2.0-alpha
"""

from .types import (
    BaseType,
    CollectionType,
    PartFormat,
    ManifestEntry,
    ColumnDef,
    Table,
    BinaryPart,
    TextPart,
    ValidationConfig,
    ValidationScenarios,
    CsvMpException,
    ReferenceException,
    IndexException,
    TypeException,
    IntegrityException,
    FormatException
)

from .parser import (
    CsvMpParser,
    parse,
    serialize,
    # Simple API
    deserialize,
    to_csv_mp,
    from_csv_mp,
    read_csv_mp,
    write_csv_mp
)

__version__ = "0.2.0-alpha"
__all__ = [
    # Types
    "BaseType",
    "CollectionType",
    "PartFormat",
    "ManifestEntry",
    "ColumnDef",
    "Table",
    "BinaryPart",
    "TextPart",
    "ValidationConfig",
    "ValidationScenarios",
    # Exceptions
    "CsvMpException",
    "ReferenceException",
    "IndexException",
    "TypeException",
    "IntegrityException",
    "FormatException",
    # Parser
    "CsvMpParser",
    "parse",
    "serialize",
    "deserialize",
    "to_csv_mp",
    "from_csv_mp",
    "read_csv_mp",
    "write_csv_mp"
]
