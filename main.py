

from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from auth import get_api_key
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import json
import threading
import tempfile
import os
from typing import List, Dict, Any, Optional


app = FastAPI()

# Mount static files for serving the web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define allowed origins for CORS
# In a production environment, this should be restricted to your frontend's domain
origins = [
    "http://localhost",
    "http://localhost:8002",
    "https://your-domain.com",  # Placeholder for your production domain
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/api_data.html")


MODEL_PATH = "mymodel"
LABELS_FILE = "labels.txt"
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
    symptoms: List[str]
    factors: Optional[List[str]] = None
    prevention: Optional[List[str]] = None
    treatment: Optional[str] = None
    care: Optional[List[str]] = None
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


def _read_disease_info_json():
    """Thread-safe read of disease info JSON file"""
    with _file_lock:
        try:
            with open(DISEASE_INFO_FILE, "r", encoding="utf8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Malformed JSON in disease info file")

def _write_disease_info_json(data: dict):
    """Safe write: write to temp + atomic replace"""
    with _file_lock:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".tmp", dir=os.path.dirname(DISEASE_INFO_FILE))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf8") as tmp:
                json.dump(data, tmp, indent=4, ensure_ascii=False)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_path, DISEASE_INFO_FILE)
        except Exception as e:
            # Clean up temp file if something goes wrong
            try:
                os.unlink(tmp_path)
            except:
                pass
            raise HTTPException(status_code=500, detail=f"Failed to write disease info file: {str(e)}")


try:
    model = tf.keras.layers.TFSMLayer(MODEL_PATH, call_endpoint='serving_default')
except Exception as e:
    raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")

try:
    with open(LABELS_FILE, "r") as f:
        class_names = [line.strip().split(maxsplit=1)[-1] for line in f if line.strip()]
except Exception as e:
    raise RuntimeError(f"Failed to load labels from {LABELS_FILE}: {e}")

try:
    with open(DISEASE_INFO_FILE, "r") as f:
        disease_info = json.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load disease info from {DISEASE_INFO_FILE}: {e}")

try:
    with open(DISEASE_MEDICINES_FILE, "r") as f:
        disease_medicines = json.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load medicine data from {DISEASE_MEDICINES_FILE}: {e}")




@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Service is up and running"}



@app.get("/classes", tags=["Model"])
def get_classes() -> Dict[str, List[str]]:
    return {"classes": class_names}



@app.get("/info", tags=["Model"])
def model_info() -> Dict[str, Any]:
    try:
        input_shape = model.input_shape
        output_shape = model.output_shape
        return {
            "input_shape": input_shape,
            "output_shape": output_shape,
            "num_classes": len(class_names),
            "model_loaded": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving model info: {str(e)}")



@app.post("/predict", tags=["Prediction"])
async def predict(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        image = image.resize((224, 224))
        image_array = np.array(image, dtype=np.float32) / 255.0
        image_array = np.expand_dims(image_array, axis=0)
        predictions = model.predict(image_array, verbose=0)[0]
        top_class_idx = int(np.argmax(predictions))
        confidence = float(predictions[top_class_idx])
        predicted_class = class_names[top_class_idx]
        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "all_confidences": {
                cls_name: round(float(conf), 4)
                for cls_name, conf in zip(class_names, predictions)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")



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
    medicine: Medicine = ...,
    api_key: str = Depends(get_api_key)
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
    medicine: Medicine = ...,
    api_key: str = Depends(get_api_key)
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
    idx: int = Path(..., ge=0, description="0-based index of medicine to delete"),
    api_key: str = Depends(get_api_key)
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


# CRUD Endpoints for Disease Info Management

@app.get("/crud/disease-info", tags=["Disease Info CRUD"])
def list_all_diseases_info_crud():
    """List all disease keys from the disease info file"""
    data = _read_disease_info_json()
    return {"available_diseases": sorted(data.keys())}


@app.get("/crud/disease-info/{disease_key}", tags=["Disease Info CRUD"])
def get_disease_info_crud(disease_key: str = Path(..., description="Disease key e.g. 'blast'")):
    """Fetch the full data object for a single disease"""
    key = disease_key.strip().lower()
    data = _read_disease_info_json()
    if key not in data:
        raise HTTPException(
            status_code=404, 
            detail=f"Disease info for '{key}' not found. Available diseases: {list(data.keys())}"
        )
    return {"disease_key": key, "data": data[key]}


@app.put("/crud/disease-info/{disease_key}", tags=["Disease Info CRUD"])
def update_disease_info_crud(
    disease_key: str = Path(..., description="Disease key to update"),
    info: DiseaseInfo = ...,
    api_key: str = Depends(get_api_key)
):
    """Update the information for a specific disease"""
    key = disease_key.strip().lower()
    data = _read_disease_info_json()
    
    if key not in data:
        raise HTTPException(status_code=404, detail=f"Disease '{key}' not found")
    
    # Update the disease info
    data[key] = info.dict(exclude_none=True)
    _write_disease_info_json(data)
    
    return {"disease_key": key, "updated": info, "message": "Disease info updated successfully"}
