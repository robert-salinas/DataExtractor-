import re

PATRONES_VALIDOS = {
    "Emails":    r'^[\w\.-]+@[\w\.-]+\.\w+$',
    "URLs":      r'^https?://.+',
    "Teléfonos PY": r'^\+?[\d\s\-\(\)]{7,15}$',
    "Cédulas PY":    r'^\d{6,8}$',
    "IP Addresses":       r'^\d{1,3}(\.\d{1,3}){3}$',
}

def es_dato_valido(valor: str, tipo: str) -> bool:
    """
    Data Validation: Avoid JS/Junk in DB.
    """
    if not valor or len(valor.strip()) < 3:
        return False
    
    valor_limpio = valor.strip()
    
    if tipo in PATRONES_VALIDOS:
        if not bool(re.match(PATRONES_VALIDOS[tipo], valor_limpio)):
            return False
            
    # Si no tiene patrón conocido, al menos que no sea JS
    sospechoso = ["function(", "=>", "var ", "const ", "{}", "undefined", "document.", "window."]
    if any(s in valor_limpio for s in sospechoso):
        return False
        
    return True
