# 🚀 Quick Start Guide - JSON CRUD Interface

## ⚡ Get Started in 3 Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
# Option A: Using the startup script (recommended)
python3 start_server.py

# Option B: Direct uvicorn command
uvicorn main:app --reload
```

### 3. Open Web Interface
Visit: **http://localhost:8000/static/crud.html**

---

## 🎯 What You Can Do

### ✅ **View Medicines**
- Select any disease from the dropdown
- See all medicines with full details
- Medicines are sorted by priority

### ➕ **Add New Medicine**
- Click "Add New Medicine" button
- Fill in the form (only name is required)
- Save to add to JSON file

### ✏️ **Edit Medicine**
- Click "Edit" button on any medicine
- Modify any field
- Save changes

### 🗑️ **Delete Medicine**
- Click "Delete" button on any medicine
- Confirm deletion
- Medicine is removed from JSON file

---

## 🔧 API Endpoints

| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/medicines` | List all diseases |
| GET | `/medicines/{disease}` | Get medicines for disease |
| POST | `/medicines/{disease}` | Add new medicine |
| PUT | `/medicines/{disease}/{index}` | Update medicine |
| DELETE | `/medicines/{disease}/{index}` | Delete medicine |

---

## 📚 Documentation

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

---

## 🆘 Troubleshooting

### Server won't start?
```bash
# Check if dependencies are installed
python3 validate_setup.py

# Install missing dependencies
pip install -r requirements.txt
```

### Can't access web interface?
- Make sure server is running on port 8000
- Visit: http://localhost:8000/static/crud.html
- Check browser console for errors

### Changes not saving?
- Check file permissions on `disease_medicines.json`
- Look for error messages in the web interface
- Check server logs in terminal

---

## 🎉 You're Ready!

Your JSON CRUD interface is now fully functional. You can:
- ✅ Add new medicines to any disease category
- ✅ Edit existing medicine details  
- ✅ Delete medicines safely
- ✅ All changes are saved to your JSON file automatically
- ✅ Thread-safe operations prevent data corruption

**Happy editing!** 🌾
