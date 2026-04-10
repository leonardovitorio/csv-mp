// CSV-MP C# Implementation - Parser and Serializer
// Version: 0.8.0-alpha
// License: CC0 1.0 (Public Domain)

using System.Text;
using System.Text.RegularExpressions;
using System.Security.Cryptography;
using CsvMp.Types;

namespace CsvMp.Parser;

public class CsvMpParser
{
    private readonly ValidationConfig _config;
    public CsvMpParser(ValidationConfig? config = null) => _config = config ?? ValidationScenarios.Default;

    public ParseResult Parse(string content)
    {
        var lines = content.Split('\n');
        var lineIndex = 0;
        var (manifest, newIndex) = ParseManifesto(lines, lineIndex);
        lineIndex = newIndex;
        while (lineIndex < lines.Length && lines[lineIndex].Trim() == "") lineIndex++;

        var tables = new List<Table>();
        var binaryParts = new List<BinaryPart>();
        var textParts = new List<TextPart>();

        while (lineIndex < lines.Length)
        {
            var line = lines[lineIndex];
            if (line.StartsWith("&:")) { var r = ParseTable(lines, lineIndex, manifest); tables.Add(r.Table); lineIndex = r.LineIndex; }
            else if (line.StartsWith("[PART:")) { var r = ParseBinaryPart(lines, lineIndex, manifest); binaryParts.Add(r.Part); lineIndex = r.LineIndex; }
            else if (line.StartsWith("[TEXT:")) { var r = ParseTextPart(lines, lineIndex, manifest); textParts.Add(r.Part); lineIndex = r.LineIndex; }
            else lineIndex++;
        }
        if (_config.ValidateOnRead) ValidateReferences(manifest, tables);
        return new ParseResult { Manifest = manifest, Tables = tables, BinaryParts = binaryParts, TextParts = textParts };
    }

    private (List<ManifestEntry>, int) ParseManifesto(string[] lines, int si)
    {
        var manifest = new List<ManifestEntry>();
        var li = si;
        while (li < lines.Length) { var l = lines[li].Trim(); if (l.StartsWith("#") || l == "") { li++; continue; } if (l.StartsWith("&|")) break; throw new FormatException($"Invalid manifesto at line {li + 1}"); }
        if (li >= lines.Length) throw new FormatException("Manifesto header not found");
        var headers = lines[li].Substring(2).Split('|');
        if (headers.Length < 7) throw new FormatException("Invalid manifesto header");
        li++; var ei = 0;
        while (li < lines.Length)
        {
            var l = lines[li].Trim();
            if (l == "") { li++; break; }
            if (l.StartsWith("#")) { li++; continue; }
            var cols = l.Split('|');
            if (cols.Length < 7) throw new FormatException($"Invalid entry at line {li + 1}");
            var idx = int.Parse(cols[0]);
            if (idx != ei) throw new IndexException($"Index error: expected {ei}, got {idx}");
            var e = new ManifestEntry { Index = idx, Type = cols[1], Description = string.IsNullOrEmpty(cols[2]) ? null : cols[2], Count = int.Parse(cols[3]), Format = cols[4], Author = string.IsNullOrEmpty(cols[5]) ? null : cols[5], Version = cols[6], Hash = string.IsNullOrEmpty(cols[7]) ? null : cols[7] };
            if (!string.IsNullOrEmpty(e.Hash) && e.Hash.Length != 64) throw new IntegrityException($"Invalid hash for '{e.Type}'");
            manifest.Add(e); ei++; li++;
        }
        return (manifest, li);
    }

