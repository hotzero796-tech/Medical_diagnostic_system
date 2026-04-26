"""
state_handler.py -- OOP session and state management.

Keeps all mutable consultation state here so the functional and logic
layers can stay stateless. One class per concern.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set


# ── VitalSigns ────────────────────────────────────────────────────────────────

class VitalSigns:
    """Patient vital sign measurements (NEWS2 parameter set). All fields optional."""

    def __init__(self):
        self.temperature_celsius: Optional[float] = None
        self.heart_rate_bpm: Optional[int] = None
        self.systolic_bp: Optional[int] = None
        self.diastolic_bp: Optional[int] = None
        self.oxygen_saturation: Optional[float] = None
        self.respiration_rate: Optional[int] = None
        self.on_supplemental_o2: bool = False
        self.acvpu: str = "A"

    # ── NEWS2 scoring ─────────────────────────────────────────────────────────

    def news2Score(self) -> int:
        score = 0

        if self.respiration_rate is not None:
            rr = self.respiration_rate
            if rr <= 8:       score += 3
            elif rr <= 11:    score += 1
            elif rr <= 20:    score += 0
            elif rr <= 24:    score += 2
            else:             score += 3

        if self.oxygen_saturation is not None:
            spo2 = self.oxygen_saturation
            if spo2 <= 91:    score += 3
            elif spo2 <= 93:  score += 2
            elif spo2 <= 95:  score += 1

        if self.on_supplemental_o2:
            score += 2

        if self.systolic_bp is not None:
            sbp = self.systolic_bp
            if sbp <= 90:     score += 3
            elif sbp <= 100:  score += 2
            elif sbp <= 110:  score += 1
            elif sbp <= 219:  score += 0
            else:             score += 3

        if self.heart_rate_bpm is not None:
            hr = self.heart_rate_bpm
            if hr <= 40:      score += 3
            elif hr <= 50:    score += 1
            elif hr <= 90:    score += 0
            elif hr <= 110:   score += 1
            elif hr <= 130:   score += 2
            else:             score += 3

        if self.acvpu.upper() != "A":
            score += 3

        if self.temperature_celsius is not None:
            t = self.temperature_celsius
            if t <= 35.0:     score += 3
            elif t <= 36.0:   score += 1
            elif t <= 38.0:   score += 0
            elif t <= 39.0:   score += 1
            else:             score += 2

        return score

    def news2Risk(self) -> str:
        score = self.news2Score()
        if score >= 7:   return "HIGH  -- urgent response required"
        elif score >= 5: return "MEDIUM -- increased monitoring"
        else:            return "LOW"

    # ── classification helpers ────────────────────────────────────────────────

    def isHighFever(self) -> bool:
        return self.temperature_celsius is not None and self.temperature_celsius >= 39.0

    def isMildFever(self) -> bool:
        return (
            self.temperature_celsius is not None
            and 37.5 <= self.temperature_celsius < 39.0
        )

    def isTachycardia(self) -> bool:
        return self.heart_rate_bpm is not None and self.heart_rate_bpm > 100

    def isHypertensive(self) -> bool:
        return self.systolic_bp is not None and self.systolic_bp >= 140

    def isHypoxic(self) -> bool:
        return self.oxygen_saturation is not None and self.oxygen_saturation < 94.0

    def asSymptoms(self) -> List[str]:
        """Translate NEWS2 readings into Prolog symptom tokens."""
        detected = []
        if self.isHighFever():
            detected.append("high_fever")
        elif self.isMildFever():
            detected.append("mild_fever")
        elif self.temperature_celsius is not None and self.temperature_celsius <= 35.0:
            detected.append("chills")
        if self.isTachycardia():
            detected.append("fast_heart_rate")
        if self.isHypertensive():
            detected.append("high_blood_pressure")
        if self.isHypoxic():
            detected.append("breathlessness")
        if self.respiration_rate is not None and (
            self.respiration_rate > 24 or self.respiration_rate <= 8
        ):
            if "breathlessness" not in detected:
                detected.append("breathlessness")
        if self.acvpu.upper() in ("C", "V", "P", "U"):
            detected.append("altered_sensorium")
        return detected

    def summary(self) -> str:
        parts = []
        if self.temperature_celsius is not None:
            parts.append(f"Temp: {self.temperature_celsius:.1f}C")
        if self.respiration_rate is not None:
            parts.append(f"RR: {self.respiration_rate} br/min")
        if self.heart_rate_bpm is not None:
            parts.append(f"HR: {self.heart_rate_bpm} bpm")
        if self.systolic_bp and self.diastolic_bp:
            parts.append(f"BP: {self.systolic_bp}/{self.diastolic_bp} mmHg")
        elif self.systolic_bp:
            parts.append(f"sBP: {self.systolic_bp} mmHg")
        if self.oxygen_saturation is not None:
            parts.append(f"SpO2: {self.oxygen_saturation:.1f}%")
        if self.on_supplemental_o2:
            parts.append("O2: supplemental")
        if self.acvpu != "A":
            parts.append(f"ACVPU: {self.acvpu}")
        if parts:
            news2 = self.news2Score()
            parts.append(f"NEWS2: {news2} ({self.news2Risk().split('--')[0].strip()})")
        return "  |  ".join(parts) if parts else "Not recorded"


# ── ConsultationEntry ─────────────────────────────────────────────────────────

class ConsultationEntry:
    """One Q&A exchange."""

    def __init__(self, symptom, question_asked, user_response, was_confirmed):
        self.symptom = symptom
        self.question_asked = question_asked
        self.user_response = user_response
        self.was_confirmed = was_confirmed
        self.timestamp = datetime.now()

    def display(self) -> str:
        if self.user_response.strip() in ("?", "unsure", "unknown", "skip"):
            tick = "?"
        else:
            tick = "Y" if self.was_confirmed else "N"
        label = self.symptom.replace("_", " ").title()
        return f"  [{tick}] {label:<40} -> {self.user_response}"


# ── ConsultationLog ───────────────────────────────────────────────────────────

class ConsultationLog:
    """Ordered list of Q&A entries for one consultation session."""

    def __init__(self) -> None:
        self.entries: List[ConsultationEntry] = []
        self.asked_symptoms: Set[str] = set()

    def append(self, entry: ConsultationEntry) -> None:
        self.entries.append(entry)
        self.asked_symptoms.add(entry.symptom)

    def hasAsked(self, symptom: str) -> bool:
        return symptom in self.asked_symptoms

    def confirmedSymptoms(self) -> List[str]:
        return [e.symptom for e in self.entries if e.was_confirmed]

    def deniedSymptoms(self) -> List[str]:
        return [e.symptom for e in self.entries if not e.was_confirmed]

    def size(self) -> int:
        return len(self.entries)

    def exportJson(self) -> str:
        """Serialize the full log to JSON."""
        return json.dumps(
            [
                {
                    "symptom": e.symptom,
                    "question": e.question_asked,
                    "response": e.user_response,
                    "confirmed": e.was_confirmed,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.entries
            ],
            indent=2,
        )

    def printTranscript(self) -> None:
        print("\n  Consultation Transcript:")
        for entry in self.entries:
            print(entry.display())


# ── MedicalRecord ─────────────────────────────────────────────────────────────

class MedicalRecord:
    """All clinical data for one patient visit: symptoms, vitals, and diagnosis."""

    def __init__(self, patient_id: str) -> None:
        self.patient_id: str = patient_id
        self.confirmed: Set[str] = set()
        self.denied: Set[str] = set()
        self.skipped: Set[str] = set()
        self.vital_signs: VitalSigns = VitalSigns()
        self.diagnosis: Optional[str] = None
        self.confidence: float = 0.0
        self.severity_score: int = 0
        self.candidate_diagnoses: List[Dict] = []
        self.created_at = datetime.now()
        self.finalized_at = None

    # ── symptom management ────────────────────────────────────────────────────

    def confirm(self, symptom: str) -> None:
        self.confirmed.add(symptom)
        self.denied.discard(symptom)
        self.skipped.discard(symptom)

    def deny(self, symptom: str) -> None:
        self.denied.add(symptom)
        self.confirmed.discard(symptom)
        self.skipped.discard(symptom)

    def skip(self, symptom: str) -> None:
        self.skipped.add(symptom)
        self.confirmed.discard(symptom)
        self.denied.discard(symptom)

    def allKnown(self) -> set:
        """All symptoms that have been answered in any way (yes/no/unknown)."""
        return self.confirmed | self.denied | self.skipped

    # ── finalization ──────────────────────────────────────────────────────────

    def finalize(self, diagnosis: str, confidence: float, severity: int,
                 candidates: List[Dict] = None) -> None:
        self.diagnosis = diagnosis
        self.confidence = confidence
        self.severity_score = severity
        self.finalized_at = datetime.now()
        if candidates:
            self.candidate_diagnoses = candidates

    def durationSeconds(self) -> Optional[int]:
        if self.finalized_at:
            return int((self.finalized_at - self.created_at).total_seconds())
        return None

    def toDict(self) -> Dict:
        return {
            "patient_id": self.patient_id,
            "confirmedSymptoms": sorted(self.confirmed),
            "deniedSymptoms": sorted(self.denied),
            "vitals": self.vital_signs.summary(),
            "diagnosis": self.diagnosis,
            "confidence_pct": f"{self.confidence:.1%}",
            "severity_score": self.severity_score,
            "durationSeconds": self.durationSeconds(),
        }


# ── UserSession ───────────────────────────────────────────────────────────────

class UserSession:
    """Top-level session container. All state mutations go through here."""

    def __init__(self, patient_name: str, age: Optional[int] = None, gender: str = "Rather not say") -> None:
        self.session_id: str = uuid.uuid4().hex.upper()
        self.patient_name: str = patient_name
        self.age: Optional[int] = age
        self.gender: str = gender
        self.record: MedicalRecord = MedicalRecord(patient_id=self.session_id)
        self.log = ConsultationLog()
        self.is_active: bool = True

    # ── core API ──────────────────────────────────────────────────────────────

    def recordExchange(self, symptom: str, question: str, response: str) -> bool:
        """Log one Q&A exchange; returns True if confirmed, False otherwise."""
        yesTokens  = {"yes", "y", "yeah", "yep", "yup", "true", "sure", "definitely", "absolutely"}
        skipTokens = {"?", "unsure", "unknown", "skip", "idk", "not sure", "dont know"}

        cleaned   = response.strip().lower()
        confirmed = cleaned in yesTokens
        skipped   = cleaned in skipTokens

        entry = ConsultationEntry(
            symptom=symptom,
            question_asked=question,
            user_response=response,
            was_confirmed=confirmed,
        )
        self.log.append(entry)

        if confirmed:
            self.record.confirm(symptom)
        elif skipped:
            self.record.skip(symptom)
        else:
            self.record.deny(symptom)

        return confirmed

    def hasBeenAsked(self, symptom: str) -> bool:
        return self.log.hasAsked(symptom)

    def finalize(self, diagnosis: str, confidence: float, severity: int,
                 candidates: List[Dict] = None) -> None:
        self.record.finalize(diagnosis, confidence, severity, candidates)
        self.is_active = False

    # ── reporting ─────────────────────────────────────────────────────────────

    def generateReport(self) -> str:
        """Build a plain-text summary of the consultation."""
        r = self.record
        age_str = f" (Age: {self.age})" if self.age else ""
        diag_str = (r.diagnosis or "Undetermined").replace("_", " ").upper()
        conf_str = f"{r.confidence:.1%}" if r.confidence else "N/A"
        sev = r.severity_score

        severity_label = (
            "CRITICAL" if sev >= 30 else
            "HIGH"     if sev >= 18 else
            "MODERATE" if sev >= 9  else
            "LOW"
        )

        lines = [
            "=" * 58,
            "  MEDICAL CONSULTATION REPORT",
            "=" * 58,
            f"  Session ID   : {self.session_id}",
            f"  Patient      : {self.patient_name}{age_str}",
            *([] if self.gender == "Rather not say" else [f"  Gender       : {self.gender}"]),
            f"  Date         : {r.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"  Duration     : {r.durationSeconds() or 'N/A'} seconds",
            f"  Vitals       : {r.vital_signs.summary()}",
            "",
            f"  CONFIRMED SYMPTOMS ({len(r.confirmed)}):",
        ]

        for sym in sorted(r.confirmed):
            lines.append(f"    + {sym.replace('_', ' ').title()}")

        if r.denied:
            lines += ["", f"  DENIED SYMPTOMS ({len(r.denied)}):"]
            for sym in sorted(r.denied):
                lines.append(f"    - {sym.replace('_', ' ').title()}")

        lines += [
            "",
            "=" * 58,
            f"  DIAGNOSIS    : {diag_str}",
            f"  CONFIDENCE   : {conf_str}",
            f"  SEVERITY     : {severity_label}  (weighted score: {sev})",
            "=" * 58,
            "",
            "  DISCLAIMER: This is an AI-assisted screening tool only.",
            "  Always consult a licensed medical professional.",
            "=" * 58,
        ]

        return "\n".join(lines)
