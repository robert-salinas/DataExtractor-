import base64
import re
from typing import List

def es_texto_valido(texto: str) -> bool:
    """
    Validación de entropía y legibilidad para descartar decodificaciones basura.
    """
    if not texto: return False
    
    # 1. Descartar si tiene demasiados caracteres no imprimibles (>30%)
    non_printable = [c for c in texto if not c.isprintable() and not c.isspace()]
    if len(non_printable) / len(texto) > 0.3:
        return False
        
    # 2. Descartar si tiene demasiados espacios (>40%) - Común en decodificaciones erróneas
    spaces = [c for c in texto if c.isspace()]
    if len(spaces) / len(texto) > 0.4:
        return False
        
    # 3. Mínima longitud útil
    if len(texto.strip()) < 4:
        return False
        
    return True

def decodificar(texto: str) -> List[str]:
    """
    Deobfuscation Engine: Robust extraction from Base64, Hex, JS Array Joins and CharCodes.
    """
    resultados = set() # Usar set para evitar duplicados internos
    
    # 1. Base64 Robust (Min 12 chars to avoid false positives)
    for match in re.findall(r'[A-Za-z0-9+/]{12,}={0,2}', texto):
        try:
            decoded = base64.b64decode(match).decode('utf-8', errors='ignore')
            if es_texto_valido(decoded):
                resultados.add(decoded.strip())
        except:
            pass
    
    # 2. Hex (Robust check for \x or pure hex strings)
    for match in re.findall(r'(?:\\x[0-9a-fA-F]{2}){4,}', texto):
        try:
            limpio = bytes.fromhex(match.replace('\\x', '')).decode('utf-8', errors='ignore')
            if es_texto_valido(limpio):
                resultados.add(limpio.strip())
        except:
            pass

    # 3. JS Array Join (Robust parser for escape chars)
    # Matches: ["a","b","c"] or ['a','b','c'] followed by .join("")
    array_matches = re.findall(r'\[\s*(?:["\'](?:\\.|[^"\'])+["\']\s*,\s*)*["\'](?:\\.|[^"\'])+["\']\s*\]\.join\(\s*["\']{2}\s*\)', texto)
    for match in array_matches:
        try:
            # Extract content between quotes, handling escapes
            parts = re.findall(r'["\']((?:\\.|[^"\'])+)["\']', match.split('.join')[0])
            decoded = "".join(parts).encode().decode('unicode_escape') # Handle \x, \u, etc.
            if es_texto_valido(decoded):
                resultados.add(decoded.strip())
        except:
            pass

    # 4. String.fromCharCode(99, 111, 110)
    char_code_matches = re.findall(r'String\.fromCharCode\s*\(\s*([\d\s,]+)\s*\)', texto)
    for match in char_code_matches:
        try:
            codes = [int(c.strip()) for c in match.split(',')]
            decoded = "".join(chr(c) for c in codes)
            if es_texto_valido(decoded):
                resultados.add(decoded.strip())
        except:
            pass
    
    return list(resultados)
