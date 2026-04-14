"""
CSV-MP Soma Service Example

Este exemplo demonstra como criar um serviço de soma de duas variáveis inteiras
usando o formato CSV-MP para serialização dos dados de entrada e saída.
"""

from src import to_csv_mp, deserialize


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
    # Dados de entrada
    input_data = {
        'SomaRequest': [
            {'a': 10, 'b': 20}
        ]
    }
    
    # Serializar request para CSV-MP
    csv_mp_request = to_csv_mp(input_data, {
        'author': 'soma-service',
        'version': '1.0',
        'description': 'Requisição de soma de dois inteiros'
    })
    
    print('=== CSV-MP Request ===')
    print(csv_mp_request)
    print()
    
    # Desserializar request
    parsed_request = deserialize(csv_mp_request)
    request_item = parsed_request['SomaRequest'][0]
    
    a = request_item['a']
    b = request_item['b']
    
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
    
    # Serializar response para CSV-MP
    csv_mp_response = to_csv_mp(output_data, {
        'author': 'soma-service',
        'version': '1.0',
        'description': 'Resposta com resultado da soma'
    })
    
    print('=== CSV-MP Response ===')
    print(csv_mp_response)
    print()
    
    # Desserializar response para verificação
    parsed_response = deserialize(csv_mp_response)
    response_item = parsed_response['SomaResponse'][0]
    
    print('=== Resultado Final ===')
    print(f'{response_item["a"]} + {response_item["b"]} = {response_item["c"]}')
    print()
    
    # Exemplo adicional: Múltiplas somas em lote
    print('=== Exemplo: Múltiplas Somas em Lote ===')
    batch_data = {
        'SomaRequest': [
            {'a': 5, 'b': 3},
            {'a': 100, 'b': 250},
            {'a': -10, 'b': 30},
            {'a': 0, 'b': 0}
        ]
    }
    
    csv_mp_batch = to_csv_mp(batch_data, {
        'author': 'soma-service',
        'version': '1.0'
    })
    
    print('CSV-MP Batch Request:')
    print(csv_mp_batch)
    print()
    
    # Processar batch
    parsed_batch = deserialize(csv_mp_batch)
    results = []
    
    for item in parsed_batch['SomaRequest']:
        resultado = soma_service(item['a'], item['b'])
        results.append({
            'a': item['a'],
            'b': item['b'],
            'c': resultado['c']
        })
    
    batch_response = {
        'SomaResponse': results
    }
    
    csv_mp_batch_response = to_csv_mp(batch_response, {
        'author': 'soma-service',
        'version': '1.0'
    })
    
    print('CSV-MP Batch Response:')
    print(csv_mp_batch_response)


if __name__ == '__main__':
    main()
