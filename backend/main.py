"""
Landslide risk API.

Run locally:
    pip install -r requirements.txt
    uvicorn main:app --reload

Then open http://127.0.0.1:8000/ in a browser (serves the frontend
dashboard), or hit http://127.0.0.1:8000/api/risk directly for JSON.
"""

import csv
import io
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from data_source import get_rainfall_data, save_to_csv, load_from_csv
from risk_model import score_region

app = FastAPI(title="Landslide Risk API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RainfallRow(BaseModel):
    region: str
    state: str
    actual_mm: float
    normal_mm: float


@app.get("/api/rainfall")
def api_rainfall():
    """Raw rainfall data currently loaded (from CSV, or live source once wired up)."""
    return get_rainfall_data()


@app.get("/api/risk")
def api_risk():
    """Rainfall data run through the risk model, ranked highest risk first."""
    rows = get_rainfall_data()
    if not rows:
        raise HTTPException(status_code=404, detail="No rainfall data loaded yet.")

    results = [
        score_region(r["region"], r["actual_mm"], r["normal_mm"], r.get("state"))
        for r in rows
    ]
    results.sort(key=lambda r: r.risk_score, reverse=True)
    return [r.__dict__ for r in results]


@app.post("/api/rainfall")
def api_set_rainfall(rows: List[RainfallRow]):
    """Replace the current rainfall dataset with new rows (JSON body)."""
    save_to_csv([r.dict() for r in rows])
    return {"status": "ok", "rows_saved": len(rows)}


@app.post("/api/upload-csv")
async def api_upload_csv(file: UploadFile = File(...)):
    """
    Upload a CSV with columns: region,state,actual_mm,normal_mm
    Replaces the current dataset.
    """
    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for row in reader:
        try:
            rows.append({
                "region": row["region"].strip(),
                "state": row.get("state", row["region"]).strip(),
                "actual_mm": float(row["actual_mm"]),
                "normal_mm": float(row["normal_mm"]),
            })
        except (KeyError, ValueError) as e:
            raise HTTPException(status_code=400, detail=f"Bad CSV row {row}: {e}")

    save_to_csv(rows)
    return {"status": "ok", "rows_saved": len(rows)}


# Serve the frontend dashboard at "/"
# app.mount("/static", StaticFiles(directory="../frontend"), name="static")


# @app.get("/")
# def serve_frontend():
#     return FileResponse("../frontend/index.html")

@app.get("/")
def root():
    return {"message": "FastAPI is working on Vercel!"}