// CSV-MP Simple API Usage Examples (C#)

using CsvMp.Parser;
using CsvMp.Types;

namespace CsvMp.Examples;

public class SimpleApiExamples
{
    public static void Run()
    {
        // Example 1: Simple Serialization - Objects to CSV-MP
        var userData = new Dictionary<string, object>
        {
            ["User"] = new List<object>
            {
                new Dictionary<string, object> { ["id"] = 1, ["name"] = "Alice", ["email"] = "alice@example.com", ["age"] = 30 },
                new Dictionary<string, object> { ["id"] = 2, ["name"] = "Bob", ["email"] = "bob@example.com", ["age"] = 25 },
                new Dictionary<string, object> { ["id"] = 3, ["name"] = "Carol", ["email"] = "carol@example.com", ["age"] = 35 }
            },
            ["Order"] = new List<object>
            {
                new Dictionary<string, object> { ["orderId"] = 101, ["userId"] = 1, ["product"] = "Laptop", ["quantity"] = 1 },
                new Dictionary<string, object> { ["orderId"] = 102, ["userId"] = 2, ["product"] = "Mouse", ["quantity"] = 2 }
            }
        };

        // Convert objects to CSV-MP format
        var csvMpContent = CsvMp.ToCsvMp(userData, author: "my-app", version: "1.0");

        Console.WriteLine("CSV-MP Content:");
        Console.WriteLine(csvMpContent);

        // Example 2: Simple Deserialization - CSV-MP to Objects
        var parsedData = CsvMp.Deserialize(csvMpContent);

        Console.WriteLine("\nParsed Users:");
        foreach (var user in (List<object>)parsedData["User"])
        {
            var dict = (Dictionary<string, object>)user;
            Console.WriteLine($"  - {dict["name"]} ({dict["email"]})");
        }

        Console.WriteLine("\nParsed Orders:");
        foreach (var order in (List<object>)parsedData["Order"])
        {
            var dict = (Dictionary<string, object>)order;
            Console.WriteLine($"  - Order {dict["orderId"]}: {dict["product"]} x{dict["quantity"]}");
        }

        // Example 3: File I/O
        FileExample(userData);

        // Example 4: Round-trip conversion
        RoundTripExample();
    }

    private static void FileExample(Dictionary<string, object> userData)
    {
        // Write to file
        CsvMp.WriteCsvMp("example.csv.mp", userData, author: "my-app", version: "1.0");

        // Read from file
        var loadedData = CsvMp.ReadCsvMp("example.csv.mp");
        Console.WriteLine("\nLoaded from file successfully!");
    }

    private static void RoundTripExample()
    {
        var original = new Dictionary<string, object>
        {
            ["Product"] = new List<object>
            {
                new Dictionary<string, object> { ["sku"] = "P001", ["name"] = "Widget", ["price"] = 9.99, ["inStock"] = true },
                new Dictionary<string, object> { ["sku"] = "P002", ["name"] = "Gadget", ["price"] = 19.99, ["inStock"] = false }
            }
        };

        // Serialize
        var serialized = CsvMp.ToCsvMp(original);

        // Deserialize
        var deserialized = CsvMp.FromCsvMp(serialized);

        Console.WriteLine("\nRound-trip completed successfully!");
    }
}

// Entry point
public class Program
{
    public static void Main(string[] args)
    {
        SimpleApiExamples.Run();
    }
}
