from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 

import os
import json
from src.generatePdf import generate_pdf

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
os.makedirs(PUBLIC_DIR, exist_ok=True)
app.mount("/public", StaticFiles(directory=os.path.join(BASE_DIR, "public")), name="public")

app.add_middleware(
    CORSMiddleware,
    allow_methods=["GET", "POST"], 
)

@app.post("/generate-pdf")
async def generate_labels(request: Request):
    try:
        body = await request.json()
        name_typed = body.get("nameTyped", "").strip()
        order_id = body.get("orderId", "")
        
        if not name_typed:
            return {"error": "El campo 'nameTyped' es requerido"}
        
        # Generar ambas versiones (400ml y 500ml)
        results = []
        base_url = str(request.base_url)
        
        for label_type in ["400", "500"]:
            result = generate_pdf(BASE_DIR, name_typed, label_type, label_type)
            
            if result["success"]:
                results.append({
                    "type": f"{label_type}ml",
                    "pdf_url": f"{base_url}{result['pdf_url'].lstrip('/')}",
                    "status": "success"
                })
            else:
                results.append({
                    "type": f"{label_type}ml",
                    "error": result.get("error", "Error desconocido"),
                    "status": "failed"
                })
        
        return {
            "orderId": order_id,
            "results": results,
            "success": all(r["status"] == "success" for r in results)
        }
        
    except Exception as e:
        print(f"Error general en la función: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
        