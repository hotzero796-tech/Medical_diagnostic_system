"""
prolog_bridge.py -- Python-to-Prolog subprocess interface.

Serialises confirmed/denied symptoms into Prolog assertions, runs swipl,
and parses the result.

Confidence = sum(weight of matched expected symptoms) / sum(weight of all expected)
"""

import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from input_processor_bridge import getWeight, symptomDisplayName

prologDir  = Path(__file__).parent
enginePl   = prologDir / "diagnostic_engine.pl"
timeoutSec = 25

swiplExe = "swipl"


class PrologBridge:
    """Interface to the SWI-Prolog diagnostic knowledge base. Prolog is required."""

    def __init__(self, engine_path: Path = enginePl) -> None:
        self.engine_path = engine_path
        # Caches populated by a background preload thread
        self.questionCache:     Dict[str, str]       = {}
        self.redFlagCache:      List[str]             = []
        self.diseaseProfileCache: Dict[str, List[str]] = {}
        self.cacheLock = threading.Lock()

        threading.Thread(target=self.preloadCaches, daemon=True).start()

    def preloadCaches(self) -> None:
        """Background: load all question texts, red flags, and disease profiles from Prolog once."""
        questions = self.queryAllQuestionsViaSwipl()
        flags     = self.queryRedFlagsViaSwipl()
        profiles  = self.loadDiseaseProfilesViaSwipl()
        with self.cacheLock:
            if questions:
                self.questionCache = questions
            if flags:
                self.redFlagCache = flags
            if profiles:
                self.diseaseProfileCache = profiles

    # ── public API ────────────────────────────────────────────────────────────

    def getQuestionText(self, symptom: str) -> str:
        """Return question text for a symptom from Prolog.

        Falls back to a generated question if Prolog hasn't loaded yet or
        has no entry for this symptom.
        """
        with self.cacheLock:
            if symptom in self.questionCache:
                return self.questionCache[symptom]

        # Cache miss: try a synchronous single-symptom lookup
        text = self.querySingleQuestion(symptom)
        if text:
            with self.cacheLock:
                self.questionCache[symptom] = text
            return text

        return f"Do you have {symptomDisplayName(symptom)}?"

    def getRedFlags(self) -> List[str]:
        """Return the list of red-flag symptoms from Prolog's knowledge base."""
        with self.cacheLock:
            if self.redFlagCache:
                return list(self.redFlagCache)
        flags = self.queryRedFlagsViaSwipl()
        with self.cacheLock:
            if flags:
                self.redFlagCache = flags
        return flags or []

    def queryDiagnosis(
        self,
        confirmed: List[str],
        denied:    List[str],
    ) -> List[Tuple[str, float]]:
        """Return up to 3 (disease, confidence) pairs ranked by confidence, best first."""
        return self.queryViaSwipl(confirmed, denied)

    # ── SWI-Prolog subprocess ─────────────────────────────────────────────────

    def runSwipl(self, goal: str, timeout: int = timeoutSec) -> str:
        """Run goal via swipl and return stdout."""
        engine_posix = self.engine_path.as_posix()
        cmd = [
            swiplExe, "-q",
            "-g", f"consult('{engine_posix}'), {goal}",
            "-t", "halt",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout

    def buildPrologGoal(self, confirmed: List[str], denied: List[str]) -> str:
        asserts = "".join(
            [f"assert(known({s}, yes)), " for s in confirmed]
            + [f"assert(known({s}, no)),  " for s in denied]
        )
        return (
            f"assert(batch_mode), "
            f"{asserts}"
            f"diagnose_partial(Ds), "
            f"forall(member(D, Ds), (write(D), nl)), halt"
        )

    def queryViaSwipl(
        self,
        confirmed: List[str],
        denied:    List[str],
    ) -> List[Tuple[str, float]]:
        goal   = self.buildPrologGoal(confirmed, denied)
        output = self.runSwipl(goal)
        if not output:
            return []

        diseases = [
            ln.strip().lower().replace(" ", "_")
            for ln in output.splitlines()
            if ln.strip() and ln.strip() not in ("unknown", "false", "true")
        ]
        if not diseases:
            return []

        ranked = sorted(
            ((d, self.computeConfidence(d, confirmed)) for d in diseases),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:3]

    # ── confidence calculation ────────────────────────────────────────────────

    def loadDiseaseProfilesViaSwipl(self) -> Dict[str, List[str]]:
        """Load all disease_symptom/2 facts from Prolog as {disease: [symptoms]}."""
        goal = "forall(disease_symptom(D, S), format('~w\t~w~n', [D, S])), halt"
        output = self.runSwipl(goal)
        if not output:
            return {}
        profiles: Dict[str, List[str]] = {}
        for line in output.splitlines():
            if "\t" in line:
                disease, symptom = line.split("\t", 1)
                disease = disease.strip()
                symptom = symptom.strip()
                if disease and symptom:
                    profiles.setdefault(disease, []).append(symptom)
        return profiles

    def computeConfidence(
        self,
        disease:   str,
        confirmed: List[str],
    ) -> float:
        with self.cacheLock:
            expected = self.diseaseProfileCache.get(disease)
        if not expected:
            return 0.0

        confirmed_set  = set(confirmed)
        covered_weight = sum(getWeight(s) for s in expected if s in confirmed_set)
        total_weight   = sum(getWeight(s) for s in expected)

        if total_weight == 0:
            return 0.5

        return min(covered_weight / total_weight, 1.0)

    # ── follow-up and exclusion queries ──────────────────────────────────────

    def queryNextQuestion(
        self,
        asked:     List[str],
        confirmed: List[str],
        denied:    List[str],
        excluded:  set,
    ) -> Optional[str]:
        result = self.queryNextViaSwipl(asked, confirmed, denied)
        return result if result and result not in excluded else None

    def queryNextViaSwipl(
        self, asked: List[str], confirmed: List[str], denied: List[str]
    ) -> Optional[str]:
        asserts  = "".join(
            [f"assert(known({s}, yes)), " for s in confirmed]
            + [f"assert(known({s}, no)),  " for s in denied]
        )
        asked_pl = "[" + ", ".join(asked) + "]"
        goal = (
            f"assert(batch_mode), "
            f"{asserts}"
            f"best_next_question({asked_pl}, Next), "
            f"write(Next), nl, halt"
        )
        output = self.runSwipl(goal)
        out = output.strip()
        return out if out and out not in ("false", "unknown") else None

    def queryExclusions(self, denied_symptom: str) -> List[str]:
        goal = (
            f"assert(batch_mode), "
            f"get_exclusions({denied_symptom}, Es), "
            f"forall(member(E, Es), (write(E), nl)), halt"
        )
        output = self.runSwipl(goal)
        return [ln.strip() for ln in output.splitlines() if ln.strip()]

    def queryFollowups(self, symptom: str) -> List[str]:
        goal = (
            f"assert(batch_mode), "
            f"get_follow_ups({symptom}, Fs), "
            f"forall(member(F, Fs), (write(F), nl)), halt"
        )
        output = self.runSwipl(goal)
        return [ln.strip() for ln in output.splitlines() if ln.strip()]

    # ── question text and red-flag queries ───────────────────────────────────

    def queryAllQuestionsViaSwipl(self) -> Dict[str, str]:
        """Fetch all symptom_question/2 facts from Prolog as {atom: text}."""
        goal = (
            "forall(symptom_question(S, Q), "
            "format('~w\t~w~n', [S, Q])), halt"
        )
        output = self.runSwipl(goal)
        if not output:
            return {}
        questions: Dict[str, str] = {}
        for line in output.splitlines():
            if "\t" in line:
                sym, q = line.split("\t", 1)
                sym = sym.strip()
                q   = q.strip()
                if sym:
                    questions[sym] = q
        return questions

    def querySingleQuestion(self, symptom: str) -> Optional[str]:
        """Fetch question text for one symptom from Prolog."""
        goal = (
            f"( symptom_question({symptom}, Q) "
            f"-> write(Q) "
            f"; true ), nl, halt"
        )
        text = self.runSwipl(goal, timeout=10).strip()
        return text if text else None

    def queryRedFlagsViaSwipl(self) -> List[str]:
        """Fetch all red_flag/1 atoms from Prolog."""
        goal = "get_red_flags(Fs), forall(member(F, Fs), (write(F), nl)), halt"
        output = self.runSwipl(goal)
        if not output:
            return []
        return [ln.strip() for ln in output.splitlines() if ln.strip()]

    def status(self) -> str:
        return "PrologBridge active — inference engine: SWI-Prolog"
