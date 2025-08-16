from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, validator
import numpy as np
from PIL import Image
import io
import json
import threading
import tempfile
import os
from typing import List, Dict, Any, Optional

app = FastAPI(title="Paddy Disease API with CRUD", version="1.0.0")

# Mount static files for serving the web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# File paths
DISEASE_INFO_FILE = "disease_info.json"
DISEASE_MEDICINES_FILE = "disease_medicines.json"

# Thread-level lock for atomic file operations
_file_lock = threading.Lock()

# Pydantic model for Medicine validation
class Medicine(BaseModel):
    name: str
    brand: Optional[str] = None
    type: Optional[str] = None
    active_ingredient: Optional[str] = None
    pack_size: Optional[str] = None
    price: Optional[str] = None
    image_url: Optional[str] = None
    application_rate: Optional[str] = None
    method: Optional[str] = None
    frequency: Optional[str] = None
    availability: Optional[str] = None
    priority: Optional[int] = Field(default=999, ge=0)
    note: Optional[str] = None

    @validator("priority")
    def priority_non_negative(cls, v):
        if v is None:
            return 999
        if v < 0:
            raise ValueError("priority must be >= 0")
        return v

# Pydantic model for Disease Info validation
class DiseaseInfo(BaseModel):
    disease_name: str
    caused_by: Optional[str] = None
    description: str
    symptoms: Optional[List[str]] = []
    factors: Optional[List[str]] = []
    prevention: Optional[List[str]] = []
    care: Optional[List[str]] = []  # For normal/healthy plants
    treatment: Optional[str] = None
    note: Optional[str] = None

def _read_medicines_json():
    """Thread-safe read of medicines JSON file"""
    with _file_lock:
        try:
            with open(DISEASE_MEDICINES_FILE, "r", encoding="utf8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Malformed JSON in medicines file")

def _write_medicines_json(data: dict):
    """Safe write: write to temp + atomic replace"""
    with _file_lock:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=os.path.dirname(DISEASE_MEDICINES_FILE))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf8") as tmp:
                json.dump(data, tmp, indent=4, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, DISEASE_MEDICINES_FILE)
        except Exception as e:
            # Clean up temp file if something goes wrong
            try:
                os.unlink(tmp_path)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to write medicines file: {str(e)}")

# Load disease info and medicines data
try:
    with open(DISEASE_INFO_FILE, "r") as f:
        disease_info = json.load(f)
except Exception as e:
    print(f"Warning: Could not load disease info: {e}")
    disease_info = {}

try:
    with open(DISEASE_MEDICINES_FILE, "r") as f:
        disease_medicines = json.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load medicine data from {DISEASE_MEDICINES_FILE}: {e}")

# Basic endpoints
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "CRUD Service is up and running"}

@app.get("/disease-info", tags=["Disease Info"])
def list_diseases() -> Dict[str, List[str]]:
    return {"available_diseases": sorted(list(disease_info.keys()))}

@app.get("/disease-info/{name}", tags=["Disease Info"])
def get_disease_info(name: str = Path(..., description="Disease identifier (e.g., 'blast', 'bacterial_leaf_blight')")) -> Dict[str, Any]:
    key = name.strip().lower()
    info = disease_info.get(key)
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{name}' not found. Available options: {list(disease_info.keys())}"
        )
    return {"disease": key, "info": info}

@app.get("/disease-medicines", tags=["Treatment"])
def get_disease_medicines(
    name: str = Query(..., description="Disease identifier to get recommended medicines (e.g., 'blast')")
) -> Dict[str, Any]:
    key = name.strip().lower()
    medicines = disease_medicines.get(key)
    if not medicines:
        raise HTTPException(
            status_code=404,
            detail=f"No medicine information found for '{name}'. Available diseases: {list(disease_medicines.keys())}"
        )
    sorted_medicines = sorted(medicines, key=lambda m: m.get("priority", 999))
    return {"name": key, "recommended_medicines": sorted_medicines}

# CRUD Endpoints for Medicines Management

