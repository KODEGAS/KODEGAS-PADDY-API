"""
Enhanced Rice Disease Detection API
  - /health               : Health check with system info
  - /classes              : List all detectable disease classes
  - /info                 : Model input/output metadata
  - /predict              : Predict disease from uploaded image
  - /disease-info         : List all diseases or get info about a specific one
  - /disease-medicines    : Get recommended treatments for a given disease
  - /batch-predict        : Predict multiple images at once
  - /stats                : API usage statistics
  - /search-diseases      : Search diseases by symptoms or keywords
  - /prevention-tips      : Get prevention tips for all or specific diseases
  - /severity-assessment  : Assess disease severity from confidence scores
"""

from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import tensorflow as tf
import numpy as np
from PIL import Image, ExifTags
import io
import json
import uvicorn
import asyncio
import time
import psutil
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import hashlib
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for tracking
request_count = 0
prediction_count = 0
start_time = time.time()

# Pydantic models for better request/response validation
class PredictionResponse(BaseModel):
    predicted_class: str
    confidence: float = Field(..., ge=0, le=1)
    all_confidences: Dict[str, float]
    severity_level: str
    recommendation: str
    processing_time_ms: float

class BatchPredictionRequest(BaseModel):
    max_files: int = Field(default=5, ge=1, le=10)

class StatsResponse(BaseModel):
    uptime_seconds: float
    total_requests: int
    total_predictions: int
    system_memory_usage: float
    system_cpu_usage: float
    model_loaded: bool
    timestamp: str

class DiseaseSearchQuery(BaseModel):
    query: str = Field(..., min_length=2, max_length=100)
    limit: int = Field(default=5, ge=1, le=20)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    logger.info("🚀 Starting Rice Disease Detection API...")
    
    # Load model and data on startup
    try:
        await load_resources()
        logger.info("✅ All resources loaded successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load resources: {e}")
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("🔄 Shutting down Rice Disease Detection API...")

app = FastAPI(
    title="Rice Disease Detection API",
    description=(
        "🌾 An advanced AI-powered API to detect common rice diseases from images. "
        "Built with TensorFlow and FastAPI. Returns disease predictions, "
        "detailed information, recommended treatments, and severity assessments."
    ),
    version="2.0.0",
    contact={
        "name": "KODEGAS AI Team",
        "email": "kavix@yahoo.com",
    },
    license_info={
        "name": "MIT License",
    },
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # Configure this properly for production
)

# Configuration
MODEL_PATH = "mymodel"
LABELS_FILE = "labels.txt"
DISEASE_INFO_FILE = "disease_info.json"
DISEASE_MEDICINES_FILE = "disease_medicines.json"

# Global variables
model = None
class_names = []
disease_info = {}
disease_medicines = {}

async def load_resources():
    """Load model and data files"""
    global model, class_names, disease_info, disease_medicines
    
    try:
        # Load model
        model = tf.keras.models.load_model(MODEL_PATH)
        logger.info(f"Model loaded successfully from {MODEL_PATH}")
        
        # Load labels
        with open(LABELS_FILE, "r") as f:
            class_names = [line.strip().split(maxsplit=1)[-1] for line in f if line.strip()]
        logger.info(f"Loaded {len(class_names)} class names")
        
        # Load disease info
        with open(DISEASE_INFO_FILE, "r") as f:
            disease_info = json.load(f)
        logger.info(f"Loaded disease information for {len(disease_info)} diseases")
        
        # Load medicine data
        with open(DISEASE_MEDICINES_FILE, "r") as f:
            disease_medicines = json.load(f)
        logger.info(f"Loaded medicine recommendations for {len(disease_medicines)} diseases")
        
    except Exception as e:
        logger.error(f"Resource loading failed: {e}")
        raise RuntimeError(f"Failed to load resources: {e}")

def track_request():
    """Dependency to track API requests"""
    global request_count
    request_count += 1

def preprocess_image(image: Image.Image, target_size: tuple = (224, 224)) -> np.ndarray:
    """Enhanced image preprocessing with rotation correction"""
    try:
        # Handle EXIF orientation
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        
        if hasattr(image, '_getexif'):
            exif = image._getexif()
            if exif is not None and orientation in exif:
                if exif[orientation] == 3:
                    image = image.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    image = image.rotate(270, expand=True)
                elif exif[orientation] == 8:
                    image = image.rotate(90, expand=True)
        
        # Convert to RGB and resize
        image = image.convert("RGB")
        image = image.resize(target_size, Image.Resampling.LANCZOS)
        
        # Normalize
        image_array = np.array(image) / 255.0
        return np.expand_dims(image_array, axis=0)
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {e}")
        raise

def assess_severity(confidence: float, predicted_class: str) -> tuple[str, str]:
    """Assess disease severity and provide recommendations"""
    if confidence < 0.5:
        return "uncertain", "Consider retaking the image with better lighting and focus"
    elif confidence < 0.7:
        return "mild", "Monitor the plant and apply preventive measures"
    elif confidence < 0.9:
        return "moderate", "Apply recommended treatments and monitor closely"
    else:
        return "severe", "Immediate treatment required - consult agricultural expert"

