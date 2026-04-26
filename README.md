# Medical Diagnostic System

### A Multi-Paradigm Rule-Based Medical Expert System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![SWI-Prolog](https://img.shields.io/badge/SWI--Prolog-Logic%20Engine-E61B23?style=for-the-badge&logo=swi-prolog&logoColor=white)](https://www.swi-prolog.org/)
[![Common Lisp](https://img.shields.io/badge/Common%20Lisp-SBCL-9C8AA5?style=for-the-badge&logo=lisp&logoColor=white)](https://www.sbcl.org/)
[![Knowledge Base](https://img.shields.io/badge/Rules-4%2C925-2EA44F?style=for-the-badge)]()
[![Conditions](https://img.shields.io/badge/Conditions-41-orange?style=for-the-badge)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge)]()

A desktop diagnostic assistant that converses with a patient about their symptoms, computes a NEWS2 clinical risk score from optional vital signs, and returns a ranked list of likely conditions with recommended precautions. It deliberately combines three paradigms: **Object-Oriented (Python)**, **Functional (Common Lisp / SBCL)**, and **Logic (SWI-Prolog)**, with each paradigm responsible for a distinct concern.

[**Live Documentation**](https://hotzero796-tech.github.io/Medical_diagnostic_system/) · [**Report a Bug**](https://github.com/hotzero796-tech/Medical_diagnostic_system/issues) · [**Request a Feature**](https://github.com/hotzero796-tech/Medical_diagnostic_system/issues)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Concurrency Model](#concurrency-model)
- [Outputs and Persistence](#outputs-and-persistence)
- [Limitations](#limitations)
- [License](#license)

---

## Overview

The Medical Diagnostic System is a desktop application that produces preliminary differential diagnoses from a free-text symptom description and an optional set of vital signs. It is not a substitute for clinical judgement; it is a triage aid that demonstrates how three programming paradigms can collaborate on a non-trivial real-world problem.

The system is built around three complementary engines. A Python OOP layer owns the GUI, the patient session, and inter-paradigm orchestration. A Common Lisp pipeline performs deterministic, side-effect-free natural-language processing on the user's symptom text. A SWI-Prolog knowledge base of **4,925 hand-curated rules covering 41 conditions** drives the diagnostic decision tree, follow-up questions, exclusions, and final ranked diagnosis. Vital signs are scored using the Royal College of Physicians' **NEWS2** standard (2017).

A defining design principle is paradigm honesty: no paradigm is a thin wrapper around another. Each layer follows the idioms of its language, with immutable transformations in Lisp, declarative facts and rules in Prolog, and encapsulated state in Python.

---

## Key Features

- **Plain-English symptom input.** Patients describe symptoms in their own words; the Lisp pipeline translates that text into canonical symbolic tokens for inference.
- **NEWS2 clinical risk scoring.** Optional vital signs (temperature, respiration rate, heart rate, systolic BP, SpO2, supplemental O2, ACVPU alertness) are converted into the Royal College of Physicians National Early Warning Score 2.
- **Interactive Q-and-A consultation.** The Prolog engine selects follow-up questions one at a time, with three answer types: Yes, No, and Not sure.
- **Ranked differential diagnosis.** Returns a prioritised list of candidate conditions with confidence scores rather than a single answer.
- **Per-diagnosis precautions.** Recommended self-care, escalation criteria, and red flags are surfaced for each candidate diagnosis.
- **Triple-format reports.** Every consultation is persisted as plain text, structured JSON, and an Excel workbook.
- **Returning-patient recognition.** Patients are recognised by name, and any chronic symptoms (those confirmed in two or more prior visits) are surfaced at session start.
- **Non-blocking inference.** Long-running Prolog queries run on a worker thread so the GUI never freezes during a consultation.
- **Fully local and offline.** No network calls, no cloud dependency, and no machine learning. The decision logic is entirely deterministic and auditable.

---

## System Architecture

The application is organised as four layers. The presentation layer is the Tkinter GUI. Below it, the Python OOP layer holds session and conversation state. Two specialist engines hang off the side of the OOP layer: the Lisp NLP pipeline and the Prolog inference engine. Both are launched as subprocesses on demand.

```
+----------------------------------------------------------------------+
|                  PRESENTATION LAYER (Tkinter)                        |
|       DiagnosticGUI    DoctorCanvas    Result panels                 |
+--------------------------------+-------------------------------------+
                                 |
                                 v
+----------------------------------------------------------------------+
|              OOP SESSION AND STATE LAYER (Python)                    |
|  UserSession   MedicalRecord   ConsultationLog   VitalSigns          |
|  patient_history (JSON)        consultation_log (Excel/TXT)          |
+-----------------+-----------------------------+----------------------+
                  |                             |
                  v                             v
+--------------------------+      +----------------------------------+
|  FUNCTIONAL LAYER (Lisp) |      |       LOGIC LAYER (Prolog)       |
|  input_processor.lisp    |      |  diagnostic_engine.pl            |
|  pure NLP pipeline       |      |  diagnosis.pl  (4,925 rules)     |
|  diagnostic weights      |      |  symptoms_descriptions.pl        |
|  no I/O, no mutable state|      |  solutions.pl                    |
+--------------------------+      +----------------------------------+
```

---

## Technology Stack

| Layer | Technology | Responsibility |
|-------|-----------|----------------|
| Presentation | Tkinter | Cross-platform desktop GUI |
| Session and state (OOP) | Python 3.9+ | Patient session, conversation log, vital signs, orchestration |
| Functional NLP | Common Lisp (SBCL) | Tokenisation, normalisation, symptom canonicalisation, weight tables |
| Logic and inference | SWI-Prolog | Knowledge base, decision tree, follow-up questions, exclusions, ranking |
| Persistence | openpyxl + JSON + plain text | Per-consultation reports in three formats |
| Clinical scoring | NEWS2 (RCP 2017) | Severity scoring from vital signs |

---

## Project Structure

```
Medical_diagnostic_system/
|-- LICENSE                            # MIT license
|-- README.md                          # This file
\-- paradgism medical/
    |-- gui.py                        # Tkinter GUI, all visual presentation
    |-- state_handler.py              # OOP classes: UserSession, MedicalRecord, etc.
    |-- consultation_log.py           # Excel report writer (openpyxl)
    |-- patient_history.py            # JSON-based patient history persistence
    |-- input_processor.lisp          # Lisp NLP pipeline (canonical implementation)
    |-- input_processor_bridge.py     # Thin Python bridge to SBCL
    |-- prolog_bridge.py              # Python bridge to SWI-Prolog
    |-- diagnostic_engine.pl          # Prolog meta-rules: questions, follow-ups, exclusions
    |-- diagnosis.pl                  # Diagnosis rule base (4,925 rules, 41 conditions)
    |-- symptoms_descriptions.pl      # Disease descriptions
    |-- solutions.pl                  # Precaution and self-care rules
    |-- requirements.txt              # Python deps + SBCL/SWI-Prolog install notes
    \-- patient_data/                 # Per-consultation reports (txt/json/xlsx)
```

The Python OOP layer is built around five classes: **UserSession** (top-level container, holds session UUID, patient identity, and references to the medical record and consultation log), **MedicalRecord** (all clinical data for one visit), **VitalSigns** (vital sign measurements and NEWS2 scoring), **ConsultationLog** (ordered Q-and-A history with JSON serialisation), and **ConsultationEntry** (a single Q-and-A exchange).

---

## Installation

### Prerequisites

You will need three runtimes available on your `PATH`:

| Tool | Verify | Install |
|------|--------|---------|
| Python 3.9+ | `python --version` | https://www.python.org/downloads/ |
| SWI-Prolog | `swipl --version` | https://www.swi-prolog.org/Download.html or `winget install SWI-Prolog.SWI-Prolog` |
| SBCL (Steel Bank Common Lisp) | `sbcl --version` | https://www.sbcl.org/platform-table.html or `winget install SBCL.SBCL` |

### Setup

```bash
git clone https://github.com/hotzero796-tech/Medical_diagnostic_system.git
cd Medical_diagnostic_system/paradgism\ medical

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

The application is designed to run fully offline. No network access is required at runtime.

---

## Usage

From the `paradgism medical/` directory, launch the GUI:

```bash
python gui.py
```

A typical consultation proceeds as follows:

1. The patient enters their name. If the name has been seen before, a one-line history summary and any chronic symptoms are surfaced.
2. The patient describes their symptoms in plain English (for example, "I have a fever and my throat hurts").
3. Optional vital signs are entered. The system computes a NEWS2 score and converts abnormal readings into Prolog symptom tokens.
4. The Prolog engine selects follow-up questions one at a time. The patient answers Yes, No, or Not sure.
5. The system stops asking as soon as it has enough evidence and presents a ranked list of candidate diagnoses with confidence scores.
6. Recommended precautions are shown for the most likely diagnosis, with one-click access to precautions for each differential.
7. The complete consultation is saved as plain text, JSON, and an Excel workbook in `patient_data/`.

A single consultation typically completes in under five minutes for a co-operative user.

---

## How It Works

**1. Functional layer (Lisp).** `input_processor.lisp` implements a pure, side-effect-free symptom-canonicalisation pipeline. Given the same input string, it always produces the same canonical list of symptom tokens. There is no I/O, no mutable state, and no time dependence inside the pipeline. The same module also exposes the diagnostic weight tables used by the Prolog layer for prioritisation and severity scoring.

**2. Bridges (Python).** `input_processor_bridge.py` and `prolog_bridge.py` spawn SBCL and SWI-Prolog respectively as subprocesses, marshal queries over stdio, and parse the responses back into Python data structures. The bridges are deliberately thin so that the paradigm boundaries stay visible.

**3. Logic layer (Prolog).** `diagnostic_engine.pl` defines the meta-rules that select the next question, apply follow-up logic, and enforce exclusions. `diagnosis.pl` holds the 4,925-rule knowledge base covering 41 conditions. `solutions.pl` maps each diagnosis to recommended precautions, and `symptoms_descriptions.pl` provides patient-facing descriptions.

**4. NEWS2 scoring (Python).** `VitalSigns` validates measurements, computes the NEWS2 score using the 2017 Royal College of Physicians rules, and converts abnormal vitals into Prolog symptom tokens that participate in inference alongside patient-reported symptoms.

**5. Session and state (Python OOP).** `state_handler.py` defines the five classes that own session state. State mutation goes through `UserSession`, which provides a single auditable point of entry.

**6. Persistence.** `consultation_log.py` writes Excel workbooks via openpyxl. `patient_history.py` maintains a JSON store on disk and exposes `summary(name)` for the returning-patient feature.

---

## Concurrency Model

The system uses three kinds of thread:

- **The main thread** owns the Tk root window and runs the event loop. All GUI updates happen here.
- **A worker thread** executes long-running Prolog queries so the UI never freezes. A typical query takes between 500 ms and 2 seconds, which would otherwise block visibly on the main thread.
- **Subprocess threads** are managed by Python's `subprocess` module for SBCL and SWI-Prolog calls.

Results are marshalled back to the main thread through a thread-safe queue and rendered when the next Tk event loop tick fires. This keeps the system responsive while inference is running.

---

## Outputs and Persistence

Each consultation is written to disk in three formats:

- **Plain text.** A human-readable transcript suitable for printing.
- **JSON.** A structured record for downstream tooling, including session UUID, timestamps, confirmed and denied symptom sets, vital signs, NEWS2 score, ranked candidate diagnoses, confidence values, and the full Q-and-A trace.
- **Excel (`.xlsx`).** A formatted workbook generated with openpyxl, suitable for clinical review.

The patient history store is a JSON file per patient. Symptoms confirmed in two or more past visits are flagged as chronic and surfaced at the start of each new session.

---

## Limitations

- **Knowledge base is finite and English-only.** Conditions outside the 41 covered cannot be diagnosed.
- **Hand-curated weights.** There is no learning component; the system does not improve as it sees more patients.
- **Limited demographics.** Only age and self-reported gender are modelled. Risk stratification by ethnicity, comorbidities, or family history is out of scope.
- **NEWS2 caveat.** NEWS2 was developed for adults in acute care. Applying it to walk-in cases of chronic conditions is a slight off-label use, but it remains better than no scoring at all.
- **External runtimes required.** SBCL and SWI-Prolog must be installed separately and on PATH. The application cannot bundle them.
- **Subprocess startup latency.** A persistent SBCL/swipl daemon could reduce per-query overhead but was out of scope for this iteration.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full text.
