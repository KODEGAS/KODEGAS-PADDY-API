# Disease Medicines CRUD Interface

This project now includes a complete CRUD (Create, Read, Update, Delete) interface for managing medicine data in your `disease_medicines.json` file.

## 🚀 Quick Start

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

3. **Access the web interface**:
   Open your browser and go to: `http://localhost:8000/static/crud.html`

## 📋 Features

### Web Interface
- **Disease Selection**: Choose from available disease categories
- **View Medicines**: See all medicines for a selected disease with full details
- **Add New Medicine**: Complete form to add new medicine entries
- **Edit Medicine**: Modify existing medicine details
- **Delete Medicine**: Remove medicines with confirmation
- **Real-time Updates**: Changes are immediately reflected in the JSON file

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/medicines` | List all disease categories |
| GET | `/medicines/{disease}` | Get all medicines for a disease |
| GET | `/medicines/{disease}/{index}` | Get specific medicine by index |
| POST | `/medicines/{disease}` | Add new medicine to disease category |
| PUT | `/medicines/{disease}/{index}` | Update existing medicine |
| DELETE | `/medicines/{disease}/{index}` | Delete medicine |

## 🧪 Testing

Run the test script to verify all endpoints work:
```bash
python3 test_crud.py
```

## 🔒 Safety Features

- **Thread-safe operations**: File locking prevents data corruption
- **Atomic writes**: Changes are written to temporary files first
- **Data validation**: Pydantic models ensure data integrity
- **Error handling**: Comprehensive error messages and status codes
- **Backup safety**: Original file structure is preserved

## 📊 Data Structure

Each medicine entry supports these fields:
- `name` (required): Medicine name
- `brand`: Brand name
- `type`: Medicine type (e.g., "Fungicide")
- `active_ingredient`: Active chemical ingredient
- `pack_size`: Package size
- `price`: Price information
- `priority`: Priority ranking (lower = higher priority)
- `image_url`: Product image URL
- `application_rate`: How much to use
- `method`: Application method
- `frequency`: How often to apply
- `availability`: Where to find it
- `note`: Additional notes

## 🌐 API Documentation

With the server running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **Alternative docs**: `http://localhost:8000/redoc`

## 🔧 Customization

### Adding New Disease Categories
New disease categories are automatically created when you add the first medicine to them.

### Modifying the Web Interface
Edit `static/crud.html` to customize the appearance or add new features.

### Extending the API
Add new endpoints in `main.py` following the existing pattern.

## 🚨 Important Notes

1. **Backup your data**: Always backup `disease_medicines.json` before making bulk changes
2. **Single user**: This interface is designed for single-user editing
3. **File permissions**: Ensure the application has write permissions to the JSON file
4. **Port conflicts**: Make sure port 8000 is available for the API server

## 🐛 Troubleshooting

### Common Issues

**"Module not found" errors**:
```bash
pip install -r requirements.txt
```

**"Permission denied" on JSON file**:
```bash
chmod 644 disease_medicines.json
```

**Port 8000 already in use**:
```bash
uvicorn main:app --reload --port 8001
# Then update API_BASE in crud.html to http://localhost:8001
```

**CORS errors in browser**:
The server is configured to allow all origins. If you still see CORS errors, try accessing the interface from `http://localhost:8000/static/crud.html` instead of opening the HTML file directly.

## 📈 Future Enhancements

Potential improvements you could add:
- User authentication
- Bulk import/export
- Image upload functionality
- Search and filtering
- Audit logging
- Multi-user support with conflict resolution
- Database backend for better performance

---

Happy editing! 🌾
