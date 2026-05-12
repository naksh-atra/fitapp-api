"""
Workout Generator Engine v2.0
Science-based weekly plan generator powered by YAML prescriptions.

Splits by goal:
  hypertrophy → Push/Pull/Legs × 2  (PPL, 6 days)          Schoenfeld et al. 2016
  strength    → Daily Undulating Periodization (DUP, 4 days) Zourdos et al. 2016
  endurance   → Polarized 80/20  (5 days)                    Seiler 2010
  fatloss     → HIIT × 3 + Steady-state × 2  (5 days)       Alkahtani et al. 2023
"""

import yaml
import random
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

ACTIVE_RECOVERY_SESSION = {
    "session_name": "Active Recovery",
    "session_type": "rest",
    "exercises": [],
    "notes": "Light walking, stretching, foam rolling, or complete rest. Keep heart rate below 60% HRmax."
}

# ---------------------------------------------------------------------------
# Master exercise database - split by movement category and equipment
# ---------------------------------------------------------------------------
EXERCISE_DB: Dict[str, Dict[str, List[str]]] = {
    "gym": {
        "push_compound":          ["Barbell Bench Press", "Overhead Press", "Incline Dumbbell Press"],
        "pull_compound":          ["Barbell Row", "Pull Up", "Cable Row"],
        "legs_compound":          ["Back Squat", "Romanian Deadlift", "Leg Press"],
        "push_isolation":         ["Tricep Extension", "Lateral Raise", "Chest Fly"],
        "pull_isolation":         ["Bicep Curl", "Face Pull", "Rear Delt Fly"],
        "legs_isolation":         ["Leg Curl", "Leg Extension", "Calf Raise"],
        "strength_main":          ["Back Squat", "Bench Press", "Deadlift", "Overhead Press"],
        "strength_accessory":     ["Paused Squat", "Close-Grip Bench Press", "Deficit Deadlift", "Barbell Row"],
        "cardio_zone2":           ["Treadmill Run", "Rowing Machine", "Stationary Bike"],
        "cardio_threshold":       ["Rowing Machine", "Stationary Bike", "Stair Climber", "Elliptical"],
        "cardio_vo2max":          ["Treadmill Run", "Assault Bike", "Rowing Machine"],
        "cardio_steady":          ["Treadmill Run", "Stationary Bike", "Elliptical"],
        "hiit":                   ["Kettlebell Swing", "Thrusters", "Box Jumps", "Battle Ropes"],
    },
    "home": {
        "push_compound":          ["Push Up", "Pike Push Up", "Decline Push Up"],
        "pull_compound":          ["Inverted Row", "Door-Frame Pull Up", "Band Pull-Apart"],
        "legs_compound":          ["Goblet Squat", "Bulgarian Split Squat", "Hip Thrust"],
        "push_isolation":         ["Tricep Dips", "Diamond Push Up"],
        "pull_isolation":         ["Bodyweight Curl", "Resistance Band Curl"],
        "legs_isolation":         ["Glute Bridge", "Calf Raise (Bodyweight)", "Nordic Curl"],
        "strength_main":          ["Goblet Squat", "Pike Push Up", "Romanian Deadlift (Dumbbell)", "Dumbbell Press"],
        "strength_accessory":     ["Bulgarian Split Squat", "Single-Leg RDL", "Close-Grip Push Up", "Inverted Row"],
        "cardio_zone2":           ["Outdoor Run", "Jump Rope", "Step-Ups"],
        "cardio_threshold":       ["High Knees", "Jump Rope", "Step-Ups", "Bodyweight Squats"],
        "cardio_vo2max":          ["Outdoor Run", "Jump Rope", "Burpees"],
        "cardio_steady":          ["Outdoor Run", "Jump Rope", "Brisk Walk"],
        "hiit":                   ["Burpees", "Jump Squat", "Mountain Climbers", "Lunge Jumps"],
    }
}

# Experience → sets per exercise (used across hypertrophy and strength accessory)
SETS_BY_EXPERIENCE = {
    "beginner":     [3, 3],
    "intermediate": [3, 4],
    "advanced":     [4, 5],
}

# Experience → Zone 2 duration in minutes (endurance)
ZONE2_DURATION_BY_EXPERIENCE = {
    "beginner":     [20, 30],
    "intermediate": [30, 45],
    "advanced":     [45, 60],
}