# Original endpoints (unchanged)
@app.get("/health", tags=["Health"])
def health_check(background_tasks: BackgroundTasks, _=Depends(track_request)):
    """Enhanced health check with system information"""
    try:
        system_info = {
            "status": "ok",
            "message": "Service is up and running",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": round(time.time() - start_time, 2),
            "model_loaded": model is not None,
            "total_classes": len(class_names),
            "memory_usage_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
            "cpu_percent": psutil.cpu_percent()
        }
        return system_info
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/classes", tags=["Model"])
def get_classes(_=Depends(track_request)) -> Dict[str, List[str]]:
    """Returns the list of all disease classes the model can predict."""
    return {"classes": class_names, "count": len(class_names)}

@app.get("/info", tags=["Model"])
def model_info(_=Depends(track_request)) -> Dict[str, Any]:
    """Enhanced model information with additional metadata"""
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
            
        input_shape = model.input_shape
        output_shape = model.output_shape
        
        return {
            "input_shape": input_shape,
            "output_shape": output_shape,
            "num_classes": len(class_names),
            "model_loaded": True,
            "model_type": str(type(model).__name__),
            "expected_image_size": f"{input_shape[1]}x{input_shape[2]}",
            "supported_formats": ["JPG", "JPEG", "PNG", "BMP", "TIFF"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving model info: {str(e)}")

@app.post("/predict", tags=["Prediction"], response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...), 
    background_tasks: BackgroundTasks = None,
    _=Depends(track_request)
) -> PredictionResponse:
    """Enhanced prediction with severity assessment and recommendations"""
    global prediction_count
    prediction_count += 1
    
    start_time_ms = time.time() * 1000
    
    # Validate file
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    
    # Check file size (limit to 10MB)
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    if file_size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    
    try:
        if model is None:
            raise HTTPException(status_code=503, detail="Model not loaded")
        
        # Process image
        image = Image.open(io.BytesIO(contents))
        image_array = preprocess_image(image)
        
        # Run prediction
        predictions = model.predict(image_array, verbose=0)[0]
        top_class_idx = int(np.argmax(predictions))
        confidence = float(predictions[top_class_idx])
        predicted_class = class_names[top_class_idx]
        
        # Assess severity
        severity_level, recommendation = assess_severity(confidence, predicted_class)
        
        processing_time = (time.time() * 1000) - start_time_ms
        
        return PredictionResponse(
            predicted_class=predicted_class,
            confidence=round(confidence, 4),
            all_confidences={
                cls_name: round(float(conf), 4)
                for cls_name, conf in zip(class_names, predictions)
            },
            severity_level=severity_level,
            recommendation=recommendation,
            processing_time_ms=round(processing_time, 2)
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/disease-info", tags=["Disease Info"])
def list_diseases(_=Depends(track_request)) -> Dict[str, Any]:
    """Enhanced disease listing with counts and categories"""
    diseases = sorted(list(disease_info.keys()))
    return {
        "available_diseases": diseases,
        "count": len(diseases),
        "categories": list(set(info.get("category", "unknown") for info in disease_info.values()))
    }

@app.get("/disease-info/{name}", tags=["Disease Info"])
def get_disease_info(
    name: str = Path(..., description="Disease identifier", example="blast"),
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Get detailed information about a specific disease."""
    key = name.strip().lower()
    info = disease_info.get(key)
    
    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{name}' not found. Available: {list(disease_info.keys())}"
        )
    
    return {"disease": key, "info": info, "last_updated": datetime.now().isoformat()}

@app.get("/disease-medicines", tags=["Treatment"])
def get_disease_medicines(
    name: str = Query(..., description="Disease identifier", example="bacterial_leaf_blight"),
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Get recommended medicines with enhanced sorting and filtering."""
    key = name.strip().lower()
    medicines = disease_medicines.get(key)
    
    if not medicines:
        raise HTTPException(
            status_code=404,
            detail=f"No medicine information found for '{name}'. "
                   f"Available diseases: {list(disease_medicines.keys())}"
        )
    
    # Enhanced sorting by priority and availability
    sorted_medicines = sorted(
        medicines, 
        key=lambda m: (m.get("priority", 999), -m.get("availability_score", 0))
    )
    
    return {
        "disease": key,
        "recommended_medicines": sorted_medicines,
        "total_options": len(sorted_medicines),
        "priority_medicines": [m for m in sorted_medicines if m.get("priority", 999) <= 2]
    }

# New enhanced endpoints
@app.post("/batch-predict", tags=["Prediction"])
async def batch_predict(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Predict multiple images at once (max 5 files)"""
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 files allowed per batch")
    
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    results = []
    start_time_ms = time.time() * 1000
    
    for idx, file in enumerate(files):
        try:
            if not file.content_type.startswith("image/"):
                results.append({
                    "file_index": idx,
                    "filename": file.filename,
                    "error": "Invalid file type"
                })
                continue
            
            contents = await file.read()
            image = Image.open(io.BytesIO(contents))
            image_array = preprocess_image(image)
            
            predictions = model.predict(image_array, verbose=0)[0]
            top_class_idx = int(np.argmax(predictions))
            confidence = float(predictions[top_class_idx])
            predicted_class = class_names[top_class_idx]
            
            severity_level, recommendation = assess_severity(confidence, predicted_class)
            
            results.append({
                "file_index": idx,
                "filename": file.filename,
                "predicted_class": predicted_class,
                "confidence": round(confidence, 4),
                "severity_level": severity_level,
                "recommendation": recommendation
            })
            
        except Exception as e:
            results.append({
                "file_index": idx,
                "filename": file.filename,
                "error": str(e)
            })
    
    processing_time = (time.time() * 1000) - start_time_ms
    
    return {
        "results": results,
        "total_files": len(files),
        "successful_predictions": len([r for r in results if "error" not in r]),
        "processing_time_ms": round(processing_time, 2)
    }

@app.get("/stats", tags=["Analytics"], response_model=StatsResponse)
def get_api_stats(_=Depends(track_request)) -> StatsResponse:
    """Get comprehensive API usage statistics"""
    return StatsResponse(
        uptime_seconds=round(time.time() - start_time, 2),
        total_requests=request_count,
        total_predictions=prediction_count,
        system_memory_usage=round(psutil.Process().memory_info().rss / 1024 / 1024, 2),
        system_cpu_usage=psutil.cpu_percent(),
        model_loaded=model is not None,
        timestamp=datetime.now().isoformat()
    )

@app.get("/search-diseases", tags=["Disease Info"])
def search_diseases(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=5, ge=1, le=20),
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Search diseases by symptoms, keywords, or partial names"""
    query = q.lower().strip()
    matches = []
    
    for disease_name, info in disease_info.items():
        score = 0
        
        # Check disease name
        if query in disease_name.lower():
            score += 10
        
        # Check symptoms
        symptoms = info.get("symptoms", "").lower()
        if query in symptoms:
            score += 5
        
        # Check description
        description = info.get("description", "").lower()
        if query in description:
            score += 3
        
        if score > 0:
            matches.append({
                "disease": disease_name,
                "relevance_score": score,
                "match_type": "name" if query in disease_name.lower() else "content",
                "info": info
            })
    
    # Sort by relevance score
    matches.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return {
        "query": q,
        "matches": matches[:limit],
        "total_matches": len(matches)
    }

@app.get("/prevention-tips", tags=["Disease Info"])
def get_prevention_tips(
    disease: Optional[str] = Query(None, description="Specific disease name"),
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Get prevention tips for all diseases or a specific one"""
    if disease:
        key = disease.strip().lower()
        info = disease_info.get(key)
        if not info:
            raise HTTPException(status_code=404, detail=f"Disease '{disease}' not found")
        
        return {
            "disease": key,
            "prevention_tips": info.get("prevention", []),
            "contributing_factors": info.get("contributing_factors", [])
        }
    else:
        # Return general prevention tips for all diseases
        all_tips = {}
        for disease_name, info in disease_info.items():
            all_tips[disease_name] = {
                "prevention": info.get("prevention", []),
                "contributing_factors": info.get("contributing_factors", [])
            }
        
        return {
            "prevention_tips": all_tips,
            "general_recommendations": [
                "Maintain proper field hygiene",
                "Use certified disease-free seeds",
                "Implement crop rotation",
                "Ensure proper drainage",
                "Monitor crops regularly",
                "Apply balanced fertilization"
            ]
        }

@app.get("/severity-assessment/{disease}", tags=["Analysis"])
def get_severity_assessment(
    disease: str = Path(..., description="Disease name"),
    confidence: float = Query(..., ge=0, le=1, description="Prediction confidence"),
    _=Depends(track_request)
) -> Dict[str, Any]:
    """Get detailed severity assessment for a disease prediction"""
    key = disease.strip().lower()
    
    if key not in disease_info:
        raise HTTPException(status_code=404, detail=f"Disease '{disease}' not found")
    
    severity_level, recommendation = assess_severity(confidence, key)
    
    # Enhanced recommendations based on disease type
    info = disease_info.get(key, {})
    treatment_urgency = "high" if confidence > 0.8 else "medium" if confidence > 0.6 else "low"
    
    return {
        "disease": key,
        "confidence": confidence,
        "severity_level": severity_level,
        "treatment_urgency": treatment_urgency,
        "recommendation": recommendation,
        "suggested_actions": info.get("treatment", []),
        "monitoring_frequency": "daily" if severity_level == "severe" else "weekly",
        "expert_consultation_needed": confidence > 0.8
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
