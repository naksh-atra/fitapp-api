# FitApp Configuration Files

## Architecture

### Prescriptions (YAML)
Training parameters for each goal: sets, reps, tempo, rest, intensity.

**Files**:
- `prescriptions/hypertrophy.yaml` - Muscle building parameters
- `prescriptions/strength.yaml` - Maximal strength parameters  
- `prescriptions/endurance.yaml` - Cardiovascular endurance parameters
- `prescriptions/fatloss.yaml` - Fat loss training parameters

**Source**: Converted from prescription PDFs in KB repo  
**Usage**: Load at app startup for clean, version-controlled parameters

---

### Research Knowledge (FAISS)
Exercise library, selection logic, and progression strategies live in FAISS indexes.

**Location**: `data/index/v1/`  
**Source**: Research PDFs in KB repo  
**Usage**: Semantic queries at runtime ("best exercises for hypertrophy chest")

---

## Current Focus (Days 3-6)

Populate **prescriptions/** YAML files only.

Other directories (`exercises/`, `selection_rules/`, `progressions/`) are placeholders for potential future use - current plan uses FAISS for this data.

---

## Update Workflow

1. **Source PDFs updated** in KB repo
2. **Convert** prescription PDFs to YAML (manual for now)
3. **Copy** YAML to `config/prescriptions/`
4. **Commit** to fitapp repo
5. **Restart app** to load new configs

## Status (Dec 2025)

- [x] Directory structure created (Day 2)
- [ ] Prescription YAMLs populated (Days 3-6)
- [ ] FAISS indexes updated with research PDFs (Days 7+)
