# CSV-MP (CSV MultiPart Protocol)

Implementação de referência do protocolo CSV-MP v0.2.0-alpha em três linguagens: TypeScript, Python e C#.

## Visão Geral

CSV-MP é um protocolo de serialização de dados que combina:
- Legibilidade humana (formato texto, abre no Excel)
- Múltiplas tabelas em um único arquivo
- Referências nativas entre tabelas
- Tipagem explícita no cabeçalho
- Assets binários (imagens, PDFs) no mesmo arquivo
- Validação integrada de schema e integridade

## Estrutura do Projeto

```
csv-mp/
├── typescript/     # Implementação em TypeScript
│   ├── src/
│   ├── examples/
│   └── tests/
├── python/         # Implementação em Python
│   ├── src/
│   ├── examples/
│   └── tests/
└── csharp/         # Implementação em C#
    ├── src/
    ├── examples/
    └── tests/
```

## Documentação

Veja a documentação completa em [DOCUMENTACAO.md](./DOCUMENTACAO.md)

## Licença

CC0 1.0 (Domínio Público)

## Versão

0.2.0-alpha
