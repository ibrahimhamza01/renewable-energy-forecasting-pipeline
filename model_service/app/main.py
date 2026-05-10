from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model_service.app.artifact_loader import find_station

from model_service.app.artifact_loader import load_model_metrics, load_stations
from model_service.app.live_analyzer import analyze_live_observation
from model_service.app.noaa_client import NOAAClient
from model_service.app.schemas import LiveAnalyzeRequest

import os
from dotenv import load_dotenv

load_dotenv()


app = FastAPI(
    title="Wind Energy Live Analysis Service",
    version="0.1.0",
    description="No-retraining live wind analysis API using NOAA observations and preserved Spark pipeline artifacts.",
)

FRONTEND_ORIGINS = [
    origin.strip()
    for origin in os.environ["FRONTEND_ORIGINS"].split(",")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

noaa = NOAAClient()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "wind-live-analysis-service",
    }


@app.get("/metrics")
def metrics():
    return load_model_metrics()


@app.get("/stations")
def stations():
    return load_stations()


@app.post("/analyze-live")
async def analyze_live(request: LiveAnalyzeRequest):
    station_id = request.station_id.strip().upper()

    station = find_station(station_id)

    if station is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown or unsupported station '{station_id}'. "
                "Use a verified NOAA station from the website station list."
            ),
        )

    try:
        observation = await noaa.get_latest_observation(station_id)
        return analyze_live_observation(observation)

    except Exception:
        raise HTTPException(
            status_code=502,
            detail=(
                f"NOAA observation unavailable for station '{station_id}'."
            ),
        )
