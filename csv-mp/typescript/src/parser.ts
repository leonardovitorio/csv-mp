/**
 * CSV-MP Parser and Serializer
 * Version: 0.2.0-alpha
 */

import {
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
} from './types';
import * as crypto from 'crypto';

export class CsvMpParser {
  private config: ValidationConfig;

  constructor(config: ValidationConfig = ValidationScenarios.default) {
    this.config = config;
  }

  /**
   * Parse a complete CSV-MP file content
   */
  parse(content: string): {
    manifest: ManifestEntry[];
    tables: Table[];
    binaryParts: BinaryPart[];
    textParts: TextPart[];
  } {
    const lines = content.split('\n');
    let lineIndex = 0;

    // Parse manifesto
    const manifest = this.parseManifesto(lines, lineIndex);
    lineIndex = manifest.lineIndex;

    // Skip empty line after manifesto
    while (lineIndex < lines.length && lines[lineIndex].trim() === '') {
      lineIndex++;
    }

    const tables: Table[] = [];
    const binaryParts: BinaryPart[] = [];
    const textParts: TextPart[] = [];

    // Parse parts
    while (lineIndex < lines.length) {
      const line = lines[lineIndex];

      if (line.startsWith('&:')) {
        // Table part
        const result = this.parseTable(lines, lineIndex, manifest);
        tables.push(result.table);
        lineIndex = result.lineIndex;
      } else if (line.startsWith('[PART:')) {
        // Binary part
        const result = this.parseBinaryPart(lines, lineIndex, manifest);
        binaryParts.push(result.part);
        lineIndex = result.lineIndex;
      } else if (line.startsWith('[TEXT:')) {
        // Text part
        const result = this.parseTextPart(lines, lineIndex, manifest);
        textParts.push(result.part);
        lineIndex = result.lineIndex;
      } else if (line.trim() === '' || line.startsWith('#')) {
        // Empty line or comment, skip
        lineIndex++;
      } else {
        // Unknown format, skip
        lineIndex++;
      }
    }

    // Validate references if configured
    if (this.config.validateOnRead) {
      this.validateReferences(manifest, tables);
    }

    return { manifest, tables, binaryParts, textParts };
  }

  /**
   * Parse manifesto section
   */
  private parseManifesto(lines: string[], startIndex: number): { manifest: ManifestEntry[]; lineIndex: number } {
    const manifest: ManifestEntry[] = [];
    let lineIndex = startIndex;

    // Skip comments and find header
    while (lineIndex < lines.length) {
      const line = lines[lineIndex].trim();
      if (line.startsWith('#') || line === '') {
        lineIndex++;
        continue;
      }
      if (line.startsWith('&|')) {
        break;
      }
      throw new FormatException(`Invalid manifesto format: expected &| prefix at line ${lineIndex + 1}`);
    }

    if (lineIndex >= lines.length) {
      throw new FormatException('Manifesto header not found');
    }

    // Parse header
    const headerLine = lines[lineIndex];
    const headers = headerLine.substring(2).split('|');
    const expectedHeaders = ['type', 'description', 'count', 'format', 'author', 'version', 'hash'];
    
    // First column is index, rest are headers
    if (headers.length < 7) {
      throw new FormatException('Invalid manifesto header: missing required columns');
    }

    lineIndex++;

    // Parse entries
    let expectedIndex = 0;
    while (lineIndex < lines.length) {
      const line = lines[lineIndex].trim();
      
      // Stop at empty line (end of manifesto)
      if (line === '') {
        lineIndex++;
        break;
      }

      // Skip comments
      if (line.startsWith('#')) {
        lineIndex++;
        continue;
      }

      const columns = line.split('|');
      if (columns.length < 7) {
        throw new FormatException(`Invalid manifesto entry at line ${lineIndex + 1}: insufficient columns`);
      }

      const index = parseInt(columns[0], 10);
      
      // Validate index sequence
      if (index !== expectedIndex) {
        throw new IndexException(`Index sequence error: expected ${expectedIndex}, got ${index}`);
      }

      const entry: ManifestEntry = {
        index,
        type: columns[1],
        description: columns[2] || undefined,
        count: parseInt(columns[3], 10),
        format: columns[4],
        author: columns[5] || undefined,
        version: columns[6],
        hash: columns[7] || undefined
      };

      // Validate hash if present
      if (entry.hash && entry.hash.length !== 64) {
        throw new IntegrityException(`Invalid hash for part '${entry.type}': must be 64 character SHA-256 hex string`);
      }

      manifest.push(entry);
      expectedIndex++;
      lineIndex++;
    }

    return { manifest, lineIndex };
  }

