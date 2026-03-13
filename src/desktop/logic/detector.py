import re

# RFC 5322 Compliant Email Regex (Simplified but robust)
EMAIL_REGEX = r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"

# URL Regex with support for www. and optional protocol
URL_REGEX = r"(?i)\b(?:https?://|www\.)[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"

# Other Patterns
PATTERNS = {
    "Emails": EMAIL_REGEX,
    "URLs": URL_REGEX,
    "Teléfonos PY": r'\b(09\d{8}|09\d{2}\s\d{3}\s\d{3})\b',
    "IP Addresses": r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
    "Dates": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
    "Cédulas PY": r'\b\d{6,8}\b',
    "Precios Gs": r'\b\d{1,3}(\.?\d{3})*\s?(Gs|GS|gs)\b',
    "SQL_PARAM": r"(?i)(\%27|'|\-\-|\#|\%23|UNION\s+SELECT|SELECT\s+.*FROM|OR\s+1=1|AND\s+1=1)",
    "HTML": r"<\s*(\w+)[^>]*>.*?<\s*/\s*\1\s*>|<\s*\w+[^>]*\s*/?>",
}

def detectar_input(data: str) -> str:
    """
    RS Brain: Classify input into URL, HTML, EMAIL, IP, SQL_PARAM or PLAIN_TEXT.
    Prioridad: URL > HTML > SQL > EMAIL > IP > TEXTO
    """
    if not data:
        return "EMPTY"
    
    data = data.strip()
    
    # 1. URL (Prioridad máxima) - Incluye www.
    if re.search(f"^{URL_REGEX}$", data, re.I):
        return "URL"
        
    # 2. HTML (Prioridad alta)
    if re.search(PATTERNS["HTML"], data, re.S | re.I):
        return "HTML"
        
    # 3. SQL_PARAM
    if re.search(PATTERNS["SQL_PARAM"], data, re.I):
        return "SQL_PARAM"
        
    # 4. EMAIL (RFC 5322 compatible)
    if re.search(f"^{EMAIL_REGEX}$", data, re.I):
        return "EMAIL"
        
    # 5. IP
    if re.search(f"^{PATTERNS['IP Addresses']}$", data, re.I):
        return "IP"
        
    return "PLAIN_TEXT"