class WorkoutGenerator:

    def __init__(self, config_dir: str = "config/prescriptions"):
        self.config_dir = Path(config_dir)
        self.prescriptions = self._load_all_prescriptions()

    # -----------------------------------------------------------------------
    # Prescription loading
    # -----------------------------------------------------------------------
    def _load_all_prescriptions(self) -> Dict[str, Dict]:
        goals = ["hypertrophy", "strength", "endurance", "fatloss"]
        prescriptions = {}
        for goal in goals:
            yaml_path = self.config_dir / f"{goal}.yaml"
            if yaml_path.exists():
                with open(yaml_path, "r", encoding="utf-8") as f:
                    prescriptions[goal] = yaml.safe_load(f)
                print(f"✓ Loaded {goal} prescription")
            else:
                print(f"⚠️  Missing {goal}.yaml")
        return prescriptions

    # -----------------------------------------------------------------------
    # Primary public API
    # -----------------------------------------------------------------------
    def generate_weekly_plan(
        self,
        goal: str,
        equipment: str = "gym",
        experience: str = "intermediate"
    ) -> Dict:
        """
        Generate a full Monday–Sunday weekly training plan.
        This is the primary method called by the API.
        """
        if goal not in self.prescriptions:
            raise ValueError(
                f"Goal '{goal}' not found. Available: {list(self.prescriptions.keys())}"
            )

        prescription = self.prescriptions[goal]
        db = EXERCISE_DB.get(equipment, EXERCISE_DB["gym"])

        if goal == "hypertrophy":
            plan = self._build_hypertrophy_week(prescription, db, experience)
        elif goal == "strength":
            plan = self._build_strength_week(prescription, db, experience)
        elif goal == "endurance":
            plan = self._build_endurance_week(prescription, db, experience)
        elif goal == "fatloss":
            plan = self._build_fatloss_week(prescription, db)
        else:
            raise ValueError(f"Unknown goal: {goal}")

        return {
            "goal":                    goal,
            "equipment":               equipment,
            "experience":              experience,
            "split_type":              plan["split_type"],
            "training_days_per_week":  plan["training_days_per_week"],
            "total_duration_minutes":  60,
            "weekly_volume_summary":   plan.get("weekly_volume_summary"),
            "dietary_disclaimer":      plan.get("dietary_disclaimer"),
            "notes":                   f"Evidence-based prescription from {prescription['metadata']['source_file']}",
            "prescription_source":     prescription["metadata"]["source_file"],
            "evidence_level":          prescription["metadata"]["evidence_level"],
            "weekly_plan":             plan["weekly_plan"],
        }

    # -----------------------------------------------------------------------
    # HYPERTROPHY - Push/Pull/Legs × 2  (6 days, Sunday rest)
    # -----------------------------------------------------------------------
    def _build_hypertrophy_week(
        self, prescription: Dict, db: Dict, experience: str
    ) -> Dict:
        p_compound  = prescription["hypertrophy"]["compound_lifts"]["parameters"]
        p_isolation = prescription["hypertrophy"]["isolation_lifts"]["parameters"]
        sets        = SETS_BY_EXPERIENCE.get(experience, [3, 4])

        def push_session(rep_scheme: str) -> Dict:
            """rep_scheme: 'strength' (6-8) or 'hypertrophy' (8-12)"""
            compound_reps = [6, 8] if rep_scheme == "strength" else [8, 12]
            return [
                self._make_compound(db["push_compound"][0], compound_reps, sets, p_compound,
                                    "Controlled 3s eccentric - maximize pectoral mechanical tension."),
                self._make_compound(db["push_compound"][1], compound_reps, sets, p_compound,
                                    "Drive elbows slightly forward; full lockout at the top."),
                self._make_isolation(db["push_isolation"][0], [10, 15], sets, p_isolation,
                                     "Full extension with 1s squeeze at peak contraction."),
                self._make_isolation(db["push_isolation"][1], [12, 20], sets, p_isolation,
                                     "Lead with elbows; keep torso upright and avoid swinging."),
            ]

        def pull_session(rep_scheme: str) -> Dict:
            compound_reps = [5, 8] if rep_scheme == "strength" else [8, 12]
            return [
                self._make_compound(db["pull_compound"][0], compound_reps, sets, p_compound,
                                    "Initiate with scapular retraction before elbow drive."),
                self._make_compound(db["pull_compound"][1], compound_reps, sets, p_compound,
                                    "Full dead-hang at bottom; chin clears bar at top."),
                self._make_isolation(db["pull_isolation"][0], [10, 15], sets, p_isolation,
                                     "Supinate at the top; avoid swinging the torso."),
                self._make_isolation(db["pull_isolation"][1], [12, 20], sets, p_isolation,
                                     "High elbow path - target posterior deltoid and rhomboids."),
            ]

        def legs_session(rep_scheme: str) -> Dict:
            compound_reps = [6, 8] if rep_scheme == "strength" else [8, 12]
            return [
                self._make_compound(db["legs_compound"][0], compound_reps, sets, p_compound,
                                    "Break parallel - load the glutes in the lengthened position."),
                self._make_compound(db["legs_compound"][1], compound_reps, sets, p_compound,
                                    "Hinge at the hip; maintain neutral spine throughout the ROM."),
                self._make_isolation(db["legs_isolation"][0], [10, 15], sets, p_isolation,
                                     "Full knee flexion - maximize hamstring stretch under load."),
                self._make_isolation(db["legs_isolation"][1], [12, 20], sets, p_isolation,
                                     "Controlled extension; pause 1s at peak to prevent momentum."),
            ]

        # Sets per muscle per week: 2 sessions × sets[1] sets × 2 exercises per session
        sets_per_muscle = f"{2 * sets[0] * 2}–{2 * sets[1] * 2} sets/week"

        return {
            "split_type": "Push / Pull / Legs (PPL × 2)",
            "training_days_per_week": 6,
            "weekly_volume_summary": {
                "chest":    sets_per_muscle,
                "back":     sets_per_muscle,
                "legs":     sets_per_muscle,
                "shoulders": f"{2 * sets[0]}–{2 * sets[1]} sets/week",
                "biceps":   f"{2 * sets[0]}–{2 * sets[1]} sets/week",
                "triceps":  f"{2 * sets[0]}–{2 * sets[1]} sets/week",
                "note":     "Based on 2 sessions per muscle group per week. Meets 10-20 sets/muscle/week threshold (Schoenfeld et al. 2016)."
            },
            "weekly_plan": {
                "monday":    {"session_name": "Push A - Strength Focus",   "session_type": "push",  "exercises": push_session("strength")},
                "tuesday":   {"session_name": "Pull A - Strength Focus",   "session_type": "pull",  "exercises": pull_session("strength")},
                "wednesday": {"session_name": "Legs A - Strength Focus",   "session_type": "legs",  "exercises": legs_session("strength")},
                "thursday":  {"session_name": "Push B - Hypertrophy Focus","session_type": "push",  "exercises": push_session("hypertrophy")},
                "friday":    {"session_name": "Pull B - Hypertrophy Focus","session_type": "pull",  "exercises": pull_session("hypertrophy")},
                "saturday":  {"session_name": "Legs B - Hypertrophy Focus","session_type": "legs",  "exercises": legs_session("hypertrophy")},
                "sunday":    dict(ACTIVE_RECOVERY_SESSION),
            }
        }

    # -----------------------------------------------------------------------
    # STRENGTH - Daily Undulating Periodization (DUP, 4 days)
    # -----------------------------------------------------------------------
    def _build_strength_week(
        self, prescription: Dict, db: Dict, experience: str
    ) -> Dict:
        p_main      = prescription["strength"]["main_lifts"]["parameters"]
        p_acc       = prescription["strength"]["accessory_lifts"]["parameters"]
        acc_sets    = SETS_BY_EXPERIENCE.get(experience, [3, 4])

        main_lifts  = db["strength_main"]       # [Squat, Bench, Deadlift, OHP]
        accessories = db["strength_accessory"]  # pool to pick from per session

        squat  = main_lifts[0]
        bench  = main_lifts[1]
        dead   = main_lifts[2]
        ohp    = main_lifts[3]

        def heavy(name: str, reps: List[int], pct: str, note: str) -> Dict:
            return {
                "name":        name,
                "type":        "main_competition",
                "sets":        [3, 4],
                "reps":        reps,
                "percent_1rm": pct,
                "rpe":         p_main["intensity_rpe"],
                "rest_seconds": [180, 300],
                "pro_notes":   note,
            }

        def volume(name: str, reps: List[int], pct: str, note: str) -> Dict:
            return {
                "name":        name,
                "type":        "main_competition",
                "sets":        [4, 5],
                "reps":        reps,
                "percent_1rm": pct,
                "rpe":         "7-8",
                "rest_seconds": [180, 240],
                "pro_notes":   note,
            }

        def accessory(name: str, note: str) -> Dict:
            return {
                "name":        name,
                "type":        "accessory",
                "sets":        acc_sets,
                "reps":        [3, 6],          # capped - never exceed 6 in a strength block
                "percent_1rm": p_acc["weight_1rm_percent"],
                "rpe":         p_acc["intensity_rpe"],
                "rest_seconds": [120, 180],
                "pro_notes":   note,
            }

        return {
            "split_type": "Daily Undulating Periodization (DUP)",
            "training_days_per_week": 4,
            "weekly_plan": {
                "monday": {
                    "session_name": "Squat - Heavy Day (DUP)",
                    "session_type": "strength_lower_heavy",
                    "exercises": [
                        heavy(squat, [2, 3], "87-93% 1RM",
                              "Maximum neural intent on the concentric. Brace the entire trunk before unracking."),
                        accessory(bench, "Volume bench - reinforce groove; focus on bar path consistency."),
                    ]
                },
                "tuesday": {
                    "session_name": "Bench - Heavy Day (DUP)",
                    "session_type": "strength_upper_heavy",
                    "exercises": [
                        heavy(bench, [2, 3], "87-93% 1RM",
                              "Leg drive into the floor; maintain upper-back tightness throughout the press."),
                        accessory(accessories[3], "Pull after press - agonist/antagonist pairing reduces fatigue and improves joint balance."),
                    ]
                },
                "wednesday": dict(ACTIVE_RECOVERY_SESSION),
                "thursday": {
                    "session_name": "Deadlift - Heavy Day (DUP)",
                    "session_type": "strength_hinge_heavy",
                    "exercises": [
                        heavy(dead, [1, 2], "90-95% 1RM",
                              "Lat engagement before the pull - 'protect your armpits'. Squeeze glutes at lockout."),
                        accessory(ohp, "Overhead strength supports bench lockout mechanics and shoulder health."),
                    ]
                },
                "friday": {
                    "session_name": "Squat + Bench - Volume Day (DUP)",
                    "session_type": "strength_volume",
                    "exercises": [
                        volume(squat, [5, 6], "75-80% 1RM",
                               "Accumulate volume at moderate intensity - focus on bar speed and technical consistency."),
                        volume(bench, [5, 6], "75-80% 1RM",
                               "Touch-and-go reps acceptable here; maintain arch and leg drive."),
                    ]
                },
                "saturday": dict(ACTIVE_RECOVERY_SESSION),
                "sunday":   dict(ACTIVE_RECOVERY_SESSION),
            }
        }

    # -----------------------------------------------------------------------
    # ENDURANCE - Polarized 80/20 (5 days)
    # -----------------------------------------------------------------------
    def _build_endurance_week(
        self, prescription: Dict, db: Dict, experience: str
    ) -> Dict:
        p_z2     = prescription["endurance"]["zone_2_aerobic_base"]["parameters"]
        p_thresh = prescription["endurance"]["lactate_threshold_tempo"]["parameters"]
        p_vo2    = prescription["endurance"]["vo2max_intervals"]["parameters"]

        duration = ZONE2_DURATION_BY_EXPERIENCE.get(experience, [30, 45])

        # Rotate 3 different Zone 2 modalities across Mon/Wed/Fri
        z2_pool    = db["cardio_zone2"]
        thresh_pool = db["cardio_threshold"]
        vo2_pool    = db["cardio_vo2max"]

        def zone2_session(modality: str) -> Dict:
            return {
                "name":            f"{modality} (Zone 2)",
                "type":            "cardio_aerobic",
                "duration_minutes": duration,
                "intensity":       f"{p_z2['intensity_hrmax_percent']} HRmax",
                "intensity_zone":  "Zone 2",
                "rpe":             "6-7",
                "cadence_note":    f"Running: 170-180 spm | Cycling: 85-95 rpm | Rowing: 18-22 spm",
                "pro_notes":       "Conversational pace - you should be able to speak in full sentences. Stay below lactate threshold at all times.",
            }

        def threshold_circuit() -> Dict:
            stations = [
                {"exercise": thresh_pool[0], "duration_seconds": 45, "reps": "15-20", "rest_seconds": 30},
                {"exercise": thresh_pool[1], "duration_seconds": 45, "reps": "15-20", "rest_seconds": 30},
                {"exercise": thresh_pool[2], "duration_seconds": 45, "reps": "15-20", "rest_seconds": 30},
            ]
            return {
                "name":            "Lactate Threshold Circuit",
                "type":            "cardio_threshold",
                "circuit_rounds":  [4, 6],
                "stations":        stations,
                "load_constraint": "<60% 1RM - keep load low to maintain cardiovascular density",
                "intensity":       f"{p_thresh['intensity_hrmax_percent']} HRmax",
                "intensity_zone":  "Zone 3-4",
                "rpe":             "8-9",
                "rest_between_rounds_seconds": [60, 90],
                "pro_notes":       "Comfortably hard pace. Consistent power output across all rounds. Allow 48-72h before next VO2max session.",
            }

        def vo2max_intervals() -> Dict:
            return {
                "name":                  f"{vo2_pool[0]} - VO2max Intervals",
                "type":                  "cardio_vo2max",
                "intervals":             4,
                "interval_duration_min": 4,
                "intensity":             f"{p_vo2['intensity_hrmax_percent']} HRmax",
                "intensity_zone":        "Zone 5",
                "rpe":                   "9-10",
                "rest_between_intervals_min": 3,
                "pro_notes":             "4×4 protocol (Seiler 2010). If last interval drops >5% from first, reduce to 3 intervals. Allow 48-72h recovery before next hard session.",
            }

        return {
            "split_type": "Polarized 80/20 (Zone 2 base + Threshold + VO2max)",
            "training_days_per_week": 5,
            "weekly_plan": {
                "monday":    {"session_name": f"Zone 2 Aerobic - {z2_pool[0]}",     "session_type": "endurance_zone2",      "exercises": [zone2_session(z2_pool[0])]},
                "tuesday":   {"session_name": "Lactate Threshold Circuit",           "session_type": "endurance_threshold",  "exercises": [threshold_circuit()]},
                "wednesday": {"session_name": f"Zone 2 Aerobic - {z2_pool[1]}",     "session_type": "endurance_zone2",      "exercises": [zone2_session(z2_pool[1])]},
                "thursday":  {"session_name": "VO2max Intervals",                    "session_type": "endurance_vo2max",     "exercises": [vo2max_intervals()]},
                "friday":    {"session_name": f"Zone 2 Aerobic - {z2_pool[2]}",     "session_type": "endurance_zone2",      "exercises": [zone2_session(z2_pool[2])]},
                "saturday":  dict(ACTIVE_RECOVERY_SESSION),
                "sunday":    dict(ACTIVE_RECOVERY_SESSION),
            }
        }

    # -----------------------------------------------------------------------
    # FAT LOSS - HIIT × 3 + Steady-state × 2 (5 days)
    # -----------------------------------------------------------------------
    def _build_fatloss_week(self, prescription: Dict, db: Dict) -> Dict:
        p_hiit = prescription["fatloss"]["hiit_circuits"]["parameters"]

        hiit_pool   = db["hiit"]
        steady_pool = db["cardio_steady"]

        # Work/rest intervals - hard cap rest at 60s regardless of YAML
        work_interval  = self._parse_range(p_hiit["work_interval_seconds"])
        rest_interval  = [
            max(15, self._parse_range(p_hiit["rest_interval_seconds"])[0]),
            min(60, self._parse_range(p_hiit["rest_interval_seconds"])[1]),
        ]

        def hiit_circuit() -> Dict:
            stations = [
                {
                    "exercise":           name,
                    "type":               "hiit_compound",
                    "work_seconds":       work_interval,
                    "rest_seconds":       rest_interval,
                    "reps":               [12, 15],
                    "rpe":                "9-10",
                    "pro_notes":          random.choice([
                        "Maximum effort on the work interval - full power output.",
                        "Short rest to amplify EPOC (afterburn effect).",
                        "Prioritize movement quality even under high metabolic fatigue.",
                        "Drive through the entire range of motion on every rep.",
                    ])
                }
                for name in hiit_pool[:4]
            ]
            return {
                "name":            "HIIT Circuit",
                "type":            "hiit_circuit",
                "circuit_rounds":  [3, 5],
                "stations":        stations,
                "total_duration_minutes": [15, 30],
                "intensity":       f"{p_hiit['intensity_percent_max']}% max effort",
                "rpe":             p_hiit["intensity_rpe"],
                "pro_notes":       "Complete all stations = 1 round. Rest 60-90s between rounds. Scale by reducing rounds, not extending work intervals.",
            }

        def steady_session(modality: str) -> Dict:
            return {
                "name":            f"{modality} (Steady-State)",
                "type":            "cardio_steady_state",
                "duration_minutes": [30, 45],
                "intensity":       "60-75% HRmax",
                "intensity_zone":  "Zone 2-3",
                "rpe":             "5-6",
                "pro_notes":       "Active recovery day - promotes fat oxidation and aids HIIT recovery without adding significant fatigue.",
            }

        return {
            "split_type": "HIIT Circuit × 3 + Steady-State Cardio × 2",
            "training_days_per_week": 5,
            "dietary_disclaimer": (
                "IMPORTANT: Exercise alone without concurrent caloric restriction produces minimal to zero "
                "fat mass reduction. For effective fat loss, maintain a sustained caloric deficit of "
                "300–500 kcal/day combined with adequate protein intake (1.6–2.2 g/kg bodyweight) to "
                "preserve lean muscle mass during the deficit."
            ),
            "weekly_plan": {
                "monday":    {"session_name": "HIIT Circuit A",          "session_type": "fatloss_hiit",   "exercises": [hiit_circuit()]},
                "tuesday":   {"session_name": f"Steady-State - {steady_pool[0]}", "session_type": "fatloss_steady", "exercises": [steady_session(steady_pool[0])]},
                "wednesday": {"session_name": "HIIT Circuit B",          "session_type": "fatloss_hiit",   "exercises": [hiit_circuit()]},
                "thursday":  {"session_name": f"Steady-State - {steady_pool[1]}", "session_type": "fatloss_steady", "exercises": [steady_session(steady_pool[1])]},
                "friday":    {"session_name": "HIIT Circuit C",          "session_type": "fatloss_hiit",   "exercises": [hiit_circuit()]},
                "saturday":  dict(ACTIVE_RECOVERY_SESSION),
                "sunday":    dict(ACTIVE_RECOVERY_SESSION),
            }
        }

    # -----------------------------------------------------------------------
    # Exercise factory helpers
    # -----------------------------------------------------------------------
    def _make_compound(
        self, name: str, reps: List[int], sets: List[int],
        params: Dict, note: str
    ) -> Dict:
        return {
            "name":         name,
            "type":         "compound",
            "sets":         sets,
            "reps":         reps,
            "tempo":        params["tempo"],
            "rest_seconds": [120, 180],   # 2-3 min - hardcoded, never null
            "rpe":          params["intensity_rpe"],
            "pro_notes":    note,
        }

    def _make_isolation(
        self, name: str, reps: List[int], sets: List[int],
        params: Dict, note: str
    ) -> Dict:
        return {
            "name":         name,
            "type":         "isolation",
            "sets":         sets,
            "reps":         reps,
            "tempo":        params["tempo"],
            "rest_seconds": [90, 120],    # 1.5-2 min - hardcoded, never null
            "rpe":          params["intensity_rpe"],
            "pro_notes":    note,
        }

    # -----------------------------------------------------------------------
    # Utility
    # -----------------------------------------------------------------------
    def _parse_range(self, range_str) -> List[int]:
        """Parse ANY range format string → [low, high]"""
        if not isinstance(range_str, str):
            return [int(range_str), int(range_str)]

        s = (range_str
             .replace("%", "").replace("1RM", "").replace("HRmax", "")
             .split(" per ")[0]
             .replace(" reps", "").replace(" minutes", "")
             .strip())

        if "-" in s:
            parts = s.split("-")
            low  = int(re.search(r"\d+", parts[0]).group())
            high = int(re.search(r"\d+", parts[1]).group())
            return [low, high]
        else:
            num = int(re.search(r"\d+", s).group())
            return [num, num]