  /**
   * Parse table section
   */
  private parseTable(lines: string[], startIndex: number, manifest: ManifestEntry[]): { table: Table; lineIndex: number } {
    let lineIndex = startIndex;
    const headerLine = lines[lineIndex];

    if (!headerLine.startsWith('&:')) {
      throw new FormatException(`Invalid table header: expected &: prefix at line ${lineIndex + 1}`);
    }

    // Parse header to get column definitions
    const headerContent = headerLine.substring(2);
    const columns = this.parseColumnDefinitions(headerContent);

    lineIndex++;

    // Find corresponding manifest entry
    const tableName = this.inferTableName(columns, manifest);
    const manifestEntry = manifest.find(m => m.type === tableName && m.format === 'csv/default');

    if (!manifestEntry) {
      throw new FormatException(`Manifest entry not found for table '${tableName}'`);
    }

    // Parse rows
    const rows: any[][] = [];
    let expectedRowIndex = 0;

    while (lineIndex < lines.length) {
      const line = lines[lineIndex].trim();

      // Stop at empty line, table header, or special part
      if (line === '' || line.startsWith('&:') || line.startsWith('[PART:') || line.startsWith('[TEXT:')) {
        break;
      }

      // Skip comments
      if (line.startsWith('#')) {
        lineIndex++;
        continue;
      }

      const values = this.parseCsvLine(line);
      
      // Validate row index
      const rowIndex = parseInt(values[0], 10);
      if (rowIndex !== expectedRowIndex) {
        throw new IndexException(`Row index sequence error: expected ${expectedRowIndex}, got ${rowIndex}`);
      }

      // Validate column count (data should have index + columns)
      if (values.length !== columns.length + 1) {
        throw new TypeException(`Column count mismatch: expected ${columns.length + 1}, got ${values.length}`);
      }

      // Validate and convert types
      const convertedRow = this.convertRowTypes(values, columns);
      rows.push(convertedRow);

      expectedRowIndex++;
      lineIndex++;
    }

    // Validate row count matches manifesto
    if (this.config.validateOnRead && rows.length !== manifestEntry.count) {
      throw new IntegrityException(`Row count mismatch: manifesto says ${manifestEntry.count}, found ${rows.length}`);
    }

    const table: Table = {
      name: tableName,
      columns,
      rows,
      manifestEntry
    };

    return { table, lineIndex };
  }

  /**
   * Parse column definitions from header
   */
  private parseColumnDefinitions(headerContent: string): ColumnDef[] {
    const columns: ColumnDef[] = [];
    const parts = headerContent.split(',');

    for (const part of parts) {
      const trimmed = part.trim();
      const colonIndex = trimmed.indexOf(':');
      
      if (colonIndex === -1) {
        throw new FormatException(`Invalid column definition: '${trimmed}' - missing type separator ':'`);
      }

      const name = trimmed.substring(0, colonIndex);
      const typeSpec = trimmed.substring(colonIndex + 1);

      const { baseType, collectionType, tupleTypes } = this.parseTypeSpecification(typeSpec);

      columns.push({
        name,
        baseType,
        collectionType,
        tupleTypes
      });
    }

    return columns;
  }

  /**
   * Parse type specification (e.g., "string", "int", "string[]", "[number,number]")
   */
  private parseTypeSpecification(typeSpec: string): { 
    baseType: BaseType; 
    collectionType: CollectionType; 
    tupleTypes?: BaseType[] 
  } {
    // Check for array type (ends with [])
    if (typeSpec.endsWith('[]')) {
      const baseTypeStr = typeSpec.substring(0, typeSpec.length - 2);
      return {
        baseType: this.stringToBaseType(baseTypeStr),
        collectionType: CollectionType.Array
      };
    }

    // Check for tuple type (starts with [ and contains comma)
    if (typeSpec.startsWith('[') && typeSpec.endsWith(']') && typeSpec.includes(',')) {
      const innerTypes = typeSpec.substring(1, typeSpec.length - 1).split(',');
      const tupleTypes = innerTypes.map(t => this.stringToBaseType(t.trim()));
      return {
        baseType: BaseType.Any,
        collectionType: CollectionType.Tuple,
        tupleTypes
      };
    }

    // Special handling for Reference, Text
    if (typeSpec === 'Reference') {
      return {
        baseType: BaseType.Reference,
        collectionType: CollectionType.Single
      };
    }

    if (typeSpec === 'Text') {
      return {
        baseType: BaseType.String,
        collectionType: CollectionType.Text
      };
    }

    // Simple base type
    return {
      baseType: this.stringToBaseType(typeSpec),
      collectionType: CollectionType.Single
    };
  }