@app.get("/medicines", tags=["Medicines CRUD"])
def list_all_diseases_crud():
    """List all disease keys in medicines file for CRUD operations"""
    data = _read_medicines_json()
    return {"available_diseases": sorted(data.keys())}

@app.get("/medicines/{disease}", tags=["Medicines CRUD"])
def list_medicines_crud(disease: str = Path(..., description="Disease key e.g. 'blast'")):
    """List all medicines for a specific disease"""
    key = disease.strip().lower()
    data = _read_medicines_json()
    if key not in data:
        raise HTTPException(
            status_code=404, 
            detail=f"No medicines found for disease '{key}'. Available diseases: {list(data.keys())}"
        )
    # Sort by priority ascending
    medicines = sorted(data[key], key=lambda m: m.get("priority", 999))
    return {"disease": key, "medicines": medicines}

@app.get("/medicines/{disease}/{idx}", tags=["Medicines CRUD"])
def get_medicine_crud(
    disease: str = Path(..., description="Disease key"),
    idx: int = Path(..., ge=0, description="0-based index of medicine item")
):
    """Get a specific medicine by disease and index"""
    key = disease.strip().lower()
    data = _read_medicines_json()
    if key not in data:
        raise HTTPException(status_code=404, detail=f"Disease '{key}' not found")
    if idx >= len(data[key]):
        raise HTTPException(status_code=404, detail=f"Medicine index {idx} not found in '{key}'")
    return {"disease": key, "index": idx, "medicine": data[key][idx]}

@app.post("/medicines/{disease}", status_code=201, tags=["Medicines CRUD"])
def create_medicine(
    disease: str = Path(..., description="Disease key"),
    medicine: Medicine = ...
):
    """Add a new medicine to a disease category"""
    key = disease.strip().lower()
    data = _read_medicines_json()
    
    # Create disease category if it doesn't exist
    if key not in data:
        data[key] = []
    
    # Check for duplicate name (optional - you can remove this if duplicates are allowed)
    existing_names = [m.get("name", "").lower() for m in data[key]]
    if medicine.name.lower() in existing_names:
        raise HTTPException(
            status_code=409, 
            detail=f"Medicine '{medicine.name}' already exists under '{key}'"
        )
    
    # Add the new medicine
    data[key].append(medicine.dict())
    _write_medicines_json(data)
    
    return {"disease": key, "created": medicine, "message": "Medicine added successfully"}

@app.put("/medicines/{disease}/{idx}", tags=["Medicines CRUD"])
def update_medicine(
    disease: str = Path(..., description="Disease key"),
    idx: int = Path(..., ge=0, description="0-based index of medicine to update"),
    medicine: Medicine = ...
):
    """Update an existing medicine"""
    key = disease.strip().lower()
    data = _read_medicines_json()
    
    if key not in data:
        raise HTTPException(status_code=404, detail=f"Disease '{key}' not found")
    if idx >= len(data[key]):
        raise HTTPException(status_code=404, detail=f"Medicine index {idx} not found in '{key}'")
    
    # Update the medicine
    data[key][idx] = medicine.dict()
    _write_medicines_json(data)
    
    return {"disease": key, "index": idx, "updated": medicine, "message": "Medicine updated successfully"}

@app.delete("/medicines/{disease}/{idx}", tags=["Medicines CRUD"])
def delete_medicine(
    disease: str = Path(..., description="Disease key"),
    idx: int = Path(..., ge=0, description="0-based index of medicine to delete")
):
    """Delete a medicine from a disease category"""
    key = disease.strip().lower()
    data = _read_medicines_json()
    
    if key not in data:
        raise HTTPException(status_code=404, detail=f"Disease '{key}' not found")
    if idx >= len(data[key]):
        raise HTTPException(status_code=404, detail=f"Medicine index {idx} not found in '{key}'")
    
    # Remove the medicine
    removed_medicine = data[key].pop(idx)
    
    # Optional: Remove empty disease categories (uncomment if desired)
    # if not data[key]:
    #     data.pop(key)
    
    _write_medicines_json(data)
    
    return {
        "disease": key, 
        "index": idx, 
        "deleted": removed_medicine, 
        "message": "Medicine deleted successfully"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
