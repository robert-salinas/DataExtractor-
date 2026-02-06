import typer
from typing import Optional
from src.core.extractor import DataExtractor
import json

app = typer.Typer(help="DataExtractor CLI - Herramienta potente de extracción de datos.")
extractor = DataExtractor()

@app.command()
def extract(
    source: str = typer.Argument(..., help="La fuente de datos (URL, archivo, etc.)"),
    type: str = typer.Option("html", "--type", "-t", help="Tipo de fuente (html, api, spa, pdf, database)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Archivo de salida (opcional)")
):
    """
    Extrae datos de una fuente específica.
    """
    typer.echo(f"Extrayendo datos de {source} (tipo: {type})...")
    try:
        data = extractor.extract(source, type=type)
        
        if output:
            with open(output, "w", encoding="utf-8") as f:
                if isinstance(data, (dict, list)):
                    json.dump(data, f, indent=4)
                else:
                    f.write(str(data))
            typer.echo(f"Datos guardados en {output}")
        else:
            typer.echo(data)
            
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
