"""
Benchmark tests for CSV-MP protocol performance.
Tests parsing and serialization performance with various data sizes.
"""
import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csvmp_types import ManifestEntry, TablePart
from parser import CsvMpParser


class TestBenchmark:
    """Benchmark tests for CSV-MP operations."""

    def test_parse_small_manifest(self, benchmark):
        """Benchmark parsing a small manifest (10 rows)."""
        csv_data = """# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|TestRequest|Test data|10|text/csv|benchmark|1.0|

&:id:int,name:string,value:number
0,1,Alice,100
1,2,Bob,200
2,3,Charlie,300
3,4,David,400
4,5,Eve,500
5,6,Frank,600
6,7,Grace,700
7,8,Henry,800
8,9,Ivy,900
9,10,Jack,1000
"""
        
        def parse():
            parser = CsvMpParser()
            return parser.parse(csv_data)
        
        result = benchmark(parse)
        assert len(result.parts) == 1
        assert result.parts[0].row_count == 10

    def test_parse_medium_manifest(self, benchmark):
        """Benchmark parsing a medium manifest (1000 rows)."""
        # Generate 1000 rows
        rows = "\n".join([f"{i},{i},Name{i},{i*10}" for i in range(1000)])
        csv_data = f"""# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|TestRequest|Test data|1000|text/csv|benchmark|1.0|

&:id:int,name:string,value:number
{rows}
"""
        
        def parse():
            parser = CsvMpParser()
            return parser.parse(csv_data)
        
        result = benchmark(parse)
        assert len(result.parts) == 1
        assert result.parts[0].row_count == 1000

    def test_parse_large_manifest(self, benchmark):
        """Benchmark parsing a large manifest (10000 rows)."""
        # Generate 10000 rows
        rows = "\n".join([f"{i},{i},Name{i},{i*10}" for i in range(10000)])
        csv_data = f"""# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|TestRequest|Test data|10000|text/csv|benchmark|1.0|

&:id:int,name:string,value:number
{rows}
"""
        
        def parse():
            parser = CsvMpParser()
            return parser.parse(csv_data)
        
        result = benchmark(parse)
        assert len(result.parts) == 1
        assert result.parts[0].row_count == 10000

    def test_serialize_small_table(self, benchmark):
        """Benchmark serializing a small table (10 rows)."""
        entries = [TablePart(
            type="TestResponse",
            description="Test response data",
            row_count=10,
            content_type="text/csv",
            author="benchmark",
            version="1.0",
            columns=["id", "name", "value"],
            column_types=["int", "string", "number"],
            data=[[i, f"Name{i}", i*10] for i in range(10)]
        )]
        
        def serialize():
            parser = CsvMpParser()
            return parser.serialize(entries)
        
        result = benchmark(serialize)
        assert "TestResponse" in result

    def test_serialize_medium_table(self, benchmark):
        """Benchmark serializing a medium table (1000 rows)."""
        entries = [TablePart(
            type="TestResponse",
            description="Test response data",
            row_count=1000,
            content_type="text/csv",
            author="benchmark",
            version="1.0",
            columns=["id", "name", "value"],
            column_types=["int", "string", "number"],
            data=[[i, f"Name{i}", i*10] for i in range(1000)]
        )]
        
        def serialize():
            parser = CsvMpParser()
            return parser.serialize(entries)
        
        result = benchmark(serialize)
        assert "TestResponse" in result

    def test_roundtrip_small(self, benchmark):
        """Benchmark roundtrip (serialize + parse) for small data."""
        original_data = [[i, f"Name{i}", i*10] for i in range(100)]
        entries = [TablePart(
            type="RoundTripTest",
            description="Roundtrip test data",
            row_count=100,
            content_type="text/csv",
            author="benchmark",
            version="1.0",
            columns=["id", "name", "value"],
            column_types=["int", "string", "number"],
            data=original_data
        )]
        
        def roundtrip():
            parser = CsvMpParser()
            serialized = parser.serialize(entries)
            parsed = parser.parse(serialized)
            return parsed
        
        result = benchmark(roundtrip)
        assert len(result.parts) == 1
        assert result.parts[0].row_count == 100

    def test_multiple_parts(self, benchmark):
        """Benchmark parsing multiple parts in one document."""
        csv_data = """# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|Part1|First part|100|text/csv|benchmark|1.0|
1|Part2|Second part|100|text/csv|benchmark|1.0|
2|Part3|Third part|100|text/csv|benchmark|1.0|

&:id:int,name:string
""" + "\n".join([f"{i},Name{i}" for i in range(100)]) + """

&:id:int,value:number
""" + "\n".join([f"{i},{i*10}" for i in range(100)]) + """

&:id:int,flag:boolean
""" + "\n".join([f"{i},{i%2==0}" for i in range(100)])
        
        def parse():
            parser = CsvMpParser()
            return parser.parse(csv_data)
        
        result = benchmark(parse)
        assert len(result.parts) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
