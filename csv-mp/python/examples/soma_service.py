"""
CSV-MP Soma Service Example

Este exemplo demonstra como criar um serviço de soma de duas variáveis inteiras
usando o formato CSV-MP para serialização dos dados de entrada e saída.

Demonstra dois modos:
1. MODO LITE: Sem manifesto, apenas tabela (transações rápidas)
2. MODO FULL: Com manifesto e múltiplos conteúdos
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from csvmp_types import TablePart, ManifestEntry, ColumnDef, BaseType, CollectionType
from parser import CsvMpParser


def to_csv_mp_lite(data: dict, columns: list) -> str:
    """
    Serializar dados no MODO LITE (sem manifesto, transação rápida).
    Ideal para operações simples de único conteúdo.
    """
    # Build schema line
    schema_parts = [f"{col}:int" for col in columns]
    schema_line = "&:" + ",".join(schema_parts)
    
    # Build data rows
    items = data[list(data.keys())[0]] if isinstance(data[list(data.keys())[0]], list) else [data[list(data.keys())[0]]]
    rows = []
    for idx, item in enumerate(items):
        row_values = [str(idx)] + [str(item[col]) for col in columns]
        rows.append(",".join(row_values))
    
    return schema_line + "\n" + "\n".join(rows)


def to_csv_mp_full(data: dict, type_name: str, description: str = "") -> str:
    """Serialize data to CSV-MP format with manifesto (Full Mode)."""
    # Extrai colunas e valores do primeiro item do dict
    first_key = list(data.keys())[0]
    first_item = data[first_key][0] if isinstance(data[first_key], list) else data[first_key]
    
    columns = list(first_item.keys())
    values = list(first_item.values())
    
    # Create manifest entry
    manifest_entry = ManifestEntry(
        index=0,
        type=type_name,
        description=description,
        count=len(data[first_key]) if isinstance(data[first_key], list) else 1,
        contentType="text/csv",
        author="soma-service",
        version="1.0"
    )
    
    # Detect column types (assume int for this example)
    col_defs = [ColumnDef(name=col, base_type=BaseType.Int, collection_type=CollectionType.Single) for col in columns]
    
    # Create table part with all rows
    rows = []
    items = data[first_key] if isinstance(data[first_key], list) else [data[first_key]]
    for idx, item in enumerate(items):
        row_values = [idx] + [item[col] for col in columns]
        rows.append(row_values)
    
    table_part = TablePart(
        name=type_name,
        columns=col_defs,
        rows=rows,
        manifest_entry=manifest_entry
    )
    
    # Use serializer with force_full_mode=True
    from serializer import CsvMpSerializer
    serializer = CsvMpSerializer()
    document = {
        'type': type_name,
        'description': description,
        'tables': [table_part],
        'binary_parts': [],
        'text_parts': []
    }
    return serializer.serialize(document, force_full_mode=True)


def deserialize(csv_mp_data: str) -> dict:
    """
    Deserialize CSV-MP data to dict structured by table name.
    No modo lite, o nome da tabela será 'unknown' e deve ser resolvido pelo contexto do service.
    """
    parser = CsvMpParser()
    result = parser.parse(csv_mp_data)
    
    # Result is a dict with 'tables' key containing list of TablePart
    output = {}
    if 'tables' in result and len(result['tables']) > 0:
        for table in result['tables']:
            # Tenta pegar nome da tabela
            table_name = getattr(table, 'name', 'unknown')
            if table_name == 'unknown' or table_name == 'Unknown':
                # No modo lite, usa 'unknown' - o server resolve pelo contexto
                table_name = 'unknown'
            
            output[table_name] = []
            for row in table.rows:
                # Pula primeira coluna (índice) e cria dict das colunas restantes
                # Se a primeira coluna for 'idx', 'index', etc, considera como índice
                first_col_name = table.columns[0].name.lower() if table.columns else ''
                is_index_col = first_col_name in ['idx', 'index', 'row_index', 'id']
                
                if is_index_col:
                    # Pula a primeira coluna (índice explícito)
                    data_cols = table.columns[1:]
                    data_row = row[1:]
                else:
                    # Pula apenas o primeiro valor (índice implícito)
                    data_cols = table.columns
                    data_row = row[1:]
                
                output[table_name].append({col.name: data_row[i] for i, col in enumerate(data_cols)})
    
    return output


def soma_service(a: int, b: int) -> dict:
    """
    Serviço de soma que recebe dois inteiros e retorna o resultado.
    
    Args:
        a: Primeiro número inteiro
        b: Segundo número inteiro
    
    Returns:
        Dicionário com o resultado da soma (c = a + b)
    """
    c = a + b
    return {'c': c}


def main():
    print("=" * 60)
    print("EXEMPLO 1: MODO LITE (Sem manifesto - Transação Rápida)")
    print("=" * 60)
    print()
    
    # Dados de entrada
    input_data = {'SomaRequest': [{'a': 10, 'b': 20}]}
    
    # Serializar request para CSV-MP Lite (sem manifesto)
    csv_mp_request_lite = to_csv_mp_lite(input_data, ['a', 'b'])
    
    print('=== CSV-MP Lite Request (Sem Manifesto) ===')
    print(csv_mp_request_lite)
    print()
    
    # Desserializar request
    parsed_request = deserialize(csv_mp_request_lite)
    print(f"Tabela parseada com nome: '{list(parsed_request.keys())[0]}'")
    print("(No modo lite, o server resolve o tipo pelo contexto do service)")
    print()
    
    # Como o server resolve: pega os dados independentemente do nome
    request_data = list(parsed_request.values())[0][0]
    a = request_data['a']
    b = request_data['b']
    
    print(f'=== Processando Soma ===')
    print(f'a = {a}')
    print(f'b = {b}')
    print()
    
    # Executar serviço de soma
    resultado = soma_service(a, b)
    
    # Preparar response
    output_data = {
        'SomaResponse': [
            {'a': a, 'b': b, 'c': resultado['c']}
        ]
    }
    
    # Serializar response para CSV-MP Lite
    csv_mp_response_lite = to_csv_mp_lite(output_data, ['a', 'b', 'c'])
    
    print('=== CSV-MP Lite Response (Sem Manifesto) ===')
    print(csv_mp_response_lite)
    print()
    
    # Desserializar response para verificação
    parsed_response = deserialize(csv_mp_response_lite)
    response_data = list(parsed_response.values())[0][0]
    
    print('=== Resultado Final ===')
    print(f'{response_data["a"]} + {response_data["b"]} = {response_data["c"]}')
    print()
    
    print("=" * 60)
    print("EXEMPLO 2: MODO FULL (Com manifesto - Múltiplos Conteúdos)")
    print("=" * 60)
    print()
    
    # Serializar request para CSV-MP Full (com manifesto)
    csv_mp_request_full = to_csv_mp_full(input_data, 'SomaRequest', 'Requisição de soma de dois inteiros')
    
    print('=== CSV-MP Full Request (Com Manifesto) ===')
    print(csv_mp_request_full)
    print()
    
    # Desserializar request
    parsed_request_full = deserialize(csv_mp_request_full)
    request_item_full = parsed_request_full['SomaRequest'][0]
    
    a_full = request_item_full['a']
    b_full = request_item_full['b']
    
    print(f'=== Processando Soma (Full Mode) ===')
    print(f'a = {a_full}')
    print(f'b = {b_full}')
    print()
    
    # Executar serviço de soma
    resultado_full = soma_service(a_full, b_full)
    
    # Preparar response
    output_data_full = {
        'SomaResponse': [
            {'a': a_full, 'b': b_full, 'c': resultado_full['c']}
        ]
    }
    
    # Serializar response para CSV-MP Full
    csv_mp_response_full = to_csv_mp_full(output_data_full, 'SomaResponse', 'Resposta com resultado da soma')
    
    print('=== CSV-MP Full Response (Com Manifesto) ===')
    print(csv_mp_response_full)
    print()
    
    # Desserializar response para verificação
    parsed_response_full = deserialize(csv_mp_response_full)
    response_item_full = parsed_response_full['SomaResponse'][0]
    
    print('=== Resultado Final (Full Mode) ===')
    print(f'{response_item_full["a"]} + {response_item_full["b"]} = {response_item_full["c"]}')
    print()
    
    # Exemplo adicional: Múltiplas somas em lote (Modo Lite)
    print("=" * 60)
    print("EXEMPLO 3: Múltiplas Somas em Lote (Modo Lite)")
    print("=" * 60)
    print()
    
    batch_data = {
        'SomaRequest': [
            {'a': 5, 'b': 3},
            {'a': 100, 'b': 250},
            {'a': -10, 'b': 30},
            {'a': 0, 'b': 0}
        ]
    }
    
    csv_mp_batch = to_csv_mp_lite(batch_data, ['a', 'b'])
    print('CSV-MP Lite Batch Request:')
    print(csv_mp_batch)
    print()
    
    parsed_batch = deserialize(csv_mp_batch)
    batch_items = list(parsed_batch.values())[0]
    
    results = []
    for item in batch_items:
        result = soma_service(item['a'], item['b'])
        results.append({'a': item['a'], 'b': item['b'], 'c': result['c']})
    
    print('Resultados:')
    for r in results:
        print(f'  {r["a"]} + {r["b"]} = {r["c"]}')
    print()
    
    print("=" * 60)
    print("RESUMO DOS MODOS")
    print("=" * 60)
    print("MODO LITE:")
    print("  - Sem manifesto")
    print("  - Apenas uma tabela")
    print("  - Nome da tabela: 'unknown' (resolvido pelo server)")
    print("  - Ideal para: transações rápidas, baixo overhead")
    print()
    print("MODO FULL:")
    print("  - Com manifesto")
    print("  - Suporta múltiplas tabelas/partes")
    print("  - Nome da tabela definido no manifesto")
    print("  - Ideal para: documentos complexos, múltiplos conteúdos")


if __name__ == '__main__':
    main()
