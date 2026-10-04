"""Phishing detection web app.

Serves a prediction page (index.html) and a small JSON API on top of the
model produced by `python main.py` (final_model/model.pkl + preprocessor.pkl).
Run locally:  python app.py   ->  http://localhost:7860
"""
import io
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import url_features

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))  # lets pickle find the `networksecurity` package

MODEL_PATH = BASE / "final_model" / "model.pkl"
PRE_PATH = BASE / "final_model" / "preprocessor.pkl"

# (column name, plain-language label, group) in the exact order of your dataset.
FEATURES = [
    ("having_IP_Address", "Uses an IP address instead of a domain name", "Web address"),
    ("URL_Length", "Web address is unusually long", "Web address"),
    ("Shortining_Service", "Uses a link shortener", "Web address"),
    ("having_At_Symbol", "Contains an @ symbol", "Web address"),
    ("double_slash_redirecting", "Has a // redirect inside the address", "Web address"),
    ("Prefix_Suffix", "Domain contains a dash (-)", "Web address"),
    ("having_Sub_Domain", "Has many sub-domains", "Web address"),
    ("SSLfinal_State", "HTTPS certificate is valid and trusted", "Security and reputation"),
    ("Domain_registeration_length", "Domain is registered for a long time", "Security and reputation"),
    ("Favicon", "Favicon loads from the same domain", "Page content"),
    ("port", "Uses a standard port", "Web address"),
    ("HTTPS_token", "Domain name does not fake 'https'", "Web address"),
    ("Request_URL", "Images and media load from the same domain", "Page content"),
    ("URL_of_Anchor", "Links stay on the same domain", "Page content"),
    ("Links_in_tags", "Meta/script links stay on the same domain", "Page content"),
    ("SFH", "Form submits to the same domain", "Page content"),
    ("Submitting_to_email", "Form does not submit to an email address", "Page content"),
    ("Abnormal_URL", "Address matches the registered host name", "Web address"),
    ("Redirect", "Does not redirect many times", "Web address"),
    ("on_mouseover", "Status bar is not changed on mouse-over", "Page content"),
    ("RightClick", "Right-click is not disabled", "Page content"),
    ("popUpWidnow", "No pop-ups asking for details", "Page content"),
    ("Iframe", "No hidden iframes", "Page content"),
    ("age_of_domain", "Domain is old (6+ months)", "Security and reputation"),
    ("DNSRecord", "Domain has a DNS record", "Security and reputation"),
    ("web_traffic", "Site has healthy web traffic", "Security and reputation"),
    ("Page_Rank", "Site has a good page rank", "Security and reputation"),
    ("Google_Index", "Site is indexed by Google", "Security and reputation"),
    ("Links_pointing_to_page", "Other sites link to this page", "Security and reputation"),
    ("Statistical_report", "Not listed in phishing reports", "Security and reputation"),
]
FEATURE_NAMES = [f[0] for f in FEATURES]

MODEL, PRE, LOAD_ERROR = None, None, None


def _load(path: Path):
    with open(path, "rb") as fh:
        return pickle.load(fh)


def load_artifacts():
    global MODEL, PRE, LOAD_ERROR
    try:
        MODEL = _load(MODEL_PATH)
        PRE = _load(PRE_PATH) if PRE_PATH.exists() else None
        LOAD_ERROR = None
    except Exception as exc:  # shown on the page so problems are easy to spot
        MODEL, PRE, LOAD_ERROR = None, None, f"{type(exc).__name__}: {exc}"


app = FastAPI(title="Phishing Detector")
load_artifacts()


def run_model(df: pd.DataFrame):
    if MODEL is None:
        raise HTTPException(503, f"Model not loaded. {LOAD_ERROR}")
    missing = [c for c in FEATURE_NAMES if c not in df.columns]
    if missing:
        raise HTTPException(422, "Missing columns: " + ", ".join(missing))
    df = df[FEATURE_NAMES].apply(pd.to_numeric, errors="coerce")

    # Works with a bundled NetworkModel(preprocessor, model) or a plain estimator.
    pre = getattr(MODEL, "preprocessor", None)
    if pre is None:
        pre = PRE
    inner = getattr(MODEL, "model", MODEL)
    X = pre.transform(df) if pre is not None else df.values
    preds = inner.predict(X)

    phish_prob = [None] * len(preds)
    try:
        classes = list(inner.classes_)
        label = 0 if 0 in classes else -1  # training maps phishing (-1) to 0
        phish_prob = inner.predict_proba(X)[:, classes.index(label)].tolist()
    except Exception:
        pass
    # 1 = legitimate; 0 or -1 = phishing
    return [(int(p) in (0, -1)) for p in preds], phish_prob


@app.get("/")
def index():
    return FileResponse(BASE / "index.html")


@app.get("/health")
def health():
    return {"model_loaded": MODEL is not None, "error": LOAD_ERROR}


@app.get("/api/features")
def features():
    return {"features": [{"name": n, "label": l, "group": g} for n, l, g in FEATURES]}


@app.post("/api/predict")
def predict(payload: dict[str, int]):
    bad = [k for k, v in payload.items() if k in FEATURE_NAMES and v not in (-1, 0, 1)]
    if bad:
        raise HTTPException(422, "Values must be -1, 0 or 1: " + ", ".join(bad))
    flags, probs = run_model(pd.DataFrame([payload]))
    return {"phishing": flags[0], "phishing_probability": probs[0]}


class UrlIn(BaseModel):
    url: str


@app.post("/api/scan-url")
def scan_url(body: UrlIn):
    try:
        result = url_features.extract(body.url)
    except url_features.ScanError as exc:
        raise HTTPException(400, str(exc))
    flags, probs = run_model(pd.DataFrame([result["features"]]))
    return {**result, "phishing": flags[0], "phishing_probability": probs[0]}


@app.post("/api/predict-csv")
async def predict_csv(file: UploadFile = File(...)):
    try:
        df = pd.read_csv(io.BytesIO(await file.read()))
    except Exception:
        raise HTTPException(400, "Could not read that file as CSV.")
    if df.empty:
        raise HTTPException(400, "The CSV has no rows.")
    flags, probs = run_model(df)
    rows = [
        {"row": i + 1, "verdict": "phishing" if f else "legitimate", "phishing_probability": p}
        for i, (f, p) in enumerate(zip(flags, probs))
    ]
    n_phish = int(np.sum(flags))
    return {"total": len(rows), "phishing": n_phish, "legitimate": len(rows) - n_phish, "rows": rows[:5000]}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
