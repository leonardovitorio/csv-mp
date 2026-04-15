"""
CSV-MP Python Serializer
Version: 0.2.0-alpha
License: CC0 1.0 (Public Domain)
"""

import io
from typing import List, Dict, Any, Optional, cast
import sys
import os

# Add src to path for direct imports
sys.path.insert(0, os.path.dirname(__file__))

from csvmp_types import (
    TablePart,
    BinaryPart,
    TextPart,
    ColumnDef,
    ManifestEntry
)


class CsvMpSerializer:
    def __init__(self):
        self.buffer_size = 30 * 1024 * 1024  # 30MB buffer principal

    def serialize(self, document: Dict[str, Any], force_full_mode: bool = False) -> str:
        """
        Serializa o documento CSV-MP.
        
        Args:
            document: Documento CSV-MP com tables, binary_parts, text_parts
            force_full_mode: Se True, sempre usa modo completo com manifesto
        
        Usa o modo 'Lite' (sem manifesto) se:
        - Houver apenas 1 parte.
        - A parte for do tipo TablePart.
        - Todos os campos forem tipos primitivos.
        - force_full_mode for False
        """
        output = io.StringIO()
        tables = document.get('tables', [])
        
        # Verificação para Modo Lite
        is_lite_mode = False
        if not force_full_mode:
            if len(tables) == 1 and len(document.get('binary_parts', [])) == 0 and len(document.get('text_parts', [])) == 0:
                table = tables[0]
                # Verifica se todos os campos são primitivos
                primitive_types = {'int', 'float', 'string', 'bool', 'date', 'number', 'long', 'boolean'}
                if all(col.base_type.value in primitive_types or col.base_type.name.lower() in primitive_types 
                       for col in table.columns):
                    is_lite_mode = True

        if is_lite_mode:
            # MODO LITE: Sem manifesto, apenas schema e dados
            self._write_table_part(output, tables[0])
        else:
            # MODO PADRÃO: Com manifesto completo
            output.write("# CSV-MP v0.2 Manifesto\n")
            # Escreve linha do manifesto
            manifest_fields = [
                "type:string", "description:string", "count:number", 
                "contentType:string", "author:string", "version:string", "hash:string"
            ]
            output.write("&|" + "|".join(manifest_fields) + "\n")
            
            # Linha de dados do manifesto
            total_parts = len(tables) + len(document.get('binary_parts', [])) + len(document.get('text_parts', []))
            doc_type = document.get('type', 'CsvMpDocument')
            doc_desc = document.get('description', 'CSV-MP Document')
            output.write(f"0|{doc_type}|{doc_desc}|{total_parts}|text/csv|csv-mp|1.0|\n")
            output.write("\n") # Separador
            
            # Escreve cada parte
            all_parts = []
            all_parts.extend([('table', t) for t in tables])
            all_parts.extend([('text', t) for t in document.get('text_parts', [])])
            all_parts.extend([('binary', t) for t in document.get('binary_parts', [])])
            
            for i, (ptype, part) in enumerate(all_parts):
                if ptype == 'table':
                    self._write_table_part(output, part)
                elif ptype == 'text':
                    self._write_text_part(output, part)
                elif ptype == 'binary':
                    self._write_binary_part(output, part)
                
                if i < len(all_parts) - 1:
                    output.write("\n") # Separador entre partes

        return output.getvalue()

    def _write_table_part(self, output: io.StringIO, part: TablePart):
        # Escreve Schema (adiciona coluna de índice)
        schema_def = "idx:int," + ",".join([f"{f.name}:{f.base_type.name.lower()}" for f in part.columns])
        output.write(f"&:{schema_def}\n")
        
        # Escreve Dados (incluindo índice como primeira coluna)
        for row in part.rows:
            values = []
            # Se a row já tem índice (primeiro elemento é int), usa ela completa
            # Caso contrário, adiciona índice sequencial
            if len(row) == len(part.columns) + 1 and isinstance(row[0], int):
                # Row já tem índice
                for val in row:
                    if val is None:
                        values.append("")
                    else:
                        values.append(str(val))
            else:
                # Adiciona índice
                values.append(str(len(values)))
                for val in row:
                    if val is None:
                        values.append("")
                    else:
                        values.append(str(val))
            output.write(",".join(values) + "\n")

    def _write_text_part(self, output: io.StringIO, part: TextPart):
        output.write(f"[TEXT:{part.name}|{part.mime_type}]\n")
        output.write(part.content)
        output.write(f"\n[END:{part.name}]")

    def _write_binary_part(self, output: io.StringIO, part: BinaryPart):
        import base64
        b64_data = base64.b64encode(part.data).decode('utf-8')
        output.write(f"[PART:{part.name}|{part.mime_type}|{len(part.data)}]\n")
        output.write(b64_data)
        output.write(f"\n[END:{part.name}]")
