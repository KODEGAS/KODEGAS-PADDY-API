# Paddy Disease Detection API

This project is a FastAPI-based API for detecting diseases in paddy crops from images. It uses a trained TensorFlow model to classify diseases and provides a comprehensive set of endpoints to manage disease information and recommended medicines. The API also includes a simple web interface for CRUD operations on the data.

## Features

- **Disease Prediction:** Upload an image of a paddy leaf to get a prediction of the disease and the confidence score.
- **Disease Information:** Get detailed information about different paddy diseases, including symptoms, causes, and prevention methods.
- **Medicine Recommendations:** Get a list of recommended medicines for a specific disease, sorted by priority.
- **CRUD Operations:** A web-based interface to Create, Read, Update, and Delete disease information and medicine data.
- **Dockerized:** The application is fully containerized for easy deployment.
- **Health Check:** A `/health` endpoint to monitor the service status.

## Project Structure

```
.
├── Dockerfile
├── LICENSE
├── README.md
├── disease_info.json
├── disease_medicines.json
├── labels.txt
├── main.py
├── mymodel
│   ├── saved_model.pb
│   └── variables
│       ├── variables.data-00000-of-00001
│       └── variables.index
├── openapi.json
├── requirements.txt
└── static
    ├── api_data.html
    ├── crud.html
    └── disease_info_crud.html
```

## API Endpoints

A full list of API endpoints is available in the `openapi.json` file and can be accessed interactively at `/docs` when the application is running.

### Main Endpoints

- `POST /predict`: Upload an image file to get a disease prediction.
- `GET /disease-info/{name}`: Get detailed information about a specific disease.
- `GET /disease-medicines?name={name}`: Get recommended medicines for a disease.
- `GET /health`: Health check endpoint.

### CRUD Endpoints

The API also provides a full set of CRUD endpoints for managing the `disease_info.json` and `disease_medicines.json` files. These are primarily used by the static web interface.

## Getting Started

### Prerequisites

- Python 3.11
- Docker (for containerized deployment)

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/kavindus0/paddy_disease_api.git
    cd paddy_disease_api
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

#### Locally

To run the application locally, use `uvicorn`:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

#### Using Docker

To build and run the application using Docker:

1.  **Build the Docker image:**

    ```bash
    docker build -t paddy-disease-api .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -p 8000:8000 paddy-disease-api
    ```

The API will be available at `http://localhost:8000`.

## Security

The CRUD endpoints (`/medicines/*` and `/crud/disease-info/*`) are protected by API key authentication. To use these endpoints, you must provide a valid API key in the `X-API-KEY` header of your request.

The default API key is `your-secret-api-key`. You can change this in the `auth.py` file. For production environments, it is highly recommended to use an environment variable to store the API key.

When using the web interface, you will be prompted to enter the API key the first time you try to perform a protected action. The key will be stored in your browser's session storage for convenience.

## Web Interface

The application includes a simple web interface for managing the data. It can be accessed at `/static/api_data.html`.

-   **Manage Medicines:** A CRUD interface for adding, editing, and deleting medicine information for each disease.
-   **Manage Disease Info:** A CRUD interface for updating the information for each disease.

## Data Files

-   `disease_info.json`: Contains detailed information about each disease.
-   `disease_medicines.json`: Contains a list of recommended medicines for each disease.
-   `labels.txt`: A list of the class names that the model can predict.

## Model

The prediction model is a trained TensorFlow model located in the `mymodel/` directory. It is loaded at startup and used by the `/predict` endpoint.
