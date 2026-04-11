# CSV-MP: Complete Data Structuring Documentation
**Version:** 0.2.0-alpha  
**Status:** Official Specification  
**License:** CC0 1.0 (Public Domain)

---

## TABLE OF CONTENTS
1. Overview
2. File Structure
3. Manifesto
4. Tables
5. Binary Content
6. Text Content
7. Type System
8. Reference System
9. Validation
10. Complete Examples

---

## 1. OVERVIEW

### 1.1 What is CSV-MP

CSV-MP (CSV MultiPart Protocol) is a data serialization protocol that combines:
- Human readability (text format, opens in Excel)
- Multiple tables in a single file
- Native references between tables
- Explicit typing in headers
- Binary assets (images, PDFs) in the same file
- Integrated schema and integrity validation

### 1.2 Design Philosophy

"Human readability with binary performance"

CSV-MP is designed with organic correlation between components:
- Same format for storage and network
- Same parser for all file types
- Same validation logic everywhere

### 1.3 Main Use Cases

| Use Case        | Why CSV-MP                                      |
|-----------------|------------------------------------------------|
| Game Saves      | Data + assets + validation in 1 file           |
| IoT Edge        | Native validation + compact size               |
| Data Pipelines  | Schema validation between stages               |
| Mobile Offline  | Efficient sync + local storage                 |
| Enterprise Sync | Audit trail + verifiable integrity             |

---

## 2. FILE STRUCTURE

### 2.1 Macro View

```
FILE.csv.mp
├── [MANIFESTO]
│   &|type|description|count|format|author|version|hash
│   0|User|User data|100|csv/default|dev01|1.0|abc...
│   1|Order|Order data|500|csv/default|dev01|1.0|def...
│   2|Avatar|User avatar|1|image/png|dev01|1.0|ghi...
├── [PART 0: User - Table]
│   &:id:int,name:string,email:string,avatar:Reference
│   0,1,Alice,alice@email.com,@Avatar.0
│   1,2,Bob,bob@email.com,@Avatar.0
├── [PART 1: Order - Table]
│   &:id:int,user:Reference,product:string,quantity:int
│   0,@User.0,Laptop,1
│   1,@User.0,Mouse,2
└── [PART 2: Avatar - Binary]
    [PART:Avatar.0|image/png|524288]
    <binary data>
    [END:Avatar.0]
```

### 2.2 File Components

| Component       | Required | Description                              |
|-----------------|----------|------------------------------------------|
| Manifesto       | Yes      | Lists all parts in the file              |
| Parts           | Yes (≥1) | Tables, binaries, or text                |
| Blank line      | Yes      | Separates manifesto from parts           |
| Encoding        | Yes      | UTF-8 (mandatory)                        |
| Line ending     | Yes      | \n (Unix-style)                          |

### 2.3 Separators