    private (Table, int) ParseTable(string[] lines, int si, List<ManifestEntry> manifest)
    {
        var li = si;
        if (!lines[li].StartsWith("&:")) throw new FormatException($"Invalid table header at line {li + 1}");
        var cols = ParseColumnDefinitions(lines[li].Substring(2)); li++;
        var tn = manifest.FirstOrDefault(m => m.Format == PartFormat.CsvDefault)?.Type ?? "Unknown";
        var me = manifest.FirstOrDefault(m => m.Type == tn && m.Format == PartFormat.CsvDefault);
        if (me == null) throw new FormatException($"Manifest entry not found for '{tn}'");
        var rows = new List<List<object?>>(); var eri = 0;
        while (li < lines.Length)
        {
            var l = lines[li].Trim();
            if (l == "" || l.StartsWith("&:") || l.StartsWith("[PART:") || l.StartsWith("[TEXT:")) break;
            if (l.StartsWith("#")) { li++; continue; }
            var vals = ParseCsvLine(l);
            var ri = int.Parse(vals[0]);
            if (ri != eri) throw new IndexException($"Row index error: expected {eri}, got {ri}");
            if (vals.Count != cols.Count + 1) throw new TypeException($"Column count mismatch");
            rows.Add(ConvertRowTypes(vals, cols)); eri++; li++;
        }
        if (_config.ValidateOnRead && rows.Count != me.Count) throw new IntegrityException($"Row count mismatch: expected {me.Count}, got {rows.Count}");
        return (new Table { Name = tn, Columns = cols, Rows = rows, ManifestEntry = me }, li);
    }

    private List<ColumnDef> ParseColumnDefinitions(string hc)
    {
        var cols = new List<ColumnDef>();
        foreach (var p in hc.Split(','))
        {
            var t = p.Trim(); var ci = t.IndexOf(':');
            if (ci == -1) throw new FormatException($"Invalid column: '{t}'");
            var (bt, ct, tt) = ParseTypeSpec(t.Substring(ci + 1));
            cols.Add(new ColumnDef { Name = t.Substring(0, ci), BaseType = bt, CollectionType = ct, TupleTypes = tt });
        }
        return cols;
    }

    private (BaseType, CollectionType, List<BaseType>?) ParseTypeSpec(string ts)
    {
        if (ts.EndsWith("[]")) return (Stb(ts[..^2]), CollectionType.Array, null);
        if (ts.StartsWith("[") && ts.EndsWith("]") && ts.Contains(",")) { var it = ts[1..^1].Split(',').Select(x => Stb(x.Trim())).ToList(); return (BaseType.Any, CollectionType.Tuple, it); }
        if (ts == "Reference") return (BaseType.Reference, CollectionType.Single, null);
        if (ts == "Text") return (BaseType.String, CollectionType.Text, null);
        return (Stb(ts), CollectionType.Single, null);
    }

    private BaseType Stb(string t)
    {
        var m = new Dictionary<string, BaseType>(StringComparer.OrdinalIgnoreCase) { ["any"]=BaseType.Any,["string"]=BaseType.String,["number"]=BaseType.Number,["long"]=BaseType.Long,["int"]=BaseType.Int,["boolean"]=BaseType.Boolean,["date"]=BaseType.Date,["datetime"]=BaseType.DateTime,["object"]=BaseType.Object,["reference"]=BaseType.Reference };
        return m.TryGetValue(t, out var b) ? b : throw new TypeException($"Unknown type: '{t}'");
    }

    private List<string> ParseCsvLine(string line)
    {
        var vals = new List<string>(); var cur = new StringBuilder(); var iq = false;
        for (var i = 0; i < line.Length;)
        {
            var c = line[i];
            if (iq) { if (c == '"') { if (i + 1 < line.Length && line[i + 1] == '"') { cur.Append('"'); i += 2; } else { iq = false; i++; } } else { cur.Append(c); i++; } }
            else { if (c == '"') { iq = true; i++; } else if (c == ',') { vals.Add(cur.ToString()); cur.Clear(); i++; } else { cur.Append(c); i++; } }
        }
        vals.Add(cur.ToString()); return vals;
    }

    private List<object?> ConvertRowTypes(List<string> vals, List<ColumnDef> cols)
    {
        var cv = new List<object?> { int.Parse(vals[0]) };
        for (var i = 0; i < cols.Count; i++) cv.Add(Cv(vals[i + 1], cols[i]));
        return cv;
    }

