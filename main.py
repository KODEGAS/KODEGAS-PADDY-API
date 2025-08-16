



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
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
        image = image.resize((224, 224))
        image_array = np.array(image) / 255.0
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

