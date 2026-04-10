/**
 * CSV-MP TypeScript Implementation
 * Version: 0.8.0-alpha
 * License: CC0 1.0 (Public Domain)
 */

/**
 * BaseTypes - Define o que o dado é
 */
export enum BaseType {
  Any = 0,
  String = 1,
  Number = 2,
  Long = 3,
  Int = 4,
  Boolean = 5,
  Date = 6,
  DateTime = 7,
  Object = 8,
  Reference = 9
}

/**
 * CollectionTypes - Define como o dado é organizado
 */
export enum CollectionType {
  Single = 0,
  Array = 1,
  Tuple = 2,
  File = 3,
  Text = 4
}

/**
 * Part formats supported by CSV-MP
 */
export enum PartFormat {
  CsvDefault = 'csv/default',
  ImagePng = 'image/png',
  ImageJpeg = 'image/jpeg',
  ApplicationJson = 'application/json',
  TextPlain = 'text/plain',
  ApplicationPdf = 'application/pdf'
}

/**
 * Manifest entry representing a part in the CSV-MP file
 */
export interface ManifestEntry {
  index: number;
  type: string;
  description?: string;
  count: number;
  format: string;
  author?: string;
  version: string;
  hash?: string;
}

/**
 * Column definition in a table header
 */
export interface ColumnDef {
  name: string;
  baseType: BaseType;
  collectionType: CollectionType;
  tupleTypes?: BaseType[]; // For tuple collection type
}

/**
 * Parsed table from CSV-MP
 */
export interface Table {
  name: string;
  columns: ColumnDef[];
  rows: any[][];
  manifestEntry: ManifestEntry;
}

/**
 * Binary part from CSV-MP
 */
export interface BinaryPart {
  name: string;
  index: number;
  mimeType: string;
  size: number;
  data: Buffer;
  manifestEntry: ManifestEntry;
}

/**
 * Text part from CSV-MP
 */
export interface TextPart {
  name: string;
  index: number;
  mimeType: string;
  content: string;
  manifestEntry: ManifestEntry;
}

/**
 * Validation configuration for different scenarios
 */
export interface ValidationConfig {
  validateOnWrite: boolean;
  validateOnRead: boolean;
  verifyHash: boolean;
  throwOnError: boolean;
}

/**
 * Default validation configurations for different use cases
 */
export const ValidationScenarios: Record<string, ValidationConfig> = {
  default: {
    validateOnWrite: true,
    validateOnRead: true,
    verifyHash: false,
    throwOnError: true
  },
  gameSave: {
    validateOnWrite: true,
    validateOnRead: false,
    verifyHash: false,
    throwOnError: false
  },
  iotTelemetry: {
    validateOnWrite: false,
    validateOnRead: true,
    verifyHash: false,
    throwOnError: false
  },
  dataPipeline: {
    validateOnWrite: true,
    validateOnRead: false,
    verifyHash: true,
    throwOnError: true
  },
  securityMax: {
    validateOnWrite: true,
    validateOnRead: true,
    verifyHash: true,
    throwOnError: true
  }
};

/**
 * Exception types for CSV-MP errors
 */
export class CsvMpException extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CsvMpException';
  }
}

export class ReferenceException extends CsvMpException {
  constructor(message: string) {
    super(message);
    this.name = 'ReferenceException';
  }
}

export class IndexException extends CsvMpException {
  constructor(message: string) {
    super(message);
    this.name = 'IndexException';
  }
}

export class TypeException extends CsvMpException {
  constructor(message: string) {
    super(message);
    this.name = 'TypeException';
  }
}

export class IntegrityException extends CsvMpException {
  constructor(message: string) {
    super(message);
    this.name = 'IntegrityException';
  }
}

export class FormatException extends CsvMpException {
  constructor(message: string) {
    super(message);
    this.name = 'FormatException';
  }
}
