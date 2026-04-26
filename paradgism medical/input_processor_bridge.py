"""
input_processor_bridge.py -- Thin bridge to the Lisp NLP engine.

The canonical implementation is input_processor.lisp (SBCL).
This file calls SBCL at runtime and provides Python utility functions
(weight lookup, severity scoring, display helpers) used by the GUI.
"""

import subprocess
import re
from functools import reduce
from pathlib import Path
from typing import Dict, List, Optional, Tuple

RawInput     = str
SymptomToken = str
WeightedPair = Tuple[SymptomToken, int]

lispFile    = Path(__file__).parent / "input_processor.lisp"
lispTimeout = 15
sbclExe     = "sbcl"


# ── Lisp subprocess call ──────────────────────────────────────────────────────


symLine = re.compile(r'^[a-z][a-z_]*(?:\s+[a-z][a-z_]*)*$')


def parseLispOutput(stdout: str) -> Optional[List[str]]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if symLine.match(line):
            return line.split()
    return None


def extractSymptoms(raw: RawInput) -> List[SymptomToken]:
    """Run the Lisp NLP pipeline via SBCL and return canonical symptom tokens."""
    cmd = [
        sbclExe, "--noinform", "--non-interactive",
        "--eval", f'(load "{lispFile.as_posix()}")',
        "--eval", "(run-from-stdin)",
        "--eval", "(quit)",
    ]
    result = subprocess.run(
        cmd,
        input=raw.replace("\n", " "),
        capture_output=True,
        text=True,
        timeout=lispTimeout,
    )
    parsed = parseLispOutput(result.stdout)
    return parsed if parsed is not None else []


# ── Diagnostic weights ────────────────────────────────────────────────────────

def loadWeightsFromLisp() -> Dict[str, int]:
    cmd = [
        sbclExe, "--noinform", "--non-interactive",
        "--eval", f'(load "{lispFile.as_posix()}")',
        "--eval", "(dump-weights)",
        "--eval", "(quit)",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=lispTimeout)
    weights: Dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) == 2:
            try:
                weights[parts[0]] = int(parts[1])
            except ValueError:
                pass
    return weights

weights: Dict[str, int] = loadWeightsFromLisp()


def getWeight(symptom: SymptomToken) -> int:
    return weights.get(symptom, 3)


def prioritizeSymptoms(symptoms: List[SymptomToken]) -> List[SymptomToken]:
    return sorted(symptoms, key=getWeight, reverse=True)


def filterUnasked(
    candidates: List[SymptomToken],
    already_asked: List[SymptomToken],
) -> List[SymptomToken]:
    asked = set(already_asked)
    return list(filter(lambda s: s not in asked, candidates))


def computeSeverityScore(confirmed: List[SymptomToken]) -> int:
    return reduce(lambda acc, s: acc + getWeight(s), confirmed, 0)


def normalizeYesNo(response: RawInput) -> bool:
    yes = frozenset({"yes", "y", "yeah", "yep", "yup", "true", "sure", "absolutely", "definitely", "1"})
    return bool(set(response.strip().lower().split()) & yes)


def symptomDisplayName(symptom: SymptomToken) -> str:
    return symptom.replace("_", " ").title()
