# Serviço de Soma com CSV-MP

## Visão Geral

Este exemplo demonstra como implementar um serviço de soma de duas variáveis inteiras (`a` e `b`) que retorna o resultado (`c = a + b`) utilizando o formato **CSV-MP** para serialização e desserialização dos dados.

## Estrutura do Serviço

### Entrada (Request)

O serviço recebe um objeto CSV-MP contendo:
- **Tipo**: `SomaRequest`
- **Campos**:
  - `a` (int): Primeiro número inteiro
  - `b` (int): Segundo número inteiro

### Saída (Response)

O serviço retorna um objeto CSV-MP contendo:
- **Tipo**: `SomaResponse`
- **Campos**:
  - `a` (int): Primeiro número (mantido para referência)
  - `b` (int): Segundo número (mantido para referência)
  - `c` (int): Resultado da soma (`a + b`)

## Exemplo de Uso

### Request CSV-MP

```csv-mp
# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|SomaRequest|SomaRequest data|1|text/csv|soma-service|1.0|

&:a:int,b:int
0,10,20
```

### Response CSV-MP

```csv-mp
# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|SomaResponse|SomaResponse data|1|text/csv|soma-service|1.0|

&:a:int,b:int,c:int
0,10,20,30
```

## Código Python

```python
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


# Serializar request
input_data = {
    'SomaRequest': [
        {'a': 10, 'b': 20}
    ]
}

csv_mp_request = to_csv_mp(input_data, {
    'author': 'soma-service',
    'version': '1.0'
})

# Desserializar e processar
parsed_request = deserialize(csv_mp_request)
request_item = parsed_request['SomaRequest'][0]

resultado = soma_service(request_item['a'], request_item['b'])

# Preparar e serializar response
output_data = {
    'SomaResponse': [
        {'a': request_item['a'], 'b': request_item['b'], 'c': resultado['c']}
    ]
}

csv_mp_response = to_csv_mp(output_data, {
    'author': 'soma-service',
    'version': '1.0'
})
```

## Processamento em Lote

O serviço suporta processamento de múltiplas requisições em lote:

### Request Batch

```csv-mp
# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|SomaRequest|SomaRequest data|4|text/csv|soma-service|1.0|

&:a:int,b:int
0,5,3
1,100,250
2,-10,30
3,0,0
```

### Response Batch

```csv-mp
# CSV-MP v0.2 Manifesto
&|type:string|description:string|count:number|contentType:string|author:string|version:string|hash:string
0|SomaResponse|SomaResponse data|4|text/csv|soma-service|1.0|

&:a:int,b:int,c:int
0,5,3,8
1,100,250,350
2,-10,30,20
3,0,0,0
```

## Executando o Exemplo

```bash
cd /workspace/csv-mp/python
python -m examples.soma_service
```

## Schema dos Dados

### SomaRequest

| Campo | Tipo | Descrição |
|-------|------|-----------|
| a | int | Primeiro número inteiro |
| b | int | Segundo número inteiro |

### SomaResponse

| Campo | Tipo | Descrição |
|-------|------|-----------|
| a | int | Primeiro número (referência) |
| b | int | Segundo número (referência) |
| c | int | Resultado da soma (a + b) |

## Benefícios do CSV-MP

- **Eficiência**: Formato binário/texto híbrido otimizado
- **Validação**: Tipos de dados validados automaticamente
- **Multi-linha**: Suporte nativo a processamento em lote
- **Metadados**: Manifesto inclui versão, autor e descrição
- **Interoperabilidade**: Implementações em Python, TypeScript e C#
