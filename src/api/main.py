from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from src.core.extractor import DataExtractor

app = FastAPI(
    title="DataExtractor API",
    description="API para la extracción potente y flexible de datos de múltiples fuentes.",
    version="0.1.0",
)

extractor = DataExtractor()


class ExtractRequest(BaseModel):
    source: str
    type: str = "html"
    params: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    return {"message": "Welcome to DataExtractor API", "status": "running"}


@app.post("/extract")
async def extract_data(request: ExtractRequest):
    try:
        data = extractor.extract(
            request.source, type=request.type, **(request.params or {})
        )
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
