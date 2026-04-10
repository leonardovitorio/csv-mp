// CSV-MP C# Implementation
// Version: 0.8.0-alpha
// License: CC0 1.0 (Public Domain)

namespace CsvMp.Types;

/// <summary>
/// Manifest entry representing a part in the CSV-MP file
/// </summary>
public class ManifestEntry
{
    public int Index { get; set; }
    public string Type { get; set; } = string.Empty;
    public string? Description { get; set; }
    public int Count { get; set; }
    public string Format { get; set; } = string.Empty;
    public string? Author { get; set; }
    public string Version { get; set; } = string.Empty;
    public string? Hash { get; set; }
}

/// <summary>
/// Column definition in a table header
/// </summary>
public class ColumnDef
{
    public string Name { get; set; } = string.Empty;
    public BaseType BaseType { get; set; }
    public CollectionType CollectionType { get; set; }
    public List<BaseType>? TupleTypes { get; set; }
}

/// <summary>
/// Parsed table from CSV-MP
/// </summary>
public class Table
{
    public string Name { get; set; } = string.Empty;
    public List<ColumnDef> Columns { get; set; } = new();
    public List<List<object?>> Rows { get; set; } = new();
    public ManifestEntry ManifestEntry { get; set; } = new();
}

/// <summary>
/// Binary part from CSV-MP
/// </summary>
public class BinaryPart
{
    public string Name { get; set; } = string.Empty;
    public int Index { get; set; }
    public string MimeType { get; set; } = string.Empty;
    public int Size { get; set; }
    public byte[] Data { get; set; } = Array.Empty<byte>();
    public ManifestEntry ManifestEntry { get; set; } = new();
}

/// <summary>
/// Text part from CSV-MP
/// </summary>
public class TextPart
{
    public string Name { get; set; } = string.Empty;
    public int Index { get; set; }
    public string MimeType { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public ManifestEntry ManifestEntry { get; set; } = new();
}

/// <summary>
/// Validation configuration for different scenarios
/// </summary>
public class ValidationConfig
{
    public bool ValidateOnWrite { get; set; } = true;
    public bool ValidateOnRead { get; set; } = true;
    public bool VerifyHash { get; set; } = false;
    public bool ThrowOnError { get; set; } = true;
}

/// <summary>
/// Default validation configurations for different use cases
/// </summary>
public static class ValidationScenarios
{
    public static ValidationConfig Default => new()
    {
        ValidateOnWrite = true,
        ValidateOnRead = true,
        VerifyHash = false,
        ThrowOnError = true
    };

    public static ValidationConfig GameSave => new()
    {
        ValidateOnWrite = true,
        ValidateOnRead = false,
        VerifyHash = false,
        ThrowOnError = false
    };

    public static ValidationConfig IotTelemetry => new()
    {
        ValidateOnWrite = false,
        ValidateOnRead = true,
        VerifyHash = false,
        ThrowOnError = false
    };

    public static ValidationConfig DataPipeline => new()
    {
        ValidateOnWrite = true,
        ValidateOnRead = false,
        VerifyHash = true,
        ThrowOnError = true
    };

    public static ValidationConfig SecurityMax => new()
    {
        ValidateOnWrite = true,
        ValidateOnRead = true,
        VerifyHash = true,
        ThrowOnError = true
    };
}