  /**
   * Convert string type name to BaseType enum
   */
  private stringToBaseType(typeStr: string): BaseType {
    const typeMap: Record<string, BaseType> = {
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
    };

    const normalized = typeStr.toLowerCase();
    if (!(normalized in typeMap)) {
      throw new TypeException(`Unknown type: '${typeStr}'`);
    }

    return typeMap[normalized];
  }

  /**
   * Parse a single CSV line respecting RFC 4180 quoting rules
   */
  private parseCsvLine(line: string): string[] {
    const values: string[] = [];
    let current = '';
    let inQuotes = false;
    let i = 0;

    while (i < line.length) {
      const char = line[i];

      if (inQuotes) {
        if (char === '"') {
          // Check for escaped quote
          if (i + 1 < line.length && line[i + 1] === '"') {
            current += '"';
            i += 2;
            continue;
          } else {
            // End of quoted field
            inQuotes = false;
            i++;
            continue;
          }
        } else {
          current += char;
          i++;
        }
      } else {
        if (char === '"') {
          inQuotes = true;
          i++;
        } else if (char === ',') {
          values.push(current);
          current = '';
          i++;
        } else {
          current += char;
          i++;
        }
      }
    }

    // Add last value
    values.push(current);

    return values;
  }

  /**
   * Convert row values according to column types
   */
  private convertRowTypes(values: string[], columns: ColumnDef[]): any[] {
    const converted: any[] = [];

    // First value is index, keep as number
    converted.push(parseInt(values[0], 10));

    // Convert remaining values according to column types
    for (let i = 0; i < columns.length; i++) {
      const value = values[i + 1];
      const column = columns[i];
      converted.push(this.convertValue(value, column));
    }

    return converted;
  }

