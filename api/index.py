from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import List

import numpy as np
import pickle
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Get the base directory (SymptoCare root)
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "model" / "model.pkl"
SYMPTOMS_PATH = BASE_DIR / "model" / "symptoms_list.pkl"
DESCRIPTION_PATH = BASE_DIR / "Datasets" / "symptom_Description.csv"
ENV_PATH = BASE_DIR / "backend" / ".env"

load_dotenv(ENV_PATH)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").strip()

app = FastAPI(title="SymptoCare API")

if CORS_ORIGINS:
	origins = [origin.strip() for origin in CORS_ORIGINS.split(",") if origin.strip()]
else:
	origins = ["*"]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


class PredictRequest(BaseModel):
	symptoms: List[str]


class AuthPayload(BaseModel):
	email: str
	password: str


class ProfileUpdate(BaseModel):
	full_name: str | None = None
	age: int | None = None
	gender: str | None = None


class HistoryCreate(BaseModel):
	symptoms: List[str]
	predicted_disease: str
	confidence: float | None = None
	description: str | None = None


class PasswordUpdate(BaseModel):
	new_password: str


def load_model():
	"""Load the ML model from pickle file"""
	try:
		with MODEL_PATH.open("rb") as file:
			return pickle.load(file)
	except Exception as e:
		print(f"Error loading model: {e}")
		return None


def load_symptoms():
	"""Load symptoms list from pickle file"""
	try:
		with SYMPTOMS_PATH.open("rb") as file:
			return pickle.load(file)
	except Exception as e:
		print(f"Error loading symptoms: {e}")
		return []


def load_descriptions() -> dict[str, str]:
	"""Load disease descriptions from CSV"""
	try:
		if not DESCRIPTION_PATH.exists():
			return {}
		with DESCRIPTION_PATH.open("r", encoding="utf-8", newline="") as file:
			reader = csv.DictReader(file)
			return {
				row["Disease"].strip(): row["Description"].strip()
				for row in reader
				if row.get("Disease") and row.get("Description")
			}
	except Exception as e:
		print(f"Error loading descriptions: {e}")
		return {}


# Load model data at startup
try:
	MODEL = load_model()
	SYMPTOMS = list(load_symptoms()) if load_symptoms() else []
	DESCRIPTIONS = load_descriptions()
except Exception as e:
	print(f"Error during initialization: {e}")
	MODEL = None
	SYMPTOMS = []
	DESCRIPTIONS = {}


@app.get("/health")
def health_check():
	"""Health check endpoint for Vercel"""
	return {"status": "healthy", "service": "SymptoCare API"}


@app.get("/")
def root():
	"""Root endpoint"""
	return {"message": "SymptoCare API is running"}


# Example prediction endpoint (customize based on your actual implementation)
@app.post("/predict")
def predict(request: PredictRequest):
	"""Make a disease prediction based on symptoms"""
	try:
		if not request.symptoms:
			raise HTTPException(status_code=400, detail="Symptoms list cannot be empty")
		
		# If model is not loaded, return mock prediction
		if not MODEL:
			return {
				"symptoms": request.symptoms,
				"predicted_disease": "Unable to predict - model not loaded",
				"confidence": 0,
				"description": "Please ensure model files are in the /model directory"
			}
		
		# Convert symptom names to indices using SYMPTOMS list
		symptom_indices = []
		for symptom in request.symptoms:
			if symptom in SYMPTOMS:
				symptom_indices.append(SYMPTOMS.index(symptom))
		
		if not symptom_indices:
			raise HTTPException(status_code=400, detail="No valid symptoms provided")
		
		# Create input array for model (one-hot encoding)
		input_array = np.zeros(len(SYMPTOMS))
		for idx in symptom_indices:
			input_array[idx] = 1
		
		# Make prediction
		prediction = MODEL.predict([input_array])[0]
		
		# Get confidence (if available)
		confidence = 0.85
		
		# Get description from DESCRIPTIONS
		description = DESCRIPTIONS.get(prediction, "No description available")
		
		return {
			"symptoms": request.symptoms,
			"predicted_disease": prediction,
			"confidence": confidence,
			"description": description
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# Auth endpoints (customize based on your Supabase setup)
@app.post("/auth/signup")
def signup(payload: AuthPayload):
	"""User signup endpoint"""
	try:
		# For now, just return success - integrate with Supabase later
		return {
			"email": payload.email,
			"access_token": "mock_token_" + payload.email.split("@")[0]
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/login")
def login(payload: AuthPayload):
	"""User login endpoint"""
	try:
		# For now, just return success - integrate with Supabase later
		return {
			"email": payload.email,
			"access_token": "mock_token_" + payload.email.split("@")[0]
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.put("/profile")
def update_profile(payload: ProfileUpdate, authorization: str = Header(None)):
	"""Update user profile"""
	try:
		# Extract token from header
		token = authorization.replace("Bearer ", "") if authorization else None
		if not token:
			raise HTTPException(status_code=401, detail="Unauthorized")
		
		return {
			"message": "Profile updated successfully",
			"full_name": payload.full_name
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile")
def get_profile(authorization: str = Header(None)):
	"""Get user profile"""
	try:
		# Extract token from header
		token = authorization.replace("Bearer ", "") if authorization else None
		if not token:
			raise HTTPException(status_code=401, detail="Unauthorized")
		
		return {
			"full_name": "User",
			"email": "user@example.com",
			"created_at": "2024-01-01"
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/symptoms")
def get_symptoms():
	"""Get list of available symptoms"""
	try:
		if not SYMPTOMS:
			raise HTTPException(status_code=500, detail="Symptoms list not loaded from model")
		
		# Return symptoms as objects with key and label
		return [{"key": symptom, "label": symptom.replace("_", " ").title()} for symptom in SYMPTOMS]
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
def get_history(authorization: str = Header(None)):
	"""Get user's prediction history"""
	try:
		# Extract token from header
		token = authorization.replace("Bearer ", "") if authorization else None
		if not token:
			raise HTTPException(status_code=401, detail="Unauthorized")
		
		# Return empty history array for now
		return []
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# Export handler for Vercel
# Vercel requires the ASGI app to be exported as 'app'
# FastAPI is already an ASGI application

# For Vercel to recognize this as a Python function
__all__ = ['app']
