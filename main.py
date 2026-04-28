from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional
import json
import os

app = FastAPI()

# Static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Load subjects from JSON
try:
    with open("data/subjects.json", "r", encoding="utf-8") as f:
        SUBJECTS = json.load(f)
except FileNotFoundError:
    SUBJECTS = []
    with open("data/subjects.json", "w", encoding="utf-8") as f:
        json.dump(SUBJECTS, f, ensure_ascii=False, indent=2)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Display the main timetable page"""
    return templates.TemplateResponse(request, "index.html")

@app.get("/api/subjects", response_class=JSONResponse)
async def get_subjects(
    request: Request,
    year: Optional[int] = 1,
    field: Optional[str] = None,
    regtype: Optional[str] = None
):
    """Get subjects filtered by year, field, and registration type"""
    filtered = SUBJECTS
    
    # Filter by year
    if year is not None:
        filtered = [s for s in filtered if s.get("year") == year]
    
    # Filter by field
    if field and field != "":
        filtered = [s for s in filtered if s.get("field") == field]
    
    # Filter by registration type
    if regtype and regtype != "":
        filtered = [s for s in filtered if s.get("regtype") == regtype]
    
    return JSONResponse(filtered)

@app.post("/api/timetable", response_class=JSONResponse)
async def update_timetable(
    request: Request,
    year: int = Form(...),
    timetable: str = Form(...)
):
    """Save timetable data"""
    try:
        # Parse timetable JSON
        timetable_data = json.loads(timetable)
        
        # Save to file
        filename = f"data/timetable_{year}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(timetable_data, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({"status": "success", "message": "Timetable saved successfully"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.get("/api/timetable/{year}", response_class=JSONResponse)
async def get_timetable(year: int):
    """Get saved timetable for a year"""
    filename = f"data/timetable_{year}.json"
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return JSONResponse(json.load(f))
    return JSONResponse({"status": "not_found"}, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
