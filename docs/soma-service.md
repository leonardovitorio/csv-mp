# Serviço de Soma

## Visão Geral
Serviço responsável por realizar a soma de dois números inteiros.

## Endpoint

### POST /api/soma

Soma dois números inteiros e retorna o resultado.

#### Request Body

```json
{
  "a": 10,
  "b": 20
}
```

#### Schema do Request (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SomaRequest",
  "type": "object",
  "properties": {
    "a": {
      "type": "integer",
      "description": "Primeiro número inteiro"
    },
    "b": {
      "type": "integer",
      "description": "Segundo número inteiro"
    }
  },
  "required": ["a", "b"],
  "additionalProperties": false
}
```

#### Response Body (Sucesso - 200 OK)

```json
{
  "c": 30
}
```

#### Schema do Response (JSON Schema)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SomaResponse",
  "type": "object",
  "properties": {
    "c": {
      "type": "integer",
      "description": "Resultado da soma de a + b"
    }
  },
  "required": ["c"],
  "additionalProperties": false
}
```

#### Códigos de Resposta

| Código | Descrição |
|--------|-----------|
| 200    | Sucesso. A soma foi realizada com sucesso. |
| 400    | Requisição inválida. Os parâmetros `a` ou `b` não são inteiros ou estão ausentes. |
| 500    | Erro interno do servidor. |

#### Exemplo de Uso

**Request:**
```bash
curl -X POST http://localhost:8080/api/soma \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 20}'
```

**Response:**
```json
{
  "c": 30
}
```

---

## Definição OpenAPI (Swagger)

```yaml
openapi: 3.0.0
info:
  title: API de Soma
  version: 1.0.0
  description: API para soma de dois números inteiros

paths:
  /api/soma:
    post:
      summary: Soma dois números inteiros
      operationId: somar
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SomaRequest'
      responses:
        '200':
          description: Sucesso na operação
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SomaResponse'
        '400':
          description: Requisição inválida
        '500':
          description: Erro interno do servidor

components:
  schemas:
    SomaRequest:
      type: object
      properties:
        a:
          type: integer
          description: Primeiro número inteiro
        b:
          type: integer
          description: Segundo número inteiro
      required:
        - a
        - b
      additionalProperties: false

    SomaResponse:
      type: object
      properties:
        c:
          type: integer
          description: Resultado da soma de a + b
      required:
        - c
      additionalProperties: false
```