  /**
   * Convert a single value according to its column definition
   */
  private convertValue(value: string, column: ColumnDef): any {
    // Handle empty values
    if (value === '' || value === null || value === undefined) {
      return null;
    }

    switch (column.baseType) {
      case BaseType.String:
        return value;

      case BaseType.Number:
        const num = parseFloat(value);
        if (isNaN(num)) {
          throw new TypeException(`Invalid number for column '${column.name}': '${value}'`);
        }
        return num;

      case BaseType.Int:
        const intVal = parseInt(value, 10);
        if (isNaN(intVal) || intVal < -2147483648 || intVal > 2147483647) {
          throw new TypeException(`Invalid int for column '${column.name}': '${value}'`);
        }
        return intVal;

      case BaseType.Long:
        const longVal = BigInt(value);
        return longVal.toString();

      case BaseType.Boolean:
        if (value !== 'true' && value !== 'false') {
          throw new TypeException(`Invalid boolean for column '${column.name}': '${value}'`);
        }
        return value === 'true';

      case BaseType.Date:
        // Validate date format yyyy-MM-dd
        if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
          throw new TypeException(`Invalid date for column '${column.name}': '${value}'`);
        }
        return value;

      case BaseType.DateTime:
        // Validate ISO 8601 format
        if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})?$/.test(value)) {
          throw new TypeException(`Invalid datetime for column '${column.name}': '${value}'`);
        }
        return value;

      case BaseType.Object:
        try {
          return JSON.parse(value);
        } catch (e) {
          throw new TypeException(`Invalid JSON object for column '${column.name}': '${value}'`);
        }

      case BaseType.Reference:
        // Validate reference format @PartName.Index
        if (!value.startsWith('@')) {
          throw new TypeException(`Invalid reference for column '${column.name}': '${value}' - must start with '@'`);
        }
        return value;

      default:
        return value;
    }
  }

  /**
   * Parse binary part
   */
  private parseBinaryPart(lines: string[], startIndex: number, manifest: ManifestEntry[]): { part: BinaryPart; lineIndex: number } {
    const startLine = lines[startIndex];
    
    // Parse [PART:Name.Index|mime|size]
    const match = startLine.match(/^\[PART:([^.]+)\.(\d+)\|([^|]+)\|(\d+)\]$/);
    if (!match) {
      throw new FormatException(`Invalid binary part start marker at line ${startIndex + 1}`);
    }

    const [, name, indexStr, mimeType, sizeStr] = match;
    const index = parseInt(indexStr, 10);
    const size = parseInt(sizeStr, 10);

    // Find end marker and extract data
    let lineIndex = startIndex + 1;
    const dataLines: string[] = [];

    while (lineIndex < lines.length) {
      const line = lines[lineIndex];
      if (line === `[END:${name}.${index}]`) {
        break;
      }
      dataLines.push(line);
      lineIndex++;
    }

    if (lineIndex >= lines.length) {
      throw new FormatException(`Missing end marker for binary part '${name}.${index}'`);
    }

    // For text-based representation, we'll store as Buffer
    // In real implementation, this would be raw bytes
    const dataString = dataLines.join('\n');
    const data = Buffer.from(dataString, 'utf-8');

    // Find manifest entry
    const manifestEntry = manifest.find(m => m.type === name && m.index === index);
    if (!manifestEntry) {
      throw new FormatException(`Manifest entry not found for binary part '${name}.${index}'`);
    }

    const part: BinaryPart = {
      name,
      index,
      mimeType,
      size: data.length,
      data,
      manifestEntry
    };

    return { part, lineIndex: lineIndex + 1 };
  }

  /**
   * Parse text part
   */
  private parseTextPart(lines: string[], startIndex: number, manifest: ManifestEntry[]): { part: TextPart; lineIndex: number } {
    const startLine = lines[startIndex];
    
    // Parse [TEXT:Name.Index|mime]
    const match = startLine.match(/^\[TEXT:([^.]+)\.(\d+)\|([^|]+)\]$/);
    if (!match) {
      throw new FormatException(`Invalid text part start marker at line ${startIndex + 1}`);
    }

    const [, name, indexStr, mimeType] = match;
    const index = parseInt(indexStr, 10);

    // Find end marker and extract content
    let lineIndex = startIndex + 1;
    const contentLines: string[] = [];

    while (lineIndex < lines.length) {
      const line = lines[lineIndex];
      if (line === `[END:${name}.${index}]`) {
        break;
      }
      contentLines.push(line);
      lineIndex++;
    }

    if (lineIndex >= lines.length) {
      throw new FormatException(`Missing end marker for text part '${name}.${index}'`);
    }

    const content = contentLines.join('\n');

    // Find manifest entry
    const manifestEntry = manifest.find(m => m.type === name && m.index === index);
    if (!manifestEntry) {
      throw new FormatException(`Manifest entry not found for text part '${name}.${index}'`);
    }

    const part: TextPart = {
      name,
      index,
      mimeType,
      content,
      manifestEntry
    };

    return { part, lineIndex: lineIndex + 1 };
  }

  /**
   * Infer table name from columns and manifest
   */
  private inferTableName(columns: ColumnDef[], manifest: ManifestEntry[]): string {
    // Try to find matching manifest entry by checking which table format would match
    // This is a simplified approach - in practice, the table name might be explicit
    
    // For now, use the first csv/default entry that hasn't been used
    for (const entry of manifest) {
      if (entry.format === 'csv/default') {
        return entry.type;
      }
    }
    
    return 'Unknown';
  }

  /**
   * Validate references between tables
   */
  private validateReferences(manifest: ManifestEntry[], tables: Table[]): void {
    // Build a map of valid references
    const validReferences = new Set<string>();

    for (const entry of manifest) {
      if (entry.format === 'csv/default') {
        // Find corresponding table
        const table = tables.find(t => t.name === entry.type);
        if (table) {
          for (let i = 0; i < table.rows.length; i++) {
            validReferences.add(`${entry.type}.${i}`);
          }
        }
      } else {
        // Binary and text parts
        for (let i = 0; i < entry.count; i++) {
          validReferences.add(`${entry.type}.${i}`);
        }
      }
    }

    // Validate all references in tables
    for (const table of tables) {
      for (let rowIndex = 0; rowIndex < table.rows.length; rowIndex++) {
        const row = table.rows[rowIndex];
        for (let colIndex = 0; colIndex < table.columns.length; colIndex++) {
          const column = table.columns[colIndex];
          if (column.baseType === BaseType.Reference) {
            const refValue = row[colIndex + 1]; // +1 because first column is index
            if (refValue && !validReferences.has(refValue.substring(1))) { // Remove @ prefix
              throw new ReferenceException(`Reference '${refValue}' not found`);
            }
          }
        }
      }
    }

    // Backward validation: check that tables with Reference columns are actually referenced
    // This is optional and may be too strict for some use cases
  }

  /**
   * Serialize data to CSV-MP format
   */
  serialize(
    manifest: ManifestEntry[],
    tables: Table[],
    binaryParts: BinaryPart[] = [],
    textParts: TextPart[] = []
  ): string {
    let output = '';

    // Write manifesto
    output += '# CSV-MP v0.2 Manifesto\n';
    output += `# Generated: ${new Date().toISOString()}\n`;
    output += '\n';
    output += '&|type|description|count|format|author|version|hash\n';

    for (const entry of manifest) {
      const hash = entry.hash || '';
      const description = entry.description || '';
      const author = entry.author || '';
      output += `${entry.index}|${entry.type}|${description}|${entry.count}|${entry.format}|${author}|${entry.version}|${hash}\n`;
    }

    // Empty line after manifesto
    output += '\n';

    // Write tables
    for (const table of tables) {
      // Write header
      const headerCols = table.columns.map(c => {
        const typeStr = this.baseTypeToString(c.baseType);
        if (c.collectionType === CollectionType.Array) {
          return `${c.name}:${typeStr}[]`;
        } else if (c.collectionType === CollectionType.Tuple && c.tupleTypes) {
          const tupleTypes = c.tupleTypes.map(t => this.baseTypeToString(t)).join(',');
          return `${c.name}:[${tupleTypes}]`;
        } else {
          return `${c.name}:${typeStr}`;
        }
      });
      output += `&:${headerCols.join(',')}\n`;

      // Write rows
      for (const row of table.rows) {
        const values = row.map((v, i) => {
          if (i === 0) {
            // Index column
            return v.toString();
          }
          return this.valueToString(v, table.columns[i - 1]);
        });
        output += values.join(',') + '\n';
      }

      output += '\n';
    }

    // Write binary parts
    for (const part of binaryParts) {
      output += `[PART:${part.name}.${part.index}|${part.mimeType}|${part.size}]\n`;
      output += part.data.toString('utf-8') + '\n';
      output += `[END:${part.name}.${part.index}]\n\n`;
    }

    // Write text parts
    for (const part of textParts) {
      output += `[TEXT:${part.name}.${part.index}|${part.mimeType}]\n`;
      output += part.content + '\n';
      output += `[END:${part.name}.${part.index}]\n\n`;
    }

    return output;
  }

  /**
   * Convert BaseType to string representation
   */
  private baseTypeToString(baseType: BaseType): string {
    const typeMap: Record<BaseType, string> = {
      [BaseType.Any]: 'any',
      [BaseType.String]: 'string',
      [BaseType.Number]: 'number',
      [BaseType.Long]: 'long',
      [BaseType.Int]: 'int',
      [BaseType.Boolean]: 'boolean',
      [BaseType.Date]: 'date',
      [BaseType.DateTime]: 'datetime',
      [BaseType.Object]: 'object',
      [BaseType.Reference]: 'Reference'
    };
    return typeMap[baseType];
  }

  /**
   * Convert value to CSV string representation
   */
  private valueToString(value: any, column: ColumnDef): string {
    if (value === null || value === undefined) {
      return '';
    }

    switch (column.baseType) {
      case BaseType.String:
        // Quote if contains special characters
        if (value.includes(',') || value.includes('"') || value.includes('\n')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;

      case BaseType.Object:
        return `"${JSON.stringify(value).replace(/"/g, '""')}"`;

      case BaseType.Date:
      case BaseType.DateTime:
        return `"${value}"`;

      case BaseType.Reference:
        return value; // References are not quoted

      case BaseType.Boolean:
        return value ? 'true' : 'false';

      default:
        return value.toString();
    }
  }

  /**
   * Calculate SHA-256 hash of content
   */
  calculateHash(content: string): string {
    return crypto.createHash('sha256').update(content).digest('hex');
  }
}

