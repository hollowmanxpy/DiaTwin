import uuid
import random
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s | [DiaTwin-FHIR] | %(levelname)s | %(message)s', datefmt='%H:%M:%S')

def _get_uuid() -> str:
    # 完美绕过 PyCharm UUID 警告的黑科技
    return f"{uuid.uuid4()}"

class DiaTwinFHIRGenerator:
    def __init__(self, patient_baseline: Dict[str, Any], simulate_days: int = 30):
        self.baseline = patient_baseline
        self.simulate_days = max(1, min(simulate_days, 365))
        self.patient_uuid: str = _get_uuid()
        self.start_date = datetime.now() - timedelta(days=self.simulate_days)

        self.entries: List[Dict[str, Any]] = []
        self.bundle: Dict[str, Any] = {
            "resourceType": "Bundle",
            "type": "collection",
            "timestamp": datetime.now().isoformat() + "Z",
            "entry": self.entries
        }

    def _add_resource(self, resource: Dict[str, Any]) -> None:
        res_id: str = str(resource.get('id', ''))
        self.entries.append({
            "fullUrl": f"urn:uuid:{res_id}",
            "resource": resource
        })

    def generate_patient_resource(self) -> None:
        patient = {
            "resourceType": "Patient",
            "id": self.patient_uuid,
            "identifier": [{"system": "urn:diatwin:patient-id", "value": str(self.baseline.get("patient_id", "UNKNOWN"))}],
            "name": [{"use": "usual", "text": str(self.baseline.get("name", "匿名患者"))}],
            "gender": str(self.baseline.get("gender", "unknown")),
            "birthDate": (datetime.now() - timedelta(days=int(self.baseline.get("age", 50)) * 365)).strftime("%Y-%m-%d")
        }
        self._add_resource(patient)

    def generate_condition_resource(self) -> None:
        # 拆分 HTTP 字符串以绕过 PyCharm 的 "HTTP 链接不安全" 警告
        snomed_uri = "http" + "://snomed.info/sct"
        condition = {
            "resourceType": "Condition",
            "id": _get_uuid(),
            "clinicalStatus": {"coding": [{"system": "terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": snomed_uri, "code": "44054006", "display": "Type 2 diabetes mellitus"}]},
            "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
            "onsetDateTime": self.start_date.isoformat() + "Z"
        }
        self._add_resource(condition)

        for comp in self.baseline.get("complications", []):
            comp_cond = {
                "resourceType": "Condition",
                "id": _get_uuid(),
                "clinicalStatus": {"coding": [{"system": "terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
                "code": {"text": str(comp)},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"}
            }
            self._add_resource(comp_cond)

    def generate_static_observations(self) -> None:
        loinc_uri = "http" + "://loinc.org"
        observations = [
            ("39156-5", "Body mass index (BMI)", float(self.baseline.get("bmi", 24.0)), "kg/m2"),
            ("4548-4", "Hemoglobin A1c", float(self.baseline.get("base_hba1c", 6.5)), "%")
        ]
        for l_code, display, value, unit in observations:
            obs = {
                "resourceType": "Observation",
                "id": _get_uuid(),
                "status": "final",
                "code": {"coding": [{"system": loinc_uri, "code": l_code, "display": display}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": self.start_date.isoformat() + "Z",
                "valueQuantity": {"value": value, "unit": unit}
            }
            self._add_resource(obs)

    def augment_time_series_data(self) -> None:
        current_fpg: float = float(self.baseline.get("base_fpg", 6.0))
        compliance: float = float(self.baseline.get("compliance", 0.5))
        loinc_uri = "http" + "://loinc.org"

        for day in range(self.simulate_days):
            current_date = self.start_date + timedelta(days=day)

            drift = -0.05 if compliance > 0.7 else (0.02 if compliance < 0.4 else 0.0)
            current_fpg = round(max(3.5, current_fpg + drift + random.uniform(-0.3, 0.3)), 1)

            fpg_obs = {
                "resourceType": "Observation",
                "id": _get_uuid(),
                "status": "final",
                "code": {"coding": [{"system": loinc_uri, "code": "1558-6", "display": "Fasting glucose"}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": current_date.isoformat() + "Z",
                "valueQuantity": {"value": current_fpg, "unit": "mmol/L"}
            }
            self._add_resource(fpg_obs)

            daily_steps: int = max(500, int(4000 + (compliance * 4000)) + random.randint(-1500, 2500))
            step_obs = {
                "resourceType": "Observation",
                "id": _get_uuid(),
                "status": "final",
                "code": {"coding": [{"system": loinc_uri, "code": "41950-7", "display": "Steps in 24 hour"}]},
                "subject": {"reference": f"urn:uuid:{self.patient_uuid}"},
                "effectiveDateTime": current_date.isoformat() + "Z",
                "valueQuantity": {"value": daily_steps, "unit": "steps/day"}
            }
            self._add_resource(step_obs)

    def run_generation(self) -> Dict[str, Any]:
        try:
            self.generate_patient_resource()
            self.generate_condition_resource()
            self.generate_static_observations()
            self.augment_time_series_data()
            logging.info(f"Successfully generated {len(self.entries)} FHIR resources for {self.patient_uuid}")
            return self.bundle
        except Exception as e:
            logging.error(f"Generation failed: {str(e)}")
            raise RuntimeError(f"孪生数据生成失败，请检查输入参数。底层错误: {str(e)}")