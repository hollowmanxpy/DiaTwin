import json
import uuid
import random
import logging
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s | [DiaTwin-FHIR] | %(message)s', datefmt='%H:%M:%S')


class DiaTwinFHIRGenerator:
    def __init__(self, patient_baseline: Dict[str, Any], simulate_days: int = 30):
        self.baseline = patient_baseline
        self.simulate_days = simulate_days
        self.patient_uuid = str(uuid.uuid4())
        self.start_date = datetime.now() - timedelta(days=self.simulate_days)

        # 严格定义类型，消除 IDE 的 append 警告
        self.entries: List[Dict[str, Any]] = []
        self.bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": datetime.now().isoformat() + "Z",
            "entry": self.entries
        }

    def _add_resource(self, resource: Dict[str, Any]):
        self.entries.append({
            "fullUrl": f"urn:uuid:{resource['id']}",
            "resource": resource
        })

    def generate_patient_resource(self):
        patient = {
            "resourceType": "Patient",
            "id": self.patient_uuid,
            "identifier": [{"system": "urn:diatwin:patient-id", "value": self.baseline.get("patient_id", "UNKNOWN")}],
            "name": [{"use": "usual", "text": self.baseline.get("name", "匿名患者")}],
            "gender": self.baseline.get("gender", "unknown"),
            "birthDate": (datetime.now() - timedelta(days=self.baseline.get("age", 50) * 365)).strftime("%Y-%m-%d")
        }
        self._add_resource(patient)

    def generate_condition_resource(self):
        condition = {
            "resourceType": "Condition",
            "id": str(uuid.uuid4()),
            "clinicalStatus": {"coding": [{"system": "urn:terminology:condition-clinical", "code": "active"}]},
            "code": {
                "coding": [{"system": "urn:snomed:sct", "code": "44054006", "display": "Type 2 diabetes mellitus"}]},
            "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
            "onsetDateTime": self.start_date.isoformat() + "Z"
        }
        self._add_resource(condition)

        for comp in self.baseline.get("complications", []):
            comp_cond = {
                "resourceType": "Condition",
                "id": str(uuid.uuid4()),
                "clinicalStatus": {"coding": [{"system": "urn:terminology:condition-clinical", "code": "active"}]},
                "code": {"text": comp},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"}
            }
            self._add_resource(comp_cond)

    def generate_static_observations(self):
        observations = [
            ("39156-5", "Body mass index (BMI)", self.baseline.get("bmi", 24.0), "kg/m2"),
            ("4548-4", "Hemoglobin A1c", self.baseline.get("base_hba1c", 6.5), "%")
        ]

        for loinc, display, value, unit in observations:
            obs = {
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "code": {"coding": [{"system": "urn:loinc:org", "code": loinc, "display": display}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": self.start_date.isoformat() + "Z",
                "valueQuantity": {"value": value, "unit": unit}
            }
            self._add_resource(obs)

    def augment_time_series_data(self):
        current_fpg = self.baseline.get("base_fpg", 6.0)
        compliance = self.baseline.get("compliance", 0.5)

        for day in range(self.simulate_days):
            current_date = self.start_date + timedelta(days=day)

            # FPG 扩增
            drift = -0.05 if compliance > 0.7 else (0.02 if compliance < 0.4 else 0.0)
            current_fpg = round(max(4.0, current_fpg + drift + random.uniform(-0.3, 0.3)), 1)

            fpg_obs = {
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "code": {"coding": [{"system": "urn:loinc:org", "code": "1558-6", "display": "Fasting glucose"}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": current_date.isoformat() + "Z",
                "valueQuantity": {"value": current_fpg, "unit": "mmol/L"}
            }
            self._add_resource(fpg_obs)

            # 步数扩增
            daily_steps = max(1000, int(4000 + (compliance * 4000)) + random.randint(-1500, 2500))
            step_obs = {
                "resourceType": "Observation",
                "id": str(uuid.uuid4()),
                "status": "final",
                "code": {"coding": [{"system": "urn:loinc:org", "code": "41950-7", "display": "Steps in 24 hour"}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": current_date.isoformat() + "Z",
                "valueQuantity": {"value": daily_steps, "unit": "steps/day"}
            }
            self._add_resource(step_obs)

    def run_generation(self) -> Dict[str, Any]:
        self.generate_patient_resource()
        self.generate_condition_resource()
        self.generate_static_observations()
        self.augment_time_series_data()
        return self.bundle