| Character | Name           | Function                      | Context             |
|-----------|----------------|-------------------------------|---------------------|
| &\|       | Manifest Header| Starts manifesto header       | Manifesto           |
| &:        | Table Header   | Starts table header           | Tables              |
| ,         | COMMA          | Separates fields              | CSV Data            |
| \n        | NEWLINE        | Separates records             | Entire file         |
| "         | QUOTE          | Escapes special characters    | CSV Data            |
| #         | HASH           | Starts comment                | Anywhere            |
| @         | REFERENCE      | Starts reference              | Values              |
| .         | REFERENCE_SEP  | Separates name and index      | References          |
| [         | BRACKET        | Starts binary/text part       | Special parts       |

---

## 3. MANIFESTO

### 3.1 Structure

```
# Comments are optional (start with #)
# CSV-MP v0.2 Manifesto
# Generated: 2024-01-20T10:30:00Z

&|type|description|count|format|author|version|hash
0|User|User data|100|csv/default|dev01|1.0|abc123...
1|Order|Order data|500|csv/default|dev01|1.0|def456...
2|Avatar|User avatar|1|image/png|dev01|1.0|ghi789...
```

### 3.2 Manifesto Columns

| Column      | Type   | Required | Description                              |
|-------------|--------|----------|------------------------------------------|
| Index       | int    | Yes      | Part index (0-based, sequential)         |
| type        | string | Yes      | Type name (User, Order, Avatar)          |
| description | string | No       | Human-readable description of the part   |
| count       | int    | Yes      | Number of rows (table) or bytes          |
| format      | string | Yes      | Format (csv/default, image/png)          |
| author      | string | No       | Author/creator of the part               |
| version     | string | Yes      | Schema version (1.0, 2.0, etc.)          |
| hash        | string | No       | SHA-256 hash of the part (empty if not)  |

### 3.3 Validation Rules

- `header_must_start_with`: "&|"
- `index_must_be`: "0-based, sequential, no gaps"
- `first_index_must_be`: 0
- `type_must_be_unique`: "within same file"
- `count_must_match`: "actual row/byte count"
- `format_must_be`: "csv/default, image/png, text/json, etc."
- `hash_if_present_must_be`: "SHA-256 hex string (64 chars)"

### 3.4 Complete Example

```
# CSV-MP v0.2 Manifesto
# Generated: 2024-01-20T10:30:00Z
# Author: csv-mp-team
# License: CC0 1.0

&|type|description|count|format|author|version|hash
0|User|User data|3|csv/default|csv-mp-team|0.2|
1|Order|Purchase orders|5|csv/default|csv-mp-team|0.2|
2|Avatar|User avatar|1|image/png|csv-mp-team|0.2|
3|Config|System settings|1|application/json|csv-mp-team|0.2|
```

---

## 4. TABLES

### 4.1 Structure

```
# Header starts with &: (schema + types)
&:id:int,name:string,email:string,age:int,active:boolean

# Data: first column is explicit index (0-based)
0,1,Alice,alice@email.com,30,true
1,2,Bob,bob@email.com,25,false
2,3,Carlos,carlos@email.com,35,true
```

### 4.2 Header Elements

| Element        | Format | Description                     | Example           |
|----------------|--------|---------------------------------|-------------------|
| Prefix         | &:     | Marks line as header            | &:                |
| Column name    | string | Column identifier               | id, name          |
| Separator      | :      | Separates name from type        | :                 |
| Type           | string | Data type (BaseType)            | int, string       |
| Collection     | [] or []| Array or tuple (optional)      | string[], [n,n]   |

### 4.3 Explicit Index

| Rule           | Description                           | Example           |
|----------------|---------------------------------------|-------------------|
| First column   | Index is always the first column      | 0,1,Alice,...     |
| 0-based        | First row = index 0                   | 0,...             |
| Sequential     | No gaps (0, 1, 2, 3...)               | 0,1,2,3 (valid)   |
| Unique         | No duplicates                         | 0,0,1 (invalid)   |
| Reference      | Used in @Table.Index                  | @User.0           |

### 4.4 Column Types (BaseTypes)

| Type       | Syntax     | CSV Example            | Validation                     |
|------------|------------|------------------------|--------------------------------|
| String     | :string    | Alice or "Hello, World"| Quoted if contains comma/quote |
| Number     | :number    | 3.14159                | Unquoted, decimal point        |
| Int        | :int       | 42                     | Unquoted, 32-bit               |
| Long       | :long      | 9223372036854775807    | Unquoted, 64-bit               |
| Boolean    | :boolean   | true or false          | Lowercase, unquoted            |
| Date       | :date      | "2024-01-20"           | Quoted, yyyy-MM-dd             |
| DateTime   | :datetime  | "2024-01-20T10:30:00Z" | Quoted, ISO 8601               |
| Object     | :object    | "{\"key\":\"value\"}"  | Quoted JSON string             |
| Reference  | :Reference | @Avatar.0              | @PartName.Index, 0-based       |

### 4.5 Collection Types

| Type   | Syntax | Header Example       | Value Example      |
|--------|--------|----------------------|--------------------|
| Single | T      | name:string          | Alice              |
| Array  | T[]    | tags:string[]        | "tag1,tag2"        |
| Tuple  | [T1,T2]| coord:[number,number]| "150.5,200.3"      |

### 4.6 Validation Rules

- `header_must_start_with`: "&:"
- `index_must_be_first_column`: true
- `index_must_be`: "0-based, sequential, unique"
- `column_count_must_match`: "header defines N columns, data must have N+1"
- `types_must_match`: "values must match declared types"
- `references_must_be_valid`: "@Table.Index must exist"
- `escaping_must_follow`: "RFC 4180 rules"

### 4.7 Complete Example

```
# Users Table
&:id:int,name:string,email:string,age:int,active:boolean,avatar:Reference
0,1,Alice Silva,alice@email.com,30,true,@Avatar.0
1,2,Bob Santos,bob@email.com,25,false,@Avatar.0
2,3,"Carlos, Jr",carlos@email.com,35,true,@Avatar.0

# Validation:
# ✅ Index: 0, 1, 2 (sequential, 0-based)
# ✅ Types: int, string, string, int, boolean, Reference
# ✅ References: @Avatar.0 (must exist in manifesto)
# ✅ Escape: "Carlos, Jr" (comma in value → quotes)
```

---

## 5. BINARY CONTENT

### 5.1 Structure

```
[PART:Avatar.0|image/png|524288]
<binary data - raw bytes, NOT base64>
[END:Avatar.0]
```

### 5.2 Components

| Element       | Format                   | Description                    |
|---------------|--------------------------|--------------------------------|
| Start marker  | [PART:Name.Index\|mime\|size]| Start of binary part         |
| Name          | string                   | Part name (Avatar)             |
| Index         | int                      | Part index (0-based)           |
| MIME type     | string                   | MIME type (image/png)          |
| Size          | int                      | Size in bytes                  |
| Data          | bytes                    | Raw binary data                |
| End marker    | [END:Name.Index]         | End of binary part             |

### 5.3 Validation Rules

- `start_marker_must_match`: "[PART:Name.Index\|mime\|size]"
- `end_marker_must_match`: "[END:Name.Index]"
- `name_must_match_manifesto`: true
- `index_must_be`: "0-based"
- `size_must_match`: "actual byte count"
- `mime_must_be_valid`: "standard MIME type"
- `data_must_be`: "raw bytes (NOT base64 encoded)"

### 5.4 Complete Example

```
[PART:Avatar.0|image/png|524288]
<524288 bytes of raw PNG data>
[END:Avatar.0]

[PART:Document.0|application/pdf|1048576]
<1048576 bytes of raw PDF data>
[END:Document.0]
```

---

## 6. TEXT CONTENT

### 6.1 Structure

```
[TEXT:Config.0|application/json]
{"theme":"dark","notifications":true}
[END:Config.0]
```

### 6.2 Components

| Element       | Format                | Description                    |
|---------------|-----------------------|--------------------------------|
| Start marker  | [TEXT:Name.Index\|mime]| Start of text part            |
| Name          | string                | Part name (Config)             |
| Index         | int                   | Part index (0-based)           |
| MIME type     | string                | MIME type (application/json)   |
| Data          | string                | Text data (UTF-8)              |
| End marker    | [END:Name.Index]      | End of text part               |

### 6.3 Validation Rules

- `start_marker_must_match`: "[TEXT:Name.Index\|mime]"
- `end_marker_must_match`: "[END:Name.Index]"
- `name_must_match_manifesto`: true
- `index_must_be`: "0-based"
- `mime_must_be_valid`: "standard MIME type"
- `data_must_be`: "UTF-8 encoded text"

### 6.4 Complete Example

```
[TEXT:Config.0|application/json]
{
  "theme": "dark",
  "notifications": {
    "email": true,
    "push": false
  },
  "language": "pt-BR"
}
[END:Config.0]

[TEXT:Log.0|text/plain]
2024-01-20T10:30:00Z - System started
2024-01-20T10:30:01Z - User logged in
[END:Log.0]
```

---

## 7. TYPE SYSTEM

### 7.1 BaseTypes (WHAT)

Defines what the data is.

| Name      | Value | Description           | CSV Example         | C# Type    | TS Type | Python Type |
|-----------|-------|-----------------------|---------------------|------------|---------|-------------|
| Any       | 0     | Not specified         | any                 | object     | any     | Any         |
| String    | 1     | UTF-8 text            | Alice               | string     | string  | str         |
| Number    | 2     | Double (64-bit float) | 3.14159             | double     | number  | float       |
| Long      | 3     | Int64                 | 9223372036854775807 | long       | number  | int         |
| Int       | 4     | Int32                 | 2147483647          | int        | number  | int         |
| Boolean   | 5     | True/false            | true                | bool       | boolean | bool        |
| Date      | 6     | Date (yyyy-MM-dd)     | "2024-01-20"        | DateTime   | Date    | date        |
| DateTime  | 7     | DateTime (ISO 8601)   | "2024-01-20T10:30Z" | DateTime   | Date    | datetime    |
| Object    | 8     | JSON object           | "{\"key\":\"value\"}"| object    | Record  | dict        |
| Reference | 9     | Reference to part     | @Avatar.0           | string     | string  | str         |

### 7.2 CollectionTypes (HOW)

Defines how the data is organized.

| Name   | Value | Description           | Syntax    | Example            |
|--------|-------|-----------------------|-----------|--------------------|
| Single | 0     | Single value          | T         | name:string        |
| Array  | 1     | Array of values       | T[]       | tags:string[]      |
| Tuple  | 2     | Fixed-size tuple      | [T1,T2]   | coord:[number,n]   |
| File   | 3     | Binary file           | Reference | avatar:Reference   |
| Text   | 4     | Formatted text        | Text      | config:Text        |

### 7.3 Type Validation Rules

**STRING:**
- `may_be_quoted`: if contains comma, quote, or newline
- `quote_escape`: "" for literal quote
- `encoding`: UTF-8

**NUMBER:**
- `must_not_be_quoted`: true
- `decimal_separator`: .
- `range`: IEEE 754 double precision

**INT:**
- `must_not_be_quoted`: true
- `range`: -2147483648 to 2147483647

**LONG:**
- `must_not_be_quoted`: true
- `range`: -9223372036854775808 to 9223372036854775807

**BOOLEAN:**
- `must_be_lowercase`: true or false
- `must_not_be_quoted`: true

**DATE:**
- `must_be_quoted`: true
- `format`: yyyy-MM-dd
- `example`: "2024-01-20"

**DATETIME:**
- `must_be_quoted`: true
- `format`: ISO 8601
- `example`: "2024-01-20T10:30:00Z"

**OBJECT:**
- `must_be_quoted`: true
- `must_be_valid_json`: true
- `example`: "{\"key\":\"value\"}"

**REFERENCE:**
- `must_start_with`: @
- `format`: @PartName.Index
- `index_must_be`: 0-based
- `must_not_be_quoted`: true

---

## 8. REFERENCE SYSTEM

### 8.1 Reference Types

CSV-MP uses a single generic type `:Reference` that can reference:

| Target  | Example    | Description                          |
|---------|------------|--------------------------------------|
| Table   | @User.0    | First row of User table              |
| Binary  | @Avatar.0  | First Avatar part (image)            |
| Text    | @Config.0  | First Config part (JSON)             |

### 8.2 Reference Syntax

```
@PartName.Index
│   │       │
│   │       └─ 0-based index (row for tables, part for binary/text)
│   └───────── Part name (from manifesto)
└───────────── Reference marker
```

### 8.3 Bidirectional Validation

**FORWARD VALIDATION:**
- **description**: Reference must point to a valid part
- **rule**: @PartName.Index must exist in manifesto
- **exception**: "Reference '@{PartName}.{Index}' not found"

**BACKWARD VALIDATION:**
- **description**: Reference column must be referenced
- **rule**: Table with :Reference columns must be referenced by another table
- **exception**: "Column reference in table '{TableName}' not found"

### 8.4 Validation Example

```
# ✅ VALID: Bidirectional reference
&|type|description|count|format|author|version|hash
0|User|User data|2|csv/default|dev01|1.0|
1|Order|Order data|3|csv/default|dev01|1.0|

&:id:int,name:string,avatar:Reference
0,1,Alice,@Avatar.0
1,2,Bob,@Avatar.0

&:id:int,user:Reference,product:string
0,@User.0,Laptop
1,@User.0,Mouse
2,@User.1,Keyboard

# Forward: @User.0 exists in User table ✅
# Backward: User is referenced by Order.user ✅

# ❌ INVALID: Reference column is not used
&|type|description|count|format|author|version|hash
0|User|User data|2|csv/default|dev01|1.0|
1|Order|Order data|3|csv/default|dev01|1.0|

&:id:int,name:string,avatar:Reference
0,1,Alice,@Avatar.0
1,2,Bob,@Avatar.0

&:id:int,product:string,quantity:int
0,Laptop,1
1,Mouse,2
2,Keyboard,3

# Forward: @Avatar.0 must exist ✅
# Backward: User is NOT referenced by Order ❌
# Exception: "Column reference in table 'User' not found"
```

---

## 9. VALIDATION

### 9.1 Validation Types

| Type                  | When      | What It Validates       | Configurable |
|-----------------------|-----------|-------------------------|--------------|
| Schema                | Write/Read| Types, columns, structure| Yes         |
| Reference (Forward)   | Read      | @Part.Index exists      | No           |
| Reference (Backward)  | Read      | Table is referenced     | No           |
| Index Sequence        | Read      | Indices 0,1,2,...       | No           |
| SHA-256 Hash          | Read      | Part integrity          | Yes (opt-in) |

### 9.2 Validation Configuration

**DEFAULTS:**
- `validate_on_write`: true
- `validate_on_read`: true
- `verify_hash`: false
- `throw_on_validation_error`: true

**SCENARIOS:**

**game_save:**
- `validate_on_write`: true
- `validate_on_read`: false
- `verify_hash`: false

**iot_telemetry:**
- `validate_on_write`: false
- `validate_on_read`: true
- `verify_hash`: false

**data_pipeline:**
- `validate_on_write`: true
- `validate_on_read`: false
- `verify_hash`: true

**security_max:**
- `validate_on_write`: true
- `validate_on_read`: true
- `verify_hash`: true
- `throw_on_validation_error`: true

### 9.3 Exception Messages

| Exception          | Message                                      | When                    |
|--------------------|----------------------------------------------|-------------------------|
| ReferenceException | Reference '@{Part}.{Index}' not found        | Forward validation fails|
| ReferenceException | Column reference in table '{Table}' not found| Backward validation     |
| IndexException     | Index sequence error: expected {N}, got {M}  | Non-sequential index    |
| TypeException      | Invalid value for column '{Column}': {Error} | Invalid type            |
| IntegrityException | Hash mismatch for part '{Part}'              | Hash verification fails |
| FormatException    | Invalid header format: expected &: prefix    | Invalid header          |

---

## 10. COMPLETE EXAMPLES

### 10.1 Example: Basic Users

```
# CSV-MP v0.2 Manifesto
&|type|description|count|format|author|version|hash
0|User|User data|3|csv/default|csv-mp-team|0.2|

&:id:int,name:string,email:string,age:int,active:boolean
0,1,Alice Silva,alice@email.com,30,true
1,2,Bob Santos,bob@email.com,25,false
2,3,"Carlos, Jr",carlos@email.com,35,true
```

### 10.2 Example: Game Save

```
# CSV-MP v0.2 Manifesto
&|type|description|count|format|author|version|hash
0|Player|Player character|1|csv/default|game-dev|0.2|
1|Inventory|Inventory items|5|csv/default|game-dev|0.2|
2|Avatar|Character avatar|1|image/png|game-dev|0.2|

&:id:int,name:string,level:int,experience:number,gold:int,avatar:Reference
0,1,HeroKnight,42,125000.5,50000,@Avatar.0

&:id:int,player:Reference,item_id:int,item_name:string,quantity:int,equipped:boolean
0,101,@Player.0,50,Excalibur,1,true
1,102,@Player.0,75,Health Potion,3,false
2,103,@Player.0,80,Shield of Valor,1,true
3,104,@Player.0,90,Dragon Armor,1,true
4,105,@Player.0,100,Map of Secrets,1,false

[PART:Avatar.0|image/png|524288]
<binary data>
[END:Avatar.0]
```

### 10.3 Example: IoT Telemetry

```
# CSV-MP v0.2 Manifesto
&|type|description|count|format|author|version|hash
0|Vehicle|Vehicle data|1|csv/default|iot-system|0.2|
1|SensorReading|Sensor readings|5|csv/default|iot-system|0.2|

&:vin:string,model:string,last_seen:datetime,battery_level:number
0,ABC123,Ford Transit,2024-01-20T10:30:00Z,85.5

&:id:int,vehicle:Reference,sensor_type:string,value:number,unit:string,timestamp:datetime
0,101,@Vehicle.0,gps_lat,-23.5505,degrees,2024-01-20T10:30:00Z
1,102,@Vehicle.0,gps_lon,-46.6333,degrees,2024-01-20T10:30:00Z
2,103,@Vehicle.0,fuel_level,75.5,percent,2024-01-20T10:30:00Z
3,104,@Vehicle.0,engine_temp,85,celsius,2024-01-20T10:30:00Z
4,105,@Vehicle.0,speed,60,km/h,2024-01-20T10:30:00Z
```

### 10.4 Example: Type Validation

```
# CSV-MP v0.2 Manifesto
&|type|description|count|format|author|version|hash
0|TypeExamples|All BaseTypes|5|csv/default|csv-mp-team|0.2|

&:id:int,string_val:string,number_val:number,long_val:long,int_val:int,bool_val:boolean,date_val:date,datetime_val:datetime,ref:Reference
0,1,Hello World,3.14159,9223372036854775807,2147483647,true,"2024-01-20","2024-01-20T10:30:00Z",@Binary.0
1,2,"Hello, World",123.45,-9223372036854775808,-2147483648,false,"2024-06-15","2024-06-15T14:45:30Z",@Binary.1
2,3,"Say ""Hi""",0.0,0,0,true,"1970-01-01","1970-01-01T00:00:00Z",
3,4,"Line1\nLine2",1.7976931348623157e+308,9223372036854775806,2147483646,false,"2099-12-31","2099-12-31T23:59:59Z",@Binary.0
4,5,,,-9223372036854775807,-2147483647,true,,
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Manifesto parser (&| header)
- [ ] Table parser (&: header + explicit index)
- [ ] Binary parser ([PART:...]/[END:...])
- [ ] Text parser ([TEXT:...]/[END:...])
- [ ] BaseType validation
- [ ] Collection validation (Single, Array, Tuple)
- [ ] Reference validation (forward + backward)
- [ ] Index sequence validation
- [ ] SHA-256 hash validation (opt-in)
- [ ] CSV-MP serializer
- [ ] CSV-MP deserializer
- [ ] Scenario-based configuration (game, IoT, pipeline, etc.)

---

**Document Version:** 0.2.0-alpha  
**License:** CC0 1.0 (Public Domain)  
**Contact:** csv-mp@example.com  
**GitHub:** https://github.com/csv-mp/csv-mp
