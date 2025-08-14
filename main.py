"""
Rice Disease Detection API
  - /health               : Health check
  - /classes              : List all detectable disease classes
  - /info                 : Model input/output metadata
  - /predict              : Predict disease from uploaded image
  - /disease-info         : List all diseases or get info about a specific one
  - /disease-medicines    : Get recommended treatments for a given disease

"""

from fastapi import FastAPI, UploadFile, File, Query, Path, HTTPException
import tensorflow as tf
import numpy as np
from PIL import Image
import io
import json
import uvicorn
from typing import List, Dict, Any

app = FastAPI(
    title="Rice Disease Detection API",
    description=(
        "An AI-powered API to detect common rice diseases from images. "
        "Built with TensorFlow and FastAPI. Returns disease predictions, "
        "detailed information, and recommended treatments."
    ),
    version="1.0.0",
    contact={
        "name": "KODEGAS AI Team",
        "email": "kavix@yahoo.com",
    },
    license_info={
        "name": "MIT License",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)



MODEL_PATH = "mymodel"  # Path to trained Keras model (HDF5 or SavedModel format)
LABELS_FILE = "labels.txt"  # Class labels (e.g., '0 bacterial_panicle_blight')
DISEASE_INFO_FILE = "disease_info.json"  # Disease descriptions, symptoms, prevention
DISEASE_MEDICINES_FILE = "disease_medicines.json"  # Treatment recommendations



try:
    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"[INFO] Model loaded successfully from {MODEL_PATH}")
except Exception as e:
    raise RuntimeError(f"Failed to load model from {MODEL_PATH}: {e}")

try:
    with open(LABELS_FILE, "r") as f:
        class_names = [line.strip().split(maxsplit=1)[-1] for line in f if line.strip()]
    print(f"[INFO] Loaded {len(class_names)} class names from {LABELS_FILE}")
except Exception as e:
    raise RuntimeError(f"Failed to load labels from {LABELS_FILE}: {e}")

try:
    with open(DISEASE_INFO_FILE, "r") as f:
        disease_info = json.load(f)
    print(f"[INFO] Loaded disease information for {len(disease_info)} diseases")
except Exception as e:
    raise RuntimeError(f"Failed to load disease info from {DISEASE_INFO_FILE}: {e}")

try:
    with open(DISEASE_MEDICINES_FILE, "r") as f:
        disease_medicines = json.load(f)
    print(f"[INFO] Loaded medicine recommendations for {len(disease_medicines)} diseases")
except Exception as e:
    raise RuntimeError(f"Failed to load medicine data from {DISEASE_MEDICINES_FILE}: {e}")



@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "Service is up and running"}


@app.get("/classes", tags=["Model"])
def get_classes() -> Dict[str, List[str]]:
    """
    Returns the list of all disease classes the model can predict.
    These correspond to the output labels of the neural network.
    """
    return {"classes": class_names}


@app.get("/info", tags=["Model"])
def model_info() -> Dict[str, Any]:
    """
    Returns metadata about the loaded model:
    - Input shape (expected image dimensions)
    - Output shape (number of prediction probabilities)
    - Number of classes
    """
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
    """
    Predict the rice disease from an uploaded image.

    Args:
        file (UploadFile): Image file (e.g., JPG, PNG) of a rice leaf, panicle, or plant.

    Returns:
        JSON with:
        - predicted_class: Name of the predicted disease
        - confidence: Prediction score (0–1)
        - all_confidences: Confidence scores for all classes
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

    try:
        # Read and preprocess image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")  # Ensure 3 channels
        image = image.resize((224, 224))  # Match model input size
        image_array = np.array(image) / 255.0  # Normalize pixel values
        image_array = np.expand_dims(image_array, axis=0)  # Add batch dimension

        # Run prediction
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
    """
    Returns a list of all disease keys available in the disease_info database.
    Useful for frontend dropdowns or API exploration.
    """
    return {"available_diseases": sorted(list(disease_info.keys()))}


@app.get("/disease-info/{name}", tags=["Disease Info"])
def get_disease_info(name: str = Path(
    ...,
    description="Disease identifier (e.g., 'blast', 'bacterial_leaf_blight')",
    example="blast"
)) -> Dict[str, Any]:
    """
    Get detailed information about a specific disease.

    Returns:
        - disease name
        - causal agent
        - symptoms
        - contributing factors
        - prevention methods
        - treatment options
        - regional notes
    """
    # Normalize input to match JSON keys (lowercase)
    key = name.strip().lower()
    info = disease_info.get(key)

    if not info:
        raise HTTPException(
            status_code=404,
            detail=f"Disease '{name}' not found. Available options: {list(disease_info.keys())}"
        )

    return {
        "disease": key,
        "info": info
    }

#/// http://127.0.0.1:8001/disease-medicines?name=bacterial_leaf_blight
#/// me wage end point eka

@app.get("/disease-medicines", tags=["Treatment"])
def get_disease_medicines(
    name: str = Query(
        ...,
        description="Disease identifier to get recommended medicines (e.g., 'blast')",
        example="bacterial_leaf_blight"
    )
) -> Dict[str, Any]:
    """
    Retrieve a prioritized list of recommended medicines/treatments for a given disease.

    The results are sorted by 'priority' (1 = highest priority).

    Returns:
        - disease name
        - list of medicines with:
          - name, brand, type, active ingredient
          - dosage, method, frequency
          - availability, price, image URL
          - usage notes
    """
    key = name.strip().lower()
    medicines = disease_medicines.get(key)

    if not medicines:
        raise HTTPException(
            status_code=404,
            detail=f"No medicine information found for '{name}'. "
                   f"Available diseases: {list(disease_medicines.keys())}"
        )

    # Sort medicines by priority (lowest number = highest priority)
    sorted_medicines = sorted(medicines, key=lambda m: m.get("priority", 999))

    return {
        "name": key,
        "recommended_medicines": sorted_medicines
    }