// Export convenience functions
export function parse(content: string, config?: ValidationConfig): ReturnType<CsvMpParser['parse']> {
  const parser = new CsvMpParser(config);
  return parser.parse(content);
}

export function serialize(
  manifest: ManifestEntry[],
  tables: Table[],
  binaryParts?: BinaryPart[],
  textParts?: TextPart[],
  config?: ValidationConfig
): string {
  const parser = new CsvMpParser(config);
  return parser.serialize(manifest, tables, binaryParts, textParts);
}

/**
 * Simple Deserialization API
 * Converts CSV-MP content to plain JavaScript objects
 */
export function deserialize<T extends Record<string, any>>(content: string, config?: ValidationConfig): T {
  const parser = new CsvMpParser(config);
  const result = parser.parse(content);
  
  const output: any = {};
  
  // Convert tables to object arrays by type name
  for (const table of result.tables) {
    const rows: any[] = table.rows.map(row => {
      const obj: any = {};
      // Skip first column (index) and map column names to values
      for (let i = 0; i < table.columns.length; i++) {
        obj[table.columns[i].name] = row[i + 1];
      }
      return obj;
    });
    output[table.name] = rows;
  }
  
  // Add binary parts
  if (result.binaryParts.length > 0) {
    output._binary = result.binaryParts;
  }
  
  // Add text parts
  if (result.textParts.length > 0) {
    output._text = result.textParts;
  }
  
  return output as T;
}

