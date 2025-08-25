

from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
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
from image_processor import process_image_for_model, validate_and_process_image, ImageProcessor


app = FastAPI()

# Mount static files for serving the web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

# Define allowed origins for CORS
# In a production environment, this should be restricted to your frontend's domain
# For example: origins = ["https://your-frontend-domain.com"]
# Configure allowed CORS origins via environment variable for production
origins_env = os.environ.get("ALLOWED_ORIGINS")
if origins_env:
    origins = [o.strip() for o in origins_env.split(",") if o.strip()]
else:
    origins = ["*"]  # Keep "*" for development, but change for production

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False, response_class=HTMLResponse)
async def root():
    return '<div class="hub-container"><h1>KODEGAS</h1></div>'


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


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
    import os

    # Allow skipping heavy model load during tests or CI environments
    if os.environ.get('SKIP_MODEL_LOAD') not in ('1', 'true', 'True'):
        try:
            model = tf.keras.layers.TFSMLayer(MODEL_PATH, call_endpoint='serving_default')
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")
    else:
        model = None
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
async def predict(
    file: UploadFile = File(...),
    maintain_aspect_ratio: bool = Query(True, description="Maintain aspect ratio during resizing"),
    max_size_mb: int = Query(10, description="Maximum file size in MB", ge=1, le=100),
    compression_quality: int = Query(85, description="JPEG compression quality (1-100)", ge=1, le=100),
    enhance_features: bool = Query(True, description="Apply rice disease-specific image enhancements for better prediction")
) -> Dict[str, Any]:
    """
    Predict rice disease from uploaded image.
    
    Supports large image uploads with automatic compression and resizing.
    Images are processed to 224x224 pixels for model input.
    
    When enhance_features=True, applies specialized preprocessing for rice disease detection:
    - Green channel enhancement (rice diseases often manifest in green channel)
    - Edge enhancement (improves detection of lesion boundaries)
    - Contrast/sharpness optimization (makes disease features more prominent)
    - Adaptive brightness adjustment (compensates for under/overexposed images)
    - Noise reduction (removes sensor noise while preserving disease features)
    """
    try:
        # Process the uploaded image with rice-specific enhancements
        image_array, metadata = await validate_and_process_image(
            file=file,
            max_size_mb=max_size_mb,
            target_size=(224, 224),
            compression_quality=compression_quality,
            enhance_features=enhance_features
        )
        
        # Make prediction
        output_dict = model(image_array)
        predictions = next(iter(output_dict.values())).numpy()[0]
        top_class_idx = int(np.argmax(predictions))
        confidence = float(predictions[top_class_idx])
        predicted_class = class_names[top_class_idx]
        
        # Get disease information if available
        disease_details = disease_info.get(predicted_class, {})
        
        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "all_confidences": {
                cls_name: round(float(conf), 4)
                for cls_name, conf in zip(class_names, predictions)
            },
            "disease_info": {
                "name": predicted_class,
                "description": disease_details.get("description", "No description available"),
                "symptoms": disease_details.get("symptoms", []),
                "treatment": disease_details.get("treatment", [])
            } if predicted_class != "normal" else {"name": "normal", "description": "No disease detected"},
            "image_metadata": metadata,
            "prediction_quality": "rice_optimized" if enhance_features else "standard"
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like file size too large)
        raise
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
    
    # Reorder priorities and add the new medicine
    medicines = data.get(key, [])
    _reorder_medicines(medicines, medicine.dict())
    data[key] = sorted(medicines, key=lambda m: m.get("priority", 999))
    
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
    
    # Reorder priorities and update the medicine
    medicines = data.get(key, [])
    _reorder_medicines(medicines, medicine.dict(), original_index=idx)
    data[key] = sorted(medicines, key=lambda m: m.get("priority", 999))

    _write_medicines_json(data)
    
    return {"disease": key, "updated": medicine, "message": "Medicine updated successfully"}