    private object? Cv(string v, ColumnDef c)
    {
        if (string.IsNullOrEmpty(v)) return null;
        return c.BaseType switch
        {
            BaseType.String => v,
            BaseType.Number => double.TryParse(v, out var n) ? n : throw new TypeException($"Invalid number"),
            BaseType.Int => int.TryParse(v, out var i) ? i : throw new TypeException($"Invalid int"),
            BaseType.Long => long.TryParse(v, out var l) ? l : throw new TypeException($"Invalid long"),
            BaseType.Boolean => v.ToLower() == "true" || throw new TypeException($"Invalid boolean"),
            BaseType.Date => Regex.IsMatch(v, @"^\d{4}-\d{2}-\d{2}$") ? v : throw new TypeException($"Invalid date"),
            BaseType.DateTime => Regex.IsMatch(v, @"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}") ? v : throw new TypeException($"Invalid datetime"),
            BaseType.Object => System.Text.Json.JsonSerializer.Deserialize<object>(v)!,
            BaseType.Reference => v.StartsWith("@") ? v : throw new TypeException($"Invalid reference"),
            _ => v
        };
    }

    private (BinaryPart, int) ParseBinaryPart(string[] lines, int si, List<ManifestEntry> manifest)
    {
        var m = Regex.Match(lines[si], @"^\[PART:([^.]+)\.(\d+)\|([^|]+)\|(\d+)\]$");
        if (!m.Success) throw new FormatException($"Invalid binary part at line {si + 1}");
        var name = m.Groups[1].Value; var idx = int.Parse(m.Groups[2].Value); var mime = m.Groups[3].Value;
        var li = si + 1; var dl = new List<string>();
        while (li < lines.Length && lines[li] != $"[END:{name}.{idx}]") dl.Add(lines[li++]);
        if (li >= lines.Length) throw new FormatException($"Missing end marker for '{name}.{idx}'");
        var data = Encoding.UTF8.GetBytes(string.Join("\n", dl));
        var me = manifest.FirstOrDefault(x => x.Type == name && x.Index == idx);
        if (me == null) throw new FormatException($"Manifest entry not found for '{name}.{idx}'");
        return (new BinaryPart { Name = name, Index = idx, MimeType = mime, Size = data.Length, Data = data, ManifestEntry = me }, li + 1);
    }

    private (TextPart, int) ParseTextPart(string[] lines, int si, List<ManifestEntry> manifest)
    {
        var m = Regex.Match(lines[si], @"^\[TEXT:([^.]+)\.(\d+)\|([^|]+)\]$");
        if (!m.Success) throw new FormatException($"Invalid text part at line {si + 1}");
        var name = m.Groups[1].Value; var idx = int.Parse(m.Groups[2].Value); var mime = m.Groups[3].Value;
        var li = si + 1; var cl = new List<string>();
        while (li < lines.Length && lines[li] != $"[END:{name}.{idx}]") cl.Add(lines[li++]);
        if (li >= lines.Length) throw new FormatException($"Missing end marker for '{name}.{idx}'");
        var me = manifest.FirstOrDefault(x => x.Type == name && x.Index == idx);
        if (me == null) throw new FormatException($"Manifest entry not found for '{name}.{idx}'");
        return (new TextPart { Name = name, Index = idx, MimeType = mime, Content = string.Join("\n", cl), ManifestEntry = me }, li + 1);
    }

    private void ValidateReferences(List<ManifestEntry> manifest, List<Table> tables)
    {
        var vr = new HashSet<string>();
        foreach (var e in manifest) { if (e.Format == PartFormat.CsvDefault) { var t = tables.FirstOrDefault(x => x.Name == e.Type); if (t != null) for (var i = 0; i < t.Rows.Count; i++) vr.Add($"{e.Type}.{i}"); } else for (var i = 0; i < e.Count; i++) vr.Add($"{e.Type}.{i}"); }
        foreach (var t in tables) foreach (var r in t.Rows) for (var ci = 0; ci < t.Columns.Count; ci++) if (t.Columns[ci].BaseType == BaseType.Reference) { var rv = r[ci + 1]?.ToString(); if (!string.IsNullOrEmpty(rv) && !vr.Contains(rv[1..])) throw new ReferenceException($"Reference '{rv}' not found"); }
    }