/**
 * Simple Serialization API - Objects to CSV-MP
 * Converts plain JavaScript objects to CSV-MP format
 */
export function toCsvMp(data: Record<string, any>, options?: {
  author?: string;
  version?: string;
  description?: string;
}): string {
  const author = options?.author || 'csv-mp';
  const version = options?.version || '0.2';
  const description = options?.description || 'Generated by csv-mp';
  
  const manifest: ManifestEntry[] = [];
  const tables: Table[] = [];
  let partIndex = 0;
  
  // Process each key in the data object
  for (const [key, value] of Object.entries(data)) {
    // Skip internal keys
    if (key.startsWith('_')) continue;
    
    if (Array.isArray(value)) {
      // It's a table
      if (value.length === 0) continue;
      
      // Infer column types from first row
      const firstRow = value[0];
      const columns: ColumnDef[] = [];
      
      for (const [colName, colValue] of Object.entries(firstRow)) {
        let baseType = BaseType.String;
        
        if (typeof colValue === 'number') {
          baseType = Number.isInteger(colValue) ? BaseType.Int : BaseType.Number;
        } else if (typeof colValue === 'boolean') {
          baseType = BaseType.Boolean;
        } else if (typeof colValue === 'string' && colValue.startsWith('@')) {
          baseType = BaseType.Reference;
        } else if (typeof colValue === 'object') {
          baseType = BaseType.Object;
        }
        
        columns.push({
          name: colName,
          baseType,
          collectionType: CollectionType.Single
        });
      }
      
      // Add index column to rows
      const rows = value.map((row, idx) => {
        const rowArray: any[] = [idx];
        for (const col of columns) {
          rowArray.push(row[col.name]);
        }
        return rowArray;
      });
      
      const table: Table = {
        name: key,
        columns,
        rows,
        manifestEntry: {
          index: partIndex,
          type: key,
          description: `${key} data`,
          count: value.length,
          format: 'csv/default',
          author,
          version,
          hash: ''
        }
      };
      
      manifest.push(table.manifestEntry);
      tables.push(table);
      partIndex++;
    }
  }
  
  return serialize(manifest, tables);
}

/**
 * Simple Deserialization API - CSV-MP to Objects
 * Alias for deserialize() for consistency
 */
export function fromCsvMp<T extends Record<string, any>>(content: string, config?: ValidationConfig): T {
  return deserialize<T>(content, config);
}

/**
 * Read CSV-MP from file (Node.js)
 */
export async function readCsvMp(filePath: string, config?: ValidationConfig): Promise<any> {
  const fs = await import('fs');
  const content = fs.readFileSync(filePath, 'utf-8');
  return deserialize(content, config);
}

/**
 * Write CSV-MP to file (Node.js)
 */
export async function writeCsvMp(filePath: string, data: Record<string, any>, options?: {
  author?: string;
  version?: string;
  description?: string;
}): Promise<void> {
  const fs = await import('fs');
  const content = toCsvMp(data, options);
  fs.writeFileSync(filePath, content, 'utf-8');
}
