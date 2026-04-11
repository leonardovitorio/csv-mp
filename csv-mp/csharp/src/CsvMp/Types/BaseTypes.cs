// CSV-MP C# Implementation
// Version: 0.2.0-alpha
// License: CC0 1.0 (Public Domain)

namespace CsvMp.Types;

/// <summary>
/// BaseTypes - Define o que o dado é
/// </summary>
public enum BaseType
{
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

/// <summary>
/// CollectionTypes - Define como o dado é organizado
/// </summary>
public enum CollectionType
{
    Single = 0,
    Array = 1,
    Tuple = 2,
    File = 3,
    Text = 4
}

/// <summary>
/// Part formats supported by CSV-MP
/// </summary>
public static class PartFormat
{
    public const string CsvDefault = "csv/default";
    public const string ImagePng = "image/png";
    public const string ImageJpeg = "image/jpeg";
    public const string ApplicationJson = "application/json";
    public const string TextPlain = "text/plain";
    public const string ApplicationPdf = "application/pdf";
}
