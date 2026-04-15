using System;
using CsvMp;

namespace SomaService
{
    /// <summary>
    /// Request do serviço de soma
    /// </summary>
    public class SomaRequest
    {
        public int A { get; set; }
        public int B { get; set; }
    }

    /// <summary>
    /// Response do serviço de soma
    /// </summary>
    public class SomaResponse
    {
        public int A { get; set; }
        public int B { get; set; }
        public int C { get; set; }
    }

    /// <summary>
    /// Serviço de Soma usando protocolo CSV-MP
    /// </summary>
    public class SomaService
    {
        /// <summary>
        /// Processa uma requisição de soma e retorna o resultado
        /// </summary>
        public static SomaResponse Somar(SomaRequest request)
        {
            return new SomaResponse
            {
                A = request.A,
                B = request.B,
                C = request.A + request.B
            };
        }

        /// <summary>
        /// Serializa uma requisição para formato CSV-MP
        /// </summary>
        public static string SerializeRequest(SomaRequest request)
        {
            var manifest = new ManifestEntry
            {
                Index = 0,
                Type = "SomaRequest",
                Description = "SomaRequest data",
                Count = 1,
                ContentType = "text/csv",
                Author = "soma-service",
                Version = "1.0",
                Hash = ""
            };

            var schema = new[]
            {
                new ColumnSchema { Name = "a", DataType = "int" },
                new ColumnSchema { Name = "b", DataType = "int" }
            };

            var rows = new[]
            {
                new object[] { 0, request.A, request.B }
            };

            var result = new System.Text.StringBuilder();
            result.AppendLine("# CSV-MP v0.2 Manifesto");
            result.AppendLine(CsvMpParser.GenerateManifest(manifest));
            result.AppendLine();
            result.AppendLine(CsvMpParser.GenerateSchema(schema.ToList()));
            result.AppendLine(CsvMpParser.GenerateRow(rows[0].ToList()));

            return result.ToString();
        }

        /// <summary>
        /// Desserializa uma requisição CSV-MP
        /// </summary>
        public static SomaRequest DeserializeRequest(string csvMpData)
        {
            var lines = csvMpData.Split('\n', StringSplitOptions.RemoveEmptyEntries);
            var tableLines = new System.Collections.Generic.List<string>();
            
            bool foundSchema = false;
            foreach (var line in lines)
            {
                var trimmed = line.Trim();
                if (trimmed.StartsWith("&:"))
                {
                    foundSchema = true;
                }
                
                if (foundSchema)
                {
                    tableLines.Add(trimmed);
                }
            }

            var (schema, rows) = CsvMpParser.ParseTable(tableLines.ToArray());
            
            if (rows.Count == 0)
                throw new ArgumentException("Nenhuma linha de dados encontrada");

            var firstRow = rows[0];
            return new SomaRequest
            {
                A = Convert.ToInt32(firstRow[1]),
                B = Convert.ToInt32(firstRow[2])
            };
        }

        /// <summary>
        /// Serializa uma resposta para formato CSV-MP
        /// </summary>
        public static string SerializeResponse(SomaResponse response)
        {
            var manifest = new ManifestEntry
            {
                Index = 0,
                Type = "SomaResponse",
                Description = "SomaResponse data",
                Count = 1,
                ContentType = "text/csv",
                Author = "soma-service",
                Version = "1.0",
                Hash = ""
            };

            var schema = new[]
            {
                new ColumnSchema { Name = "a", DataType = "int" },
                new ColumnSchema { Name = "b", DataType = "int" },
                new ColumnSchema { Name = "c", DataType = "int" }
            };

            var rows = new[]
            {
                new object[] { 0, response.A, response.B, response.C }
            };

            var result = new System.Text.StringBuilder();
            result.AppendLine("# CSV-MP v0.2 Manifesto");
            result.AppendLine(CsvMpParser.GenerateManifest(manifest));
            result.AppendLine();
            result.AppendLine(CsvMpParser.GenerateSchema(schema.ToList()));
            result.AppendLine(CsvMpParser.GenerateRow(rows[0].ToList()));

            return result.ToString();
        }

