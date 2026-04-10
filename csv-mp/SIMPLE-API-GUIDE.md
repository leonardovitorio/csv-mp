# CSV-MP Simple API Guide

## Overview

CSV-MP provides a simple, high-level API for serialization and deserialization in TypeScript, Python, and C#. This guide shows you how to quickly start using CSV-MP without dealing with low-level details.

## API Functions

All three implementations provide the same set of simple API functions:

| Function | Description |
|----------|-------------|
| `deserialize()` / `from_csv_mp()` / `FromCsvMp()` | Convert CSV-MP content to plain objects |
| `toCsvMp()` / `to_csv_mp()` / `ToCsvMp()` | Convert plain objects to CSV-MP format |
| `readCsvMp()` / `read_csv_mp()` / `ReadCsvMp()` | Read CSV-MP from file |
| `writeCsvMp()` / `write_csv_mp()` / `WriteCsvMp()` | Write CSV-MP to file |

---

## TypeScript

### Installation

```bash
npm install csv-mp
```

### Basic Usage

```typescript
import { toCsvMp, deserialize } from 'csv-mp';

// Serialize objects to CSV-MP
const data = {
  User: [
    { id: 1, name: 'Alice', email: 'alice@example.com' },
    { id: 2, name: 'Bob', email: 'bob@example.com' }
  ],
  Order: [
    { orderId: 101, userId: 1, product: 'Laptop' },
    { orderId: 102, userId: 2, product: 'Mouse' }
  ]
};

const csvMpContent = toCsvMp(data, {
  author: 'my-app',
  version: '1.0'
});

// Deserialize CSV-MP to objects
const parsed = deserialize<{ User: any[], Order: any[] }>(csvMpContent);
console.log(parsed.User); // [{ id: 1, name: 'Alice', ... }, ...]
```

### File I/O

```typescript
import { writeCsvMp, readCsvMp } from 'csv-mp';

// Write to file
await writeCsvMp('data.csv.mp', data, {
  author: 'my-app',
  version: '1.0'
});

// Read from file
const loaded = await readCsvMp('data.csv.mp');
```

---

## Python

### Installation

```bash
pip install csv-mp
```

### Basic Usage

```python
from csv_mp import to_csv_mp, deserialize

# Serialize objects to CSV-MP
data = {
    'User': [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'}
    ],
    'Order': [
        {'orderId': 101, 'userId': 1, 'product': 'Laptop'},
        {'orderId': 102, 'userId': 2, 'product': 'Mouse'}
    ]
}

csv_mp_content = to_csv_mp(data, {
    'author': 'my-app',
    'version': '1.0'
})

# Deserialize CSV-MP to objects
parsed = deserialize(csv_mp_content)
print(parsed['User'])  # [{'id': 1, 'name': 'Alice', ...}, ...]
```

### File I/O

```python
from csv_mp import write_csv_mp, read_csv_mp

# Write to file
write_csv_mp('data.csv.mp', data, {
    'author': 'my-app',
    'version': '1.0'
})

# Read from file
loaded = read_csv_mp('data.csv.mp')
```

---

## C#

### Installation

```bash
dotnet add package CsvMp
```

### Basic Usage

```csharp
using CsvMp.Parser;

// Serialize objects to CSV-MP
var data = new Dictionary<string, object>
{
    ["User"] = new List<object>
    {
        new Dictionary<string, object> { ["id"] = 1, ["name"] = "Alice", ["email"] = "alice@example.com" },
        new Dictionary<string, object> { ["id"] = 2, ["name"] = "Bob", ["email"] = "bob@example.com" }
    },
    ["Order"] = new List<object>
    {
        new Dictionary<string, object> { ["orderId"] = 101, ["userId"] = 1, ["product"] = "Laptop" },
        new Dictionary<string, object> { ["orderId"] = 102, ["userId"] = 2, ["product"] = "Mouse" }
    }
};

var csvMpContent = CsvMp.ToCsvMp(data, author: "my-app", version: "1.0");

// Deserialize CSV-MP to objects
var parsed = CsvMp.Deserialize(csvMpContent);
Console.WriteLine(parsed["User"]); // List of user dictionaries
```

### File I/O

```csharp
using CsvMp.Parser;

// Write to file
CsvMp.WriteCsvMp("data.csv.mp", data, author: "my-app", version: "1.0");

// Read from file
var loaded = CsvMp.ReadCsvMp("data.csv.mp");
```

---

## Type Inference

The simple API automatically infers column types from your data:

| JavaScript/Python Type | CSV-MP Type |
|------------------------|-------------|
| `string` | `string` |
| `number` (integer) | `int` |
| `number` (float) | `number` |
| `boolean` | `boolean` |
| `string` starting with `@` | `Reference` |
| `object`/`dict` | `object` (JSON) |

---

## Options

### Serialization Options

| Option | Default | Description |
|--------|---------|-------------|
| `author` | `'csv-mp'` | Author name for manifesto |
| `version` | `'0.8'` | Schema version |
| `description` | `'{Type} data'` | Part description |

### Validation Configuration

For advanced validation options, use the low-level API with `ValidationConfig`:

```typescript
import { CsvMpParser, ValidationScenarios } from 'csv-mp';

const parser = new CsvMpParser(ValidationScenarios.SECURITY_MAX);
const result = parser.parse(content);
```

---

## Examples

See the `examples/` directory for complete working examples in each language:

- **TypeScript**: `examples/simple-api.ts`
- **Python**: `examples/simple_api.py`
- **C#**: `examples/SimpleApiExamples.cs`

---

## License

CSV-MP is released under CC0 1.0 (Public Domain).
