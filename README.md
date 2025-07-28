

# Rice Disease Detection API Documentation

## Overview

The Rice Disease Detection API is a FastAPI-based service for:
- Predicting rice diseases from leaf/panicle images using a pre-trained deep learning model.
- Providing detailed disease information and recommended treatments (medicines).

---

## Features

- **/health**: Health check endpoint.
- **/classes**: List all detectable disease classes.
- **/info**: Model input/output metadata.
- **/predict**: Predict disease from uploaded image.
- **/disease-info**: List all diseases or get info about a specific one.
- **/disease-medicines**: Get recommended treatments for a given disease.

---

## Setup

### Requirements

- Python 3.11+
- [FastAPI](https://fastapi.tiangolo.com/)
- [TensorFlow](https://www.tensorflow.org/)
- [Pillow (PIL)](https://python-pillow.org/)
- [Uvicorn](https://www.uvicorn.org/)

Install dependencies:
```sh
pip install -r requirements.txt
```

### Running the API

```sh
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Endpoints

### 1. Health Check

**GET /health**

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Service is up and running"
}
```

---

### 2. List Disease Classes

**GET /classes**

Returns all disease classes the model can predict.

**Response:**
```json
{
  "classes": [
    "bacterial_panicle_blight",
    "downey_mildew",
    "dead_heart",
    "bacterial_leaf_blight",
    "brown_spot",
    "normal",
    "hispa",
    "tungro",
    "blast",
    "bacterial_leaf_streak"
  ]
}
```

---

### 3. Model Info

**GET /info**

Returns model metadata.

**Response:**
```json
{
  "input_shape": [null, 224, 224, 3],
  "output_shape": [null, 10],
  "num_classes": 10,
  "model_loaded": true
}
```

---

### 4. Predict Disease

**POST /predict**

Upload an image to predict the disease.

**Request:**
- Form-data: `file` (image file, e.g., JPG, PNG)

**Response:**
```json
{
  "predicted_class": "blast",
  "confidence": 0.9876,
  "all_confidences": {
    "bacterial_panicle_blight": 0.0001,
    "downey_mildew": 0.0002,
    "...": "...",
    "blast": 0.9876,
    "bacterial_leaf_streak": 0.0001
  }
}
```

---

### 5. List All Diseases

**GET /disease-info**

Returns all disease keys available.

**Response:**
```json
{
  "available_diseases": [
    "bacterial_panicle_blight",
    "downey_mildew",
    "dead_heart",
    "bacterial_leaf_blight",
    "brown_spot",
    "normal",
    "hispa",
    "tungro",
    "blast",
    "bacterial_leaf_streak"
  ]
}
```

---

### 6. Get Disease Info

**GET /disease-info/{name}**

Get detailed info about a specific disease.

**Path Parameter:**
- `name`: Disease identifier (e.g., `blast`)

**Response:**
```json
{
  "disease": "blast",
  "info": {
    "disease_name": "Rice Blast",
    "caused_by": "Magnaporthe oryzae",
    "description": "...",
    "symptoms": ["..."],
    "factors": ["..."],
    "prevention": ["..."],
    "treatment": "...",
    "note": "..."
  }
}
```

---

### 7. Get Disease Medicines

**GET /disease-medicines?name={disease}**

Get recommended medicines for a disease.

**Query Parameter:**
- `name`: Disease identifier (e.g., `blast`)

**Response:**
```json
{
  "name": "blast",
  "recommended_medicines": [
    {
      "name": "Tricyclazole 75% WP",
      "brand": "BASF BlastX",
      "type": "Rice Blast Fungicide",
      "active_ingredient": "Tricyclazole",
      "pack_size": "250g",
      "price": "Rs. 1200",
      "image_url": "https://example.com/images/tricyclazole.jpg",
      "application_rate": "1g per liter of water",
      "method": "Spray at booting stage – critical for neck blast prevention",
      "frequency": "One preventive spray is usually sufficient",
      "availability": "Highly recommended and stocked in blast-prone areas",
      "priority": 1,
      "note": "Do not wait for symptoms. Proactive spraying is most effective."
    },
    ...
  ]
}
```

---

## Data Files

- labels.txt: List of class labels.
- disease_info.json: Disease descriptions, symptoms, prevention, and treatment.
- disease_medicines.json: Recommended medicines for each disease.

---

## Example Usage

**Predict Disease (using curl):**
```sh
curl -X POST "http://localhost:8000/predict" -F "file=@/path/to/leaf.jpg"
```

**Get Disease Info:**
```sh
curl "http://localhost:8000/disease-info/blast"
```

**Get Medicines:**
```sh
curl "http://localhost:8000/disease-medicines?name=blast"
```

---

## Error Handling

- 400: Invalid input (e.g., wrong file type)
- 404: Disease or medicine info not found
- 500: Internal server/model error

---

## License

MIT License

---

## Contact

- KODEGAS AI Team
- Email: kavix@yahoo.com

---

For more details, see the README.md and source code in main.py.
- If you want to upgrade Python, you can change the image in the [Dockerfile](./.codesandbox/Dockerfile).
- Modify [requirements.txt](./requirements.txt) to add packages.