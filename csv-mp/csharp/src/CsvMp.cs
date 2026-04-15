using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;

namespace CsvMp
{
    /// <summary>
    /// Representa uma entrada no manifesto CSV-MP
    /// </summary>
    public class ManifestEntry
    {
        public int Index { get; set; }
        public string Type { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public int Count { get; set; }
        public string ContentType { get; set; } = "text/csv";
        public string Author { get; set; } = string.Empty;
        public string Version { get; set; } = string.Empty;
        public string Hash { get; set; } = string.Empty;
    }

    /// <summary>
    /// Representa um schema de coluna
    /// </summary>
    public class ColumnSchema
    {
        public string Name { get; set; } = string.Empty;
        public string DataType { get; set; } = string.Empty;
    }

    /// <summary>
    /// Representa uma parte de dados em formato tabela
    /// </summary>
    public class TablePart
    {
        public List<ColumnSchema> Schema { get; set; } = new List<ColumnSchema>();
        public List<List<object>> Rows { get; set; } = new List<List<object>>();
    }

    /// <summary>
    /// Parser do protocolo CSV-MP
    /// </summary>
    public class CsvMpParser
    {
        public static ManifestEntry ParseManifest(string line)
        {
            // Remove o prefixo &| e o sufixo |
            if (!line.StartsWith("&|") || !line.EndsWith("|"))
                throw new ArgumentException("Linha de manifesto inválida");

            var content = line.Substring(2, line.Length - 3);
            var parts = content.Split('|');
            
            if (parts.Length < 8)
                throw new ArgumentException("Manifesto incompleto");

            return new ManifestEntry
            {
                Index = int.Parse(parts[0].Split(':')[1]),
                Type = parts[1].Split(':')[1],
                Description = parts[2].Split(':')[1],
                Count = int.Parse(parts[3].Split(':')[1]),
                ContentType = parts[4].Split(':')[1],
                Author = parts[5].Split(':')[1],
                Version = parts[6].Split(':')[1],
                Hash = parts[7].Split(':')[1]
            };
        }

        public static (List<ColumnSchema> Schema, List<List<object>> Rows) ParseTable(string[] lines)
        {
            var schemaLine = lines[0];
            if (!schemaLine.StartsWith("&:"))
                throw new ArgumentException("Linha de schema inválida");

            var schemaContent = schemaLine.Substring(2);
            var columns = schemaContent.Split(',');
            var schema = new List<ColumnSchema>();

            foreach (var col in columns)
            {
                var parts = col.Trim().Split(':');
                schema.Add(new ColumnSchema
                {
                    Name = parts[0],
                    DataType = parts[1]
                });
            }

            var rows = new List<List<object>>();
            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i])) continue;
                
                var values = lines[i].Split(',');
                var row = new List<object>();
                
                for (int j = 0; j < values.Length; j++)
                {
                    var value = values[j].Trim();
                    var dataType = j < schema.Count ? schema[j].DataType : "string";
                    
                    row.Add(ConvertValue(value, dataType));
                }
                
                rows.Add(row);
            }

            return (schema, rows);
        }

        private static object ConvertValue(string value, string dataType)
        {
            return dataType.ToLower() switch
            {
                "int" or "integer" => int.Parse(value),
                "number" or "double" or "float" => double.Parse(value),
                "boolean" or "bool" => bool.Parse(value),
                _ => value
            };
        }

        public static string GenerateManifest(ManifestEntry entry)
        {
            return $"&|index:{entry.Index}|type:{entry.Type}|description:{entry.Description}|count:{entry.Count}|contentType:{entry.ContentType}|author:{entry.Author}|version:{entry.Version}|hash:{entry.Hash}|";
        }

        public static string GenerateSchema(List<ColumnSchema> schema)
        {
            var columns = schema.Select(c => $"{c.Name}:{c.DataType}");
            return "&:" + string.Join(",", columns);
        }

        public static string GenerateRow(List<object> values)
        {
            return string.Join(",", values.Select(v => v?.ToString() ?? ""));
        }
    }
}