def _reorder_medicines(medicines: List[Dict[str, Any]], new_medicine: Dict[str, Any], original_index: Optional[int] = None):
    """
    Reorders medicine priorities to ensure uniqueness and correct sorting.
    - If a new medicine is added with a priority that already exists,
      it shifts down the priorities of subsequent items.
    - If a medicine's priority is updated, it adjusts the list accordingly.
    """
    new_priority = new_medicine.get("priority", 999)
    
    # If updating, remove the old version of the medicine first
    if original_index is not None and 0 <= original_index < len(medicines):
        medicines.pop(original_index)

    # Check if the new priority already exists
    is_priority_taken = any(m.get("priority") == new_priority for m in medicines)

    if is_priority_taken:
        # Shift priorities for items with the same or higher priority
        for med in medicines:
            if med.get("priority", 999) >= new_priority:
                med["priority"] = med.get("priority", 999) + 1
    
    # Add the new or updated medicine to the list
    medicines.append(new_medicine)
    
    # Normalize priorities to be sequential if there are gaps
    medicines.sort(key=lambda m: m.get("priority", 999))
    for i, med in enumerate(medicines):
        med["priority"] = i + 1 # Re-assign priorities starting from 1


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
    
    # Re-order the remaining medicines to ensure sequential priorities
    remaining_medicines = data[key]
    remaining_medicines.sort(key=lambda m: m.get("priority", 999))
    for i, med in enumerate(remaining_medicines):
        med["priority"] = i + 1
    data[key] = remaining_medicines

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


# Image Processing Endpoints

@app.post("/process-image", tags=["Image Processing"])
async def process_image_endpoint(
    file: UploadFile = File(...),
    target_size: str = Query("224x224", description="Target size in format 'widthxheight'"),
    maintain_aspect_ratio: bool = Query(True, description="Maintain aspect ratio during resizing"),
    quality: int = Query(85, description="JPEG quality (1-100)", ge=1, le=100),
    output_format: str = Query("JPEG", description="Output format: JPEG, PNG, or WEBP")
) -> Dict[str, Any]:
    """
    Process and compress an image without making predictions.
    Useful for testing image processing capabilities.
    """
    try:
        # Parse target size
        try:
            width, height = map(int, target_size.split('x'))
            target_size_tuple = (width, height)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid target_size format. Use 'widthxheight' (e.g., '224x224')")
        
        # Process image
        processor = ImageProcessor(target_size=target_size_tuple, quality=quality)
        image_array, metadata = await processor.process_uploaded_image(
            file, 
            maintain_aspect_ratio=maintain_aspect_ratio
        )
        
        # Get the processed image for compression
        processed_image = Image.fromarray((image_array[0] * 255).astype(np.uint8))
        
        # Compress the image
        compressed_data = processor.compress_image(processed_image, output_format, quality)
        
        # Calculate compression stats
        original_size = metadata.get("file_size_bytes", 0)
        compression_stats = processor.get_compression_stats(original_size, len(compressed_data))
        
        return {
            "success": True,
            "original_metadata": metadata,
            "target_size": target_size_tuple,
            "output_format": output_format,
            "compression_stats": compression_stats,
            "processed_image_size": image_array.shape,
            "message": f"Image processed successfully to {target_size} pixels"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")


@app.get("/image-processing-info", tags=["Image Processing"])
def get_image_processing_info() -> Dict[str, Any]:
    """
    Get information about image processing capabilities and limits.
    """
    return {
        "supported_formats": ["JPEG", "PNG", "WEBP", "BMP", "TIFF"],
        "default_target_size": (224, 224),
        "max_file_size_mb": 50,
        "default_quality": 85,
        "features": [
            "Large image upload support (up to 50MB)",
            "Automatic compression and resizing",
            "Aspect ratio preservation",
            "Multiple output formats",
            "Image enhancement for better model performance",
            "Background padding for non-square images"
        ],
        "model_requirements": {
            "input_size": "224x224 pixels",
            "color_format": "RGB",
            "normalization": "Pixel values normalized to [0, 1]",
            "batch_dimension": "Single image with batch dimension"
        }
    }
