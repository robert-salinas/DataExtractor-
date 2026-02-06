from src.core.extractor import DataExtractor

def main():
    # Inicializar el extractor
    extractor = DataExtractor()
    
    # Extraer datos de Hacker News (HTML simple)
    print("Extrayendo datos de Hacker News...")
    url = "https://news.ycombinator.com/"
    
    try:
        # En una implementación real, esto usaría selectores inteligentes
        # Por ahora, extrae el HTML crudo
        data = extractor.extract(url, type="html")
        print(f"Extracción exitosa. Longitud del contenido: {len(data)} caracteres.")
        print("\nPrimeros 200 caracteres del contenido:")
        print(data[:200])
        
    except Exception as e:
        print(f"Error durante la extracción: {e}")

if __name__ == "__main__":
    main()
