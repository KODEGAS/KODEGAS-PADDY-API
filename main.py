

from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import json
from typing import List, Dict, Any


app = FastAPI(
    title="Rice Disease Detection API",
    description="AI-powered API to detect rice diseases from images. Returns predictions, information, and treatments.",
    version="1.0.0",
    contact={"name": "KODEGAS AI Team", "email": "kavix@yahoo.com"},
    license_info={"name": "MIT License"},
)


# For production, set allowed origins appropriately
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




MODEL_PATH = "mymodel"
LABELS_FILE = "labels.txt"
DISEASE_INFO_FILE = "disease_info.json"
DISEASE_MEDICINES_FILE = "disease_medicines.json"




try:
    model = tf.keras.models.load_model(MODEL_PATH)
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

# Root endpoint for API info
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Rice Disease Detection API. See /docs for usage.",
        "docs_url": "/docs",
        "health_url": "/health"
    }


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
    
    # Check file size (limit to 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB, got {len(contents) // (1024*1024)}MB"
        )
    
    try:
        image = Image.open(io.BytesIO(contents))
        
        # Debug info about original image
        original_size = image.size
        original_mode = image.mode
        
        # Handle EXIF orientation (common in camera photos)
        try:
            from PIL.ExifTags import ORIENTATION
            exif = image._getexif()
            if exif is not None:
                orientation = exif.get(0x0112)  # Orientation tag
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
        except:
            pass  # Skip if no EXIF data
        
        # Better preprocessing
        # Convert to RGB (handles grayscale, RGBA, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # For very large images, resize in steps to preserve quality
        if max(image.size) > 1000:
            # First resize to reasonable size, maintaining aspect ratio
            image.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        
        # Final resize to model input size
        image = image.resize((224, 224), Image.Resampling.LANCZOS)
        
        # Convert to array and normalize
        image_array = np.array(image, dtype=np.float32) / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        # Get predictions
        predictions = model.predict(image_array, verbose=0)[0]
        top_class_idx = int(np.argmax(predictions))
        confidence = float(predictions[top_class_idx])
        predicted_class = class_names[top_class_idx]
        
        # Check if confidence is too low (might indicate poor image quality)
        low_confidence_warning = None
        if confidence < 0.5:
            low_confidence_warning = "Low confidence prediction. Image quality might be poor or disease not clearly visible."
        
        return {
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "all_confidences": {
                cls_name: round(float(conf), 4)
                for cls_name, conf in zip(class_names, predictions)
            },
            "image_info": {
                "original_size": original_size,
                "original_mode": original_mode,
                "processed_size": [224, 224]
            },
            "warning": low_confidence_warning
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


@app.post("/debug-image", tags=["Debug"])
async def debug_image(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Debug endpoint to analyze image properties without prediction"""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Get image statistics
        image_rgb = image.convert('RGB')
        image_array = np.array(image_rgb)
        
        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "file_size_bytes": len(contents),
            "original_size": image.size,
            "original_mode": image.mode,
            "has_transparency": image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
            "pixel_stats": {
                "mean_rgb": [float(np.mean(image_array[:,:,i])) for i in range(3)],
                "std_rgb": [float(np.std(image_array[:,:,i])) for i in range(3)],
                "min_rgb": [int(np.min(image_array[:,:,i])) for i in range(3)],
                "max_rgb": [int(np.max(image_array[:,:,i])) for i in range(3)]
            },
            "recommendations": {
                "image_quality": "Good" if min(image.size) >= 224 else "Low resolution - might affect accuracy",
                "format_issues": "None" if image.mode == 'RGB' else f"Convert from {image.mode} to RGB",
                "brightness": "Normal" if 50 < np.mean(image_array) < 200 else "Too dark/bright - might affect accuracy"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

