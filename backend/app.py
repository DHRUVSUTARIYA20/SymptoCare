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
	with MODEL_PATH.open("rb") as file:
		return pickle.load(file)


def load_symptoms():
	with SYMPTOMS_PATH.open("rb") as file:
		return pickle.load(file)


def load_descriptions() -> dict[str, str]:
	if not DESCRIPTION_PATH.exists():
		return {}
	with DESCRIPTION_PATH.open("r", encoding="utf-8", newline="") as file:
		reader = csv.DictReader(file)
		return {
			row["Disease"].strip(): row["Description"].strip()
			for row in reader
			if row.get("Disease") and row.get("Description")
		}


try:
	MODEL = load_model()
	SYMPTOMS = list(load_symptoms())
	DESCRIPTIONS = load_descriptions()
except Exception as exc:  # pragma: no cover - surface startup issues
	MODEL = None
	SYMPTOMS = []
	DESCRIPTIONS = {}
	LOAD_ERROR = str(exc)
else:
	LOAD_ERROR = None


def ensure_supabase_config() -> None:
	if not SUPABASE_URL or not SUPABASE_ANON_KEY:
		raise HTTPException(
			status_code=500,
			detail="Supabase is not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.",
		)


def supabase_request(
	method: str,
	endpoint: str,
	*,
	access_token: str | None = None,
	json: dict | None = None,
	params: dict | None = None,
	extra_headers: dict | None = None,
):
	ensure_supabase_config()
	url = f"{SUPABASE_URL}{endpoint}"
	headers = {
		"apikey": SUPABASE_ANON_KEY,
		"Content-Type": "application/json",
	}
	if access_token:
		headers["Authorization"] = f"Bearer {access_token}"
	if extra_headers:
		headers.update(extra_headers)

	response = requests.request(
		method,
		url,
		json=json,
		params=params,
		headers=headers,
		timeout=15,
	)
	if response.status_code >= 400:
		try:
			payload = response.json()
		except ValueError:
			payload = {}
		detail = (
			payload.get("msg")
			or payload.get("error_description")
			or payload.get("error")
			or response.text
			or "Supabase request failed."
		)
		raise HTTPException(status_code=response.status_code, detail=detail)
	if response.status_code == 204:
		return None
	return response.json()


def get_user_id(access_token: str) -> str:
	user = supabase_request("GET", "/auth/v1/user", access_token=access_token)
	user_id = user.get("id")
	if not user_id:
		raise HTTPException(status_code=401, detail="Invalid access token.")
	return user_id


@app.get("/health")
def health_check():
	if LOAD_ERROR:
		return {"status": "error", "detail": LOAD_ERROR}
	return {
		"status": "ok",
		"supabase_configured": bool(SUPABASE_URL and SUPABASE_ANON_KEY),
	}


@app.get("/symptoms")
def list_symptoms():
	if LOAD_ERROR:
		raise HTTPException(status_code=500, detail=LOAD_ERROR)
	return [
		{"key": symptom, "label": symptom.replace("_", " ")}
		for symptom in SYMPTOMS
	]


@app.post("/predict")
def predict(payload: PredictRequest):
	if LOAD_ERROR:
		raise HTTPException(status_code=500, detail=LOAD_ERROR)

	selected = [symptom for symptom in payload.symptoms if symptom in SYMPTOMS]
	if not selected:
		raise HTTPException(status_code=400, detail="Select at least one symptom.")

	vector = np.array([1 if symptom in selected else 0 for symptom in SYMPTOMS])
	prediction = MODEL.predict([vector])[0]
	description = DESCRIPTIONS.get(str(prediction), "")

	return {
		"disease": str(prediction),
		"description": description,
		"selected_symptoms": selected,
	}


@app.post("/auth/signup")
def auth_signup(payload: AuthPayload):
	data = supabase_request(
		"POST",
		"/auth/v1/signup",
		json={"email": payload.email, "password": payload.password},
	)
	return data


@app.post("/auth/login")
def auth_login(payload: AuthPayload):
	data = supabase_request(
		"POST",
		"/auth/v1/token",
		json={"email": payload.email, "password": payload.password},
		params={"grant_type": "password"},
	)
	return data


@app.put("/auth/password")
def auth_update_password(
	payload: PasswordUpdate, authorization: str | None = Header(default=None)
):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	data = supabase_request(
		"PUT",
		"/auth/v1/user",
		access_token=access_token,
		json={"password": payload.new_password},
	)
	return data


@app.get("/profile")
def get_profile(authorization: str | None = Header(default=None)):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	user_id = get_user_id(access_token)
	data = supabase_request(
		"GET",
		"/rest/v1/profiles",
		access_token=access_token,
		params={"select": "*", "id": f"eq.{user_id}"},
	)
	if not data:
		return {}
	return data[0]


@app.put("/profile")
def update_profile(
	payload: ProfileUpdate, authorization: str | None = Header(default=None)
):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	user_id = get_user_id(access_token)
	body = {
		"id": user_id,
		"full_name": payload.full_name,
		"age": payload.age,
		"gender": payload.gender,
	}
	data = supabase_request(
		"POST",
		"/rest/v1/profiles",
		access_token=access_token,
		json=body,
		extra_headers={
			"Prefer": "resolution=merge-duplicates,return=representation"
		},
	)
	return data[0] if data else {}


@app.get("/history")
def list_history(authorization: str | None = Header(default=None)):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	data = supabase_request(
		"GET",
		"/rest/v1/history",
		access_token=access_token,
		params={"select": "*", "order": "created_at.desc", "limit": "20"},
	)
	return data or []


@app.post("/history")
def create_history(
	payload: HistoryCreate, authorization: str | None = Header(default=None)
):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	user_id = get_user_id(access_token)
	body = {
		"user_id": user_id,
		"symptoms": payload.symptoms,
		"predicted_disease": payload.predicted_disease,
		"confidence": payload.confidence,
		"description": payload.description,
	}
	data = supabase_request(
		"POST",
		"/rest/v1/history",
		access_token=access_token,
		json=body,
		extra_headers={"Prefer": "return=representation"},
	)
	return data[0] if data else {}


@app.delete("/history/{history_id}")
def delete_history(
	history_id: int, authorization: str | None = Header(default=None)
):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	_ = get_user_id(access_token)
	data = supabase_request(
		"DELETE",
		"/rest/v1/history",
		access_token=access_token,
		params={"id": f"eq.{history_id}"},
		extra_headers={"Prefer": "return=representation"},
	)
	return data[0] if data else {}


@app.delete("/history")
def clear_history(authorization: str | None = Header(default=None)):
	if not authorization:
		raise HTTPException(status_code=401, detail="Missing Authorization header.")
	access_token = authorization.replace("Bearer ", "").strip()
	user_id = get_user_id(access_token)
	data = supabase_request(
		"DELETE",
		"/rest/v1/history",
		access_token=access_token,
		params={"user_id": f"eq.{user_id}"},
		extra_headers={"Prefer": "return=representation"},
	)
	return {"deleted": len(data or [])}
