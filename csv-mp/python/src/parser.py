"""
CSV-MP Python Parser and Serializer
Version: 0.8.0-alpha
License: CC0 1.0 (Public Domain)
"""

import re
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from .types import (
    BaseType,
    CollectionType,
    ManifestEntry,
    ColumnDef,
    Table,
    BinaryPart,
    TextPart,
    ValidationConfig,
    ValidationScenarios,
    ReferenceException,
    IndexException,
    TypeException,
    IntegrityException,
    FormatException
)


class CsvMpParser:
    """CSV-MP Parser and Serializer"""
    
    def __init__(self, config: Optional[ValidationConfig] = None):
        self.config = config or ValidationScenarios.DEFAULT
    
    def parse(self, content: str) -> Dict[str, Any]:
        """Parse a complete CSV-MP file content"""
        lines = content.split('\n')
        line_index = 0
        
        # Parse manifesto
        manifest, line_index = self._parse_manifesto(lines, line_index)
        
        # Skip empty lines after manifesto
        while line_index < len(lines) and lines[line_index].strip() == '':
            line_index += 1
        
        tables: List[Table] = []
        binary_parts: List[BinaryPart] = []
        text_parts: List[TextPart] = []
        
        # Parse parts
        while line_index < len(lines):
            line = lines[line_index]
            
            if line.startswith('&:'):
                # Table part
                table, line_index = self._parse_table(lines, line_index, manifest)
                tables.append(table)
            elif line.startswith('[PART:'):
                # Binary part
                part, line_index = self._parse_binary_part(lines, line_index, manifest)
                binary_parts.append(part)
            elif line.startswith('[TEXT:'):
                # Text part
                part, line_index = self._parse_text_part(lines, line_index, manifest)
                text_parts.append(part)
            elif line.strip() == '' or line.startswith('#'):
                # Empty line or comment, skip
                line_index += 1
            else:
                # Unknown format, skip
                line_index += 1
        
        # Validate references if configured
        if self.config.validate_on_read:
            self._validate_references(manifest, tables)
        
        return {
            'manifest': manifest,
            'tables': tables,
            'binary_parts': binary_parts,
            'text_parts': text_parts
        }
    
    def _parse_manifesto(self, lines: List[str], start_index: int) -> Tuple[List[ManifestEntry], int]:
        """Parse manifesto section"""
        manifest: List[ManifestEntry] = []
        line_index = start_index
        
        # Skip comments and find header
        while line_index < len(lines):
            line = lines[line_index].strip()
            if line.startswith('#') or line == '':
                line_index += 1
                continue
            if line.startswith('&|'):
                break
            raise FormatException(f'Invalid manifesto format: expected &| prefix at line {line_index + 1}')
        
        if line_index >= len(lines):
            raise FormatException('Manifesto header not found')
        
        # Parse header
        header_line = lines[line_index]
        headers = header_line[2:].split('|')
        
        if len(headers) < 7:
            raise FormatException('Invalid manifesto header: missing required columns')
        
        line_index += 1
        
        # Parse entries
        expected_index = 0
        while line_index < len(lines):
            line = lines[line_index].strip()
            
            # Stop at empty line (end of manifesto)
            if line == '':
                line_index += 1
                break
            
            # Skip comments
            if line.startswith('#'):
                line_index += 1
                continue
            
            columns = line.split('|')
            if len(columns) < 7:
                raise FormatException(f'Invalid manifesto entry at line {line_index + 1}: insufficient columns')
            
            index = int(columns[0])
            
            # Validate index sequence
            if index != expected_index:
                raise IndexException(f'Index sequence error: expected {expected_index}, got {index}')
            
            entry = ManifestEntry(
                index=index,
                type=columns[1],
                description=columns[2] or None,
                count=int(columns[3]),
                format=columns[4],
                author=columns[5] or None,
                version=columns[6],
                hash=columns[7] or None
            )
            
            # Validate hash if present
            if entry.hash and len(entry.hash) != 64:
                raise IntegrityException(f"Invalid hash for part '{entry.type}': must be 64 character SHA-256 hex string")
            
            manifest.append(entry)
            expected_index += 1
            line_index += 1
        
        return manifest, line_index
    
    def _parse_table(self, lines: List[str], start_index: int, manifest: List[ManifestEntry]) -> Tuple[Table, int]:
        """Parse table section"""
        line_index = start_index
        header_line = lines[line_index]
        
        if not header_line.startswith('&:'):
            raise FormatException(f'Invalid table header: expected &: prefix at line {line_index + 1}')
        
        # Parse header to get column definitions
        header_content = header_line[2:]
        columns = self._parse_column_definitions(header_content)
        
        line_index += 1
        
        # Find corresponding manifest entry
        table_name = self._infer_table_name(columns, manifest)
        manifest_entry = next((m for m in manifest if m.type == table_name and m.format == 'csv/default'), None)
        
        if not manifest_entry:
            raise FormatException(f"Manifest entry not found for table '{table_name}'")
        
        # Parse rows
        rows: List[List[Any]] = []
        expected_row_index = 0
        
        while line_index < len(lines):
            line = lines[line_index].strip()
            
            # Stop at empty line, table header, or special part
            if line == '' or line.startswith('&:') or line.startswith('[PART:') or line.startswith('[TEXT:'):
                break
            
            # Skip comments
            if line.startswith('#'):
                line_index += 1
                continue
            
            values = self._parse_csv_line(line)
            
            # Validate row index
            row_index = int(values[0])
            if row_index != expected_row_index:
                raise IndexException(f'Row index sequence error: expected {expected_row_index}, got {row_index}')
            
            # Validate column count
            if len(values) != len(columns) + 1:
                raise TypeException(f'Column count mismatch: expected {len(columns) + 1}, got {len(values)}')
            
            # Validate and convert types
            converted_row = self._convert_row_types(values, columns)
            rows.append(converted_row)
            
            expected_row_index += 1
            line_index += 1
        
        # Validate row count matches manifesto
        if self.config.validate_on_read and len(rows) != manifest_entry.count:
            raise IntegrityException(f"Row count mismatch: manifesto says {manifest_entry.count}, found {len(rows)}")
        
        table = Table(
            name=table_name,
            columns=columns,
            rows=rows,
            manifest_entry=manifest_entry
        )
        
        return table, line_index
    
    def _parse_column_definitions(self, header_content: str) -> List[ColumnDef]:
        """Parse column definitions from header"""
        columns: List[ColumnDef] = []
        parts = header_content.split(',')
        
        for part in parts:
            trimmed = part.strip()
            colon_index = trimmed.find(':')
            
            if colon_index == -1:
                raise FormatException(f"Invalid column definition: '{trimmed}' - missing type separator ':'")
            
            name = trimmed[:colon_index]
            type_spec = trimmed[colon_index + 1:]
            
            base_type, collection_type, tuple_types = self._parse_type_specification(type_spec)
            
            columns.append(ColumnDef(
                name=name,
                base_type=base_type,
                collection_type=collection_type,
                tuple_types=tuple_types
            ))
        
        return columns
    
    def _parse_type_specification(self, type_spec: str) -> Tuple[BaseType, CollectionType, Optional[List[BaseType]]]:
        """Parse type specification"""
        # Check for array type
        if type_spec.endswith('[]'):
            base_type_str = type_spec[:-2]
            return self._string_to_base_type(base_type_str), CollectionType.Array, None
        
        # Check for tuple type
        if type_spec.startswith('[') and type_spec.endswith(']') and ',' in type_spec:
            inner_types = type_spec[1:-1].split(',')
            tuple_types = [self._string_to_base_type(t.strip()) for t in inner_types]
            return BaseType.Any, CollectionType.Tuple, tuple_types
        
        # Special handling for Reference
        if type_spec == 'Reference':
            return BaseType.Reference, CollectionType.Single, None
        
        # Simple base type
        return self._string_to_base_type(type_spec), CollectionType.Single, None
    
    def _string_to_base_type(self, type_str: str) -> BaseType:
        """Convert string type name to BaseType enum"""
        type_map = {
            'any': BaseType.Any,
            'string': BaseType.String,
            'number': BaseType.Number,
            'long': BaseType.Long,
            'int': BaseType.Int,
            'boolean': BaseType.Boolean,
            'date': BaseType.Date,
            'datetime': BaseType.DateTime,
            'object': BaseType.Object,
            'reference': BaseType.Reference
        }
        
        normalized = type_str.lower()
        if normalized not in type_map:
            raise TypeException(f"Unknown type: '{type_str}'")
        
        return type_map[normalized]
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Parse a single CSV line respecting RFC 4180 quoting rules"""
        values: List[str] = []
        current = ''
        in_quotes = False
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if in_quotes:
                if char == '"':
                    if i + 1 < len(line) and line[i + 1] == '"':
                        current += '"'
                        i += 2
                        continue
                    else:
                        in_quotes = False
                        i += 1
                        continue
                else:
                    current += char
                    i += 1
            else:
                if char == '"':
                    in_quotes = True
                    i += 1
                elif char == ',':
                    values.append(current)
                    current = ''
                    i += 1
                else:
                    current += char
                    i += 1
        
        values.append(current)
        return values
    
    def _convert_row_types(self, values: List[str], columns: List[ColumnDef]) -> List[Any]:
        """Convert row values according to column types"""
        converted: List[Any] = []
        
        # First value is index
        converted.append(int(values[0]))
        
        # Convert remaining values
        for i, column in enumerate(columns):
            value = values[i + 1]
            converted.append(self._convert_value(value, column))
        
        return converted
    
    def _convert_value(self, value: str, column: ColumnDef) -> Any:
        """Convert a single value according to its column definition"""
        if value == '' or value is None:
            return None
        
        if column.base_type == BaseType.String:
            return value
        
        elif column.base_type == BaseType.Number:
            try:
                return float(value)
            except ValueError:
                raise TypeException(f"Invalid number for column '{column.name}': '{value}'")
        
        elif column.base_type == BaseType.Int:
            try:
                int_val = int(value)
                if -2147483648 <= int_val <= 2147483647:
                    return int_val
                raise TypeException(f"Int out of range for column '{column.name}': '{value}'")
            except ValueError:
                raise TypeException(f"Invalid int for column '{column.name}': '{value}'")
        
        elif column.base_type == BaseType.Long:
            return int(value)
        
        elif column.base_type == BaseType.Boolean:
            if value not in ('true', 'false'):
                raise TypeException(f"Invalid boolean for column '{column.name}': '{value}'")
            return value == 'true'
        
        elif column.base_type == BaseType.Date:
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', value):
                raise TypeException(f"Invalid date for column '{column.name}': '{value}'")
            return value
        
        elif column.base_type == BaseType.DateTime:
            if not re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?$', value):
                raise TypeException(f"Invalid datetime for column '{column.name}': '{value}'")
            return value
        
        elif column.base_type == BaseType.Object:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise TypeException(f"Invalid JSON object for column '{column.name}': '{value}'")
        
        elif column.base_type == BaseType.Reference:
            if not value.startswith('@'):
                raise TypeException(f"Invalid reference for column '{column.name}': '{value}' - must start with '@'")
            return value
        
        return value
    
    def _infer_table_name(self, columns: List[ColumnDef], manifest: List[ManifestEntry]) -> str:
        """Infer table name from columns or manifest"""
        # Try to match with manifest entries
        for entry in manifest:
            if entry.format == 'csv/default':
                return entry.type
        return 'Unknown'
    
    def _parse_binary_part(self, lines: List[str], start_index: int, manifest: List[ManifestEntry]) -> Tuple[BinaryPart, int]:
        """Parse binary part"""
        start_line = lines[start_index]
        
        match = re.match(r'^\[PART:([^.]+)\.(\d+)\|([^|]+)\|(\d+)\]$', start_line)
        if not match:
            raise FormatException(f'Invalid binary part start marker at line {start_index + 1}')
        
        name, index_str, mime_type, size_str = match.groups()
        index = int(index_str)
        size = int(size_str)
        
        line_index = start_index + 1
        data_lines: List[str] = []
        
        while line_index < len(lines):
            line = lines[line_index]
            if line == f'[END:{name}.{index}]':
                break
            data_lines.append(line)
            line_index += 1
        
        if line_index >= len(lines):
            raise FormatException(f"Missing end marker for binary part '{name}.{index}'")
        
        data_string = '\n'.join(data_lines)
        data = data_string.encode('utf-8')
        
        manifest_entry = next((m for m in manifest if m.type == name and m.index == index), None)
        if not manifest_entry:
            raise FormatException(f"Manifest entry not found for binary part '{name}.{index}'")
        
        part = BinaryPart(
            name=name,
            index=index,
            mime_type=mime_type,
            size=len(data),
            data=data,
            manifest_entry=manifest_entry
        )
        
        return part, line_index + 1
    
    def _parse_text_part(self, lines: List[str], start_index: int, manifest: List[ManifestEntry]) -> Tuple[TextPart, int]:
        """Parse text part"""
        start_line = lines[start_index]
        
        match = re.match(r'^\[TEXT:([^.]+)\.(\d+)\|([^|]+)\]$', start_line)
        if not match:
            raise FormatException(f'Invalid text part start marker at line {start_index + 1}')
        
        name, index_str, mime_type = match.groups()
        index = int(index_str)
        
        line_index = start_index + 1
        content_lines: List[str] = []
        
        while line_index < len(lines):
            line = lines[line_index]
            if line == f'[END:{name}.{index}]':
                break
            content_lines.append(line)
            line_index += 1
        
        if line_index >= len(lines):
            raise FormatException(f"Missing end marker for text part '{name}.{index}'")
        
        content = '\n'.join(content_lines)
        
        manifest_entry = next((m for m in manifest if m.type == name and m.index == index), None)
        if not manifest_entry:
            raise FormatException(f"Manifest entry not found for text part '{name}.{index}'")
        
        part = TextPart(
            name=name,
            index=index,
            mime_type=mime_type,
            content=content,
            manifest_entry=manifest_entry
        )
        
        return part, line_index + 1
    
    def _validate_references(self, manifest: List[ManifestEntry], tables: List[Table]):
        """Validate references between tables"""
        # Build a set of valid references
        valid_refs = set()
        for entry in manifest:
            valid_refs.add(f'@{entry.type}')
        
        # Check forward references
        for table in tables:
            for row in table.rows:
                for i, col in enumerate(table.columns):
                    if col.base_type == BaseType.Reference:
                        ref_value = row[i + 1]
                        if ref_value:
                            # Extract part name from reference
                            match = re.match(r'^@([^.]+)\.(\d+)$', ref_value)
                            if match:
                                part_name = match.group(1)
                                if f'@{part_name}' not in valid_refs:
                                    raise ReferenceException(f"Reference '{ref_value}' not found")
    
    def serialize(self, manifest: List[ManifestEntry], tables: List[Table], 
                  binary_parts: Optional[List[BinaryPart]] = None,
                  text_parts: Optional[List[TextPart]] = None) -> str:
        """Serialize CSV-MP data to string"""
        output = '# CSV-MP v0.8 Manifesto\n'
        output += '&|type|description|count|format|author|version|hash\n'
        
        for entry in manifest:
            desc = entry.description or ''
            author = entry.author or ''
            hash_val = entry.hash or ''
            output += f'{entry.index}|{entry.type}|{desc}|{entry.count}|{entry.format}|{author}|{entry.version}|{hash_val}\n'
        
        output += '\n'
        
        # Write tables
        for table in tables:
            # Write header
            header_parts = [f'{col.name}:{self._base_type_to_string(col.base_type)}' for col in table.columns]
            output += f'&:{",".join(header_parts)}\n'
            
            # Write rows
            for row in table.rows:
                values = [str(row[0])]  # Index
                for i, col in enumerate(table.columns):
                    values.append(self._value_to_string(row[i + 1], col))
                output += ','.join(values) + '\n'
            
            output += '\n'
        
        # Write binary parts
        if binary_parts:
            for part in binary_parts:
                output += f'[PART:{part.name}.{part.index}|{part.mime_type}|{part.size}]\n'
                output += part.data.decode('utf-8', errors='replace') + '\n'
                output += f'[END:{part.name}.{part.index}]\n\n'
        
        # Write text parts
        if text_parts:
            for part in text_parts:
                output += f'[TEXT:{part.name}.{part.index}|{part.mime_type}]\n'
                output += part.content + '\n'
                output += f'[END:{part.name}.{part.index}]\n\n'
        
        return output
    
    def _base_type_to_string(self, base_type: BaseType) -> str:
        """Convert BaseType to string representation"""
        type_map = {
            BaseType.Any: 'any',
            BaseType.String: 'string',
            BaseType.Number: 'number',
            BaseType.Long: 'long',
            BaseType.Int: 'int',
            BaseType.Boolean: 'boolean',
            BaseType.Date: 'date',
            BaseType.DateTime: 'datetime',
            BaseType.Object: 'object',
            BaseType.Reference: 'Reference'
        }
        return type_map.get(base_type, 'string')
    
    def _value_to_string(self, value: Any, column: ColumnDef) -> str:
        """Convert value to CSV string representation"""
        if value is None:
            return ''
        
        if column.base_type == BaseType.String:
            if ',' in value or '"' in value or '\n' in value:
                return f'"{value.replace(chr(34), chr(34)+chr(34))}"'
            return value
        
        elif column.base_type == BaseType.Object:
            return f'"{json.dumps(value).replace(chr(34), chr(34)+chr(34))}"'
        
        elif column.base_type in (BaseType.Date, BaseType.DateTime):
            return f'"{value}"'
        
        elif column.base_type == BaseType.Reference:
            return value
        
        elif column.base_type == BaseType.Boolean:
            return 'true' if value else 'false'
        
        return str(value)
    
    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


# Convenience functions
def parse(content: str, config: Optional[ValidationConfig] = None) -> Dict[str, Any]:
    """Parse CSV-MP content"""
    parser = CsvMpParser(config)
    return parser.parse(content)


def serialize(manifest: List[ManifestEntry], tables: List[Table],
              binary_parts: Optional[List[BinaryPart]] = None,
              text_parts: Optional[List[TextPart]] = None,
              config: Optional[ValidationConfig] = None) -> str:
    """Serialize to CSV-MP format"""
    parser = CsvMpParser(config)
    return parser.serialize(manifest, tables, binary_parts, text_parts)


def deserialize(content: str, config: Optional[ValidationConfig] = None) -> Dict[str, Any]:
    """
    Simple Deserialization API
    Converts CSV-MP content to plain Python dictionaries
    """
    parser = CsvMpParser(config)
    result = parser.parse(content)
    
    output = {}
    
    # Convert tables to list of dicts by type name
    for table in result['tables']:
        rows = []
        for row in table.rows:
            obj = {}
            # Skip first column (index) and map column names to values
            for i, col in enumerate(table.columns):
                obj[col.name] = row[i + 1]
            rows.append(obj)
        output[table.name] = rows
    
    # Add binary parts
    if result['binary_parts']:
        output['_binary'] = result['binary_parts']
    
    # Add text parts
    if result['text_parts']:
        output['_text'] = result['text_parts']
    
    return output


def to_csv_mp(data: Dict[str, Any], options: Optional[Dict[str, str]] = None) -> str:
    """
    Simple Serialization API - Objects to CSV-MP
    Converts plain Python dictionaries to CSV-MP format
    """
    author = options.get('author', 'csv-mp') if options else 'csv-mp'
    version = options.get('version', '0.8') if options else '0.8'
    
    manifest: List[ManifestEntry] = []
    tables: List[Table] = []
    part_index = 0
    
    for key, value in data.items():
        # Skip internal keys
        if key.startswith('_'):
            continue
        
        if isinstance(value, list):
            if not value:
                continue
            
            # Infer column types from first row
            first_row = value[0]
            columns: List[ColumnDef] = []
            
            for col_name, col_value in first_row.items():
                base_type = BaseType.String
                
                if isinstance(col_value, bool):
                    base_type = BaseType.Boolean
                elif isinstance(col_value, int):
                    base_type = BaseType.Int
                elif isinstance(col_value, float):
                    base_type = BaseType.Number
                elif isinstance(col_value, str) and col_value.startswith('@'):
                    base_type = BaseType.Reference
                elif isinstance(col_value, dict):
                    base_type = BaseType.Object
                
                columns.append(ColumnDef(
                    name=col_name,
                    base_type=base_type,
                    collection_type=CollectionType.Single
                ))
            
            # Add index column to rows
            rows = []
            for idx, row in enumerate(value):
                row_array = [idx]
                for col in columns:
                    row_array.append(row[col.name])
                rows.append(row_array)
            
            table = Table(
                name=key,
                columns=columns,
                rows=rows,
                manifest_entry=ManifestEntry(
                    index=part_index,
                    type=key,
                    description=f'{key} data',
                    count=len(value),
                    format='csv/default',
                    author=author,
                    version=version,
                    hash=''
                )
            )
            
            manifest.append(table.manifest_entry)
            tables.append(table)
            part_index += 1
    
    return serialize(manifest, tables)


def from_csv_mp(content: str, config: Optional[ValidationConfig] = None) -> Dict[str, Any]:
    """
    Simple Deserialization API - CSV-MP to Objects
    Alias for deserialize() for consistency
    """
    return deserialize(content, config)


def read_csv_mp(file_path: str, config: Optional[ValidationConfig] = None) -> Dict[str, Any]:
    """Read CSV-MP from file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return deserialize(content, config)


def write_csv_mp(file_path: str, data: Dict[str, Any], options: Optional[Dict[str, str]] = None):
    """Write CSV-MP to file"""
    content = to_csv_mp(data, options)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