    public string Serialize(List<ManifestEntry> manifest, List<Table> tables, List<BinaryPart>? bps = null, List<TextPart>? tps = null)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# CSV-MP v0.8 Manifesto").AppendLine($"# Generated: {DateTime.UtcNow:O}").AppendLine().AppendLine("&|type|description|count|format|author|version|hash");
        foreach (var e in manifest) sb.AppendLine($"{e.Index}|{e.Type}|{e.Description ?? ""}|{e.Count}|{e.Format}|{e.Author ?? ""}|{e.Version}|{e.Hash ?? ""}");
        sb.AppendLine();
        foreach (var t in tables)
        {
            var hc = t.Columns.Select(c => { var ts = Bts(c.BaseType); return c.CollectionType switch { CollectionType.Array => $"{c.Name}:{ts}[]", CollectionType.Tuple when c.TupleTypes != null => $"{c.Name}:[{string.Join(",", c.TupleTypes.Select(Bts))}]", _ => $"{c.Name}:{ts}" }; });
            sb.AppendLine($"&:{string.Join(",", hc)}");
            foreach (var r in t.Rows) sb.AppendLine(string.Join(",", r.Select((v, i) => i == 0 ? v?.ToString() ?? "" : Vts(v, t.Columns[i - 1]))));
            sb.AppendLine();
        }
        foreach (var p in bps ?? Enumerable.Empty<BinaryPart>()) { sb.AppendLine($"[PART:{p.Name}.{p.Index}|{p.MimeType}|{p.Size}]").AppendLine(Encoding.UTF8.GetString(p.Data)).AppendLine($"[END:{p.Name}.{p.Index}]").AppendLine(); }
        foreach (var p in tps ?? Enumerable.Empty<TextPart>()) { sb.AppendLine($"[TEXT:{p.Name}.{p.Index}|{p.MimeType}]").AppendLine(p.Content).AppendLine($"[END:{p.Name}.{p.Index}]").AppendLine(); }
        return sb.ToString();
    }

    private static string Bts(BaseType b) => b switch { BaseType.Any => "any", BaseType.String => "string", BaseType.Number => "number", BaseType.Long => "long", BaseType.Int => "int", BaseType.Boolean => "boolean", BaseType.Date => "date", BaseType.DateTime => "datetime", BaseType.Object => "object", BaseType.Reference => "Reference", _ => "any" };

    private string Vts(object? v, ColumnDef c)
    {
        if (v == null) return "";
        return c.BaseType switch { BaseType.String => Nq(v.ToString()!) ? $"\"{v.ToString()!.Replace("\"", "\"\"")}\"" : v.ToString()!, BaseType.Object => $"\"{System.Text.Json.JsonSerializer.Serialize(v).Replace("\"", "\"\"")}\"", BaseType.Date or BaseType.DateTime => $"\"{v}\"", BaseType.Reference => v.ToString()!, BaseType.Boolean => (bool)v! ? "true" : "false", _ => v.ToString()! };
    }
    private static bool Nq(string v) => v.Contains(",") || v.Contains("\"") || v.Contains("\n");
    public string CalculateHash(string c) { using var s = SHA256.Create(); return BitConverter.ToString(s.ComputeHash(Encoding.UTF8.GetBytes(c))).Replace("-", "").ToLowerInvariant(); }
}

public class ParseResult { public List<ManifestEntry> Manifest { get; set; } = new(); public List<Table> Tables { get; set; } = new(); public List<BinaryPart> BinaryParts { get; set; } = new(); public List<TextPart> TextParts { get; set; } = new(); }

// Convenience functions
public static class CsvMp
{
    /// <summary>
    /// Parse CSV-MP content
    /// </summary>
    public static ParseResult Parse(string content, ValidationConfig? config = null)
        => new CsvMpParser(config).Parse(content);