        /// <summary>
        /// Desserializa uma resposta CSV-MP
        /// </summary>
        public static SomaResponse DeserializeResponse(string csvMpData)
        {
            var lines = csvMpData.Split('\n', StringSplitOptions.RemoveEmptyEntries);
            var tableLines = new System.Collections.Generic.List<string>();
            
            bool foundSchema = false;
            foreach (var line in lines)
            {
                var trimmed = line.Trim();
                if (trimmed.StartsWith("&:"))
                {
                    foundSchema = true;
                }
                
                if (foundSchema)
                {
                    tableLines.Add(trimmed);
                }
            }

            var (schema, rows) = CsvMpParser.ParseTable(tableLines.ToArray());
            
            if (rows.Count == 0)
                throw new ArgumentException("Nenhuma linha de dados encontrada");

            var firstRow = rows[0];
            return new SomaResponse
            {
                A = Convert.ToInt32(firstRow[1]),
                B = Convert.ToInt32(firstRow[2]),
                C = Convert.ToInt32(firstRow[3])
            };
        }
    }

    /// <summary>
    /// Programa principal demonstrando o serviço
    /// </summary>
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("=== CSV-MP Soma Service Demo ===\n");

            // Exemplo simples
            var request = new SomaRequest { A = 10, B = 20 };
            
            Console.WriteLine("=== CSV-MP Request ===");
            var serializedRequest = SomaService.SerializeRequest(request);
            Console.WriteLine(serializedRequest);

            Console.WriteLine("=== Processando Soma ===");
            var deserializedRequest = SomaService.DeserializeRequest(serializedRequest);
            Console.WriteLine($"a = {deserializedRequest.A}");
            Console.WriteLine($"b = {deserializedRequest.B}");

            var response = SomaService.Somar(deserializedRequest);
            
            Console.WriteLine("\n=== CSV-MP Response ===");
            var serializedResponse = SomaService.SerializeResponse(response);
            Console.WriteLine(serializedResponse);

            Console.WriteLine("=== Resultado Final ===");
            Console.WriteLine($"{response.A} + {response.B} = {response.C}");

            // Exemplo em lote
            Console.WriteLine("\n=== Exemplo: Múltiplas Somas em Lote ===");
            var batchRequests = new[]
            {
                new SomaRequest { A = 5, B = 3 },
                new SomaRequest { A = 100, B = 250 },
                new SomaRequest { A = -10, B = 30 },
                new SomaRequest { A = 0, B = 0 }
            };

            Console.WriteLine("CSV-MP Batch Request:");
            var batchManifest = new ManifestEntry
            {
                Index = 0,
                Type = "SomaRequest",
                Description = "SomaRequest data",
                Count = batchRequests.Length,
                ContentType = "text/csv",
                Author = "soma-service",
                Version = "1.0",
                Hash = ""
            };

            var batchSchema = new[]
            {
                new ColumnSchema { Name = "a", DataType = "int" },
                new ColumnSchema { Name = "b", DataType = "int" }
            };

            var batchResult = new System.Text.StringBuilder();
            batchResult.AppendLine("# CSV-MP v0.2 Manifesto");
            batchResult.AppendLine(CsvMpParser.GenerateManifest(batchManifest));
            batchResult.AppendLine();
            batchResult.AppendLine(CsvMpParser.GenerateSchema(batchSchema.ToList()));
            
            for (int i = 0; i < batchRequests.Length; i++)
            {
                batchResult.AppendLine($"{i},{batchRequests[i].A},{batchRequests[i].B}");
            }
            
            Console.WriteLine(batchResult.ToString());

            Console.WriteLine("CSV-MP Batch Response:");
            var batchResponseManifest = new ManifestEntry
            {
                Index = 0,
                Type = "SomaResponse",
                Description = "SomaResponse data",
                Count = batchRequests.Length,
                ContentType = "text/csv",
                Author = "soma-service",
                Version = "1.0",
                Hash = ""
            };

            var batchResponseSchema = new[]
            {
                new ColumnSchema { Name = "a", DataType = "int" },
                new ColumnSchema { Name = "b", DataType = "int" },
                new ColumnSchema { Name = "c", DataType = "int" }
            };

            var batchResponseResult = new System.Text.StringBuilder();
            batchResponseResult.AppendLine("# CSV-MP v0.2 Manifesto");
            batchResponseResult.AppendLine(CsvMpParser.GenerateManifest(batchResponseManifest));
            batchResponseResult.AppendLine();
            batchResponseResult.AppendLine(CsvMpParser.GenerateSchema(batchResponseSchema.ToList()));
            
            foreach (var req in batchRequests)
            {
                var resp = SomaService.Somar(req);
                batchResponseResult.AppendLine($"{resp.A},{resp.B},{resp.C}");
            }
            
            Console.WriteLine(batchResponseResult.ToString());
        }
    }
}
