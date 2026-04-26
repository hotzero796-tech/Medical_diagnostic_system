"""
patient_history.py -- Lightweight session-history persistence.

Stores past consultation summaries in patient_history.json so returning
patients can be recognised and their history surfaced to the clinician.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

dataDir    = Path(__file__).parent / "patient_data"
dataDir.mkdir(exist_ok=True)
historyFile = dataDir / "patient_history.json"


def historyKey(name: str) -> str:
    return name.strip().lower()


def loadHistory() -> Dict:
    if not historyFile.exists():
        return {}
    try:
        return json.loads(historyFile.read_text(encoding="utf-8"))
    except Exception:
        return {}


def saveHistory(data: Dict) -> None:
    historyFile.write_text(json.dumps(data, indent=2), encoding="utf-8")


def getPatient(name: str) -> Optional[Dict]:
    """Return stored history for a patient, or None if first visit."""
    return loadHistory().get(historyKey(name))


def recordVisit(
    name:      str,
    diagnosis: str,
    confirmed: List[str],
    severity:  int,
    candidates: List[Dict] = None,
    gender: str = "Rather not say",
) -> None:
    """Append a completed consultation to the patient's history."""
    data  = loadHistory()
    k     = historyKey(name)
    entry = data.get(k, {"name": name, "visits": []})
    entry["gender"] = gender

    entry["visits"].append({
        "date":       datetime.now().isoformat(),
        "diagnosis":  diagnosis,
        "confirmed":  confirmed,
        "severity":   severity,
        "candidates": candidates or [],
    })
    entry["last_visit"]     = datetime.now().isoformat()
    entry["last_diagnosis"] = diagnosis
    data[k] = entry
    saveHistory(data)


def visitCount(name: str) -> int:
    p = getPatient(name)
    return len(p["visits"]) if p else 0


def chronicSymptoms(name: str, min_visits: int = 2) -> List[str]:
    """Symptoms confirmed in at least min_visits past consultations."""
    p = getPatient(name)
    if not p or len(p["visits"]) < min_visits:
        return []
    counts: Counter = Counter()
    for v in p["visits"]:
        for s in v.get("confirmed", []):
            counts[s] += 1
    return [s for s, n in counts.items() if n >= min_visits]


def summary(name: str) -> Optional[str]:
    """One-line human-readable summary for display on registration."""
    p = getPatient(name)
    if not p or not p["visits"]:
        return None
    n     = len(p["visits"])
    diag  = p.get("last_diagnosis", "unknown").replace("_", " ").title()
    date  = p.get("last_visit", "")[:10]
    visits_word = "visit" if n == 1 else "visits"
    return f"Returning patient — {n} previous {visits_word}. Last: {diag} ({date})"
