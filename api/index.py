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

# Load environment variables
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
		
		# Add your prediction logic here
		return {
			"symptoms": request.symptoms,
			"predicted_disease": "Sample Disease",
			"confidence": 0.85,
			"description": "This is a sample prediction"
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


# Export handler for Vercel
# Vercel requires the ASGI app to be exported as 'app'
# FastAPI is already an ASGI application

# For Vercel to recognize this as a Python function
__all__ = ['app']