    /// <summary>
    /// Serialize to CSV-MP format
    /// </summary>
    public static string Serialize(List<ManifestEntry> manifest, List<Table> tables, 
        List<BinaryPart>? binaryParts = null, List<TextPart>? textParts = null,
        ValidationConfig? config = null)
        => new CsvMpParser(config).Serialize(manifest, tables, binaryParts, textParts);

    /// <summary>
    /// Simple Deserialization API - Converts CSV-MP content to plain C# objects
    /// </summary>
    public static Dictionary<string, object> Deserialize(string content, ValidationConfig? config = null)
    {
        var parser = new CsvMpParser(config);
        var result = parser.Parse(content);
        var output = new Dictionary<string, object>();

        // Convert tables to list of dicts by type name
        foreach (var table in result.Tables)
        {
            var rows = new List<Dictionary<string, object?>>();
            foreach (var row in table.Rows)
            {
                var obj = new Dictionary<string, object?>();
                for (int i = 0; i < table.Columns.Count; i++)
                    obj[table.Columns[i].Name] = row[i + 1];
                rows.Add(obj);
            }
            output[table.Name] = rows;
        }

        if (result.BinaryParts.Count > 0) output["_binary"] = result.BinaryParts;
        if (result.TextParts.Count > 0) output["_text"] = result.TextParts;

        return output;
    }

    /// <summary>
    /// Simple Serialization API - Objects to CSV-MP
    /// </summary>
    public static string ToCsvMp(Dictionary<string, object> data, string? author = null, string? version = null)
    {
        author ??= "csv-mp";
        version ??= "0.8";
        var manifest = new List<ManifestEntry>();
        var tables = new List<Table>();
        var partIndex = 0;

        foreach (var kvp in data)
        {
            if (kvp.Key.StartsWith("_")) continue;
            if (kvp.Value is not List<object> list || list.Count == 0) continue;
            if (list[0] is not Dictionary<string, object> firstRow) continue;

            var columns = new List<ColumnDef>();
            foreach (var col in firstRow)
            {
                var baseType = col.Value switch
                {
                    bool => BaseType.Boolean,
                    int => BaseType.Int,
                    long => BaseType.Long,
                    double or float => BaseType.Number,
                    string s when s.StartsWith("@") => BaseType.Reference,
                    Dictionary<string, object> => BaseType.Object,
                    _ => BaseType.String
                };
                columns.Add(new ColumnDef { Name = col.Key, BaseType = baseType, CollectionType = CollectionType.Single });
            }

            var rows = new List<List<object?>>();
            for (int idx = 0; idx < list.Count; idx++)
            {
                var row = new List<object?> { idx };
                var dict = (Dictionary<string, object>)list[idx];
                foreach (var col in columns)
                    row.Add(dict.TryGetValue(col.Name, out var v) ? v : null);
                rows.Add(row);
            }

            var me = new ManifestEntry
            {
                Index = partIndex,
                Type = kvp.Key,
                Description = $"{kvp.Key} data",
                Count = list.Count,
                Format = PartFormat.CsvDefault,
                Author = author,
                Version = version,
                Hash = ""
            };

            manifest.Add(me);
            tables.Add(new Table { Name = kvp.Key, Columns = columns, Rows = rows, ManifestEntry = me });
            partIndex++;
        }

        return new CsvMpParser().Serialize(manifest, tables);
    }

    /// <summary>
    /// Alias for Deserialize() for consistency
    /// </summary>
    public static Dictionary<string, object> FromCsvMp(string content, ValidationConfig? config = null)
        => Deserialize(content, config);

    /// <summary>
    /// Read CSV-MP from file
    /// </summary>
    public static Dictionary<string, object> ReadCsvMp(string filePath, ValidationConfig? config = null)
    {
        var content = File.ReadAllText(filePath, Encoding.UTF8);
        return Deserialize(content, config);
    }

    /// <summary>
    /// Write CSV-MP to file
    /// </summary>
    public static void WriteCsvMp(string filePath, Dictionary<string, object> data, string? author = null, string? version = null)
    {
        var content = ToCsvMp(data, author, version);
        File.WriteAllText(filePath, content, Encoding.UTF8);
    }
}
