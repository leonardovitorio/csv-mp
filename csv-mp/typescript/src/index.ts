/**
 * CSV-MP TypeScript Package
 * Version: 0.8.0-alpha
 */

export {
  BaseType,
  CollectionType,
  PartFormat,
  type ManifestEntry,
  type ColumnDef,
  type Table,
  type BinaryPart,
  type TextPart,
  type ValidationConfig,
  ValidationScenarios,
  CsvMpException,
  ReferenceException,
  IndexException,
  TypeException,
  IntegrityException,
  FormatException
} from './types';

export {
  CsvMpParser,
  parse,
  serialize,
  // Simple API
  deserialize,
  toCsvMp,
  fromCsvMp,
  readCsvMp,
  writeCsvMp
} from './parser';
