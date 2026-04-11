// CSV-MP C# Implementation
// Version: 0.2.0-alpha
// License: CC0 1.0 (Public Domain)

namespace CsvMp.Types;

/// <summary>
/// Base exception for CSV-MP errors
/// </summary>
public class CsvMpException : Exception
{
    public CsvMpException(string message) : base(message) { }
}

/// <summary>
/// Reference validation error
/// </summary>
public class ReferenceException : CsvMpException
{
    public ReferenceException(string message) : base(message) { }
}

/// <summary>
/// Index sequence error
/// </summary>
public class IndexException : CsvMpException
{
    public IndexException(string message) : base(message) { }
}

/// <summary>
/// Type validation error
/// </summary>
public class TypeException : CsvMpException
{
    public TypeException(string message) : base(message) { }
}

/// <summary>
/// Data integrity error
/// </summary>
public class IntegrityException : CsvMpException
{
    public IntegrityException(string message) : base(message) { }
}

/// <summary>
/// Format parsing error
/// </summary>
public class FormatException : CsvMpException
{
    public FormatException(string message) : base(message) { }
}
