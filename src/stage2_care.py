import os
import random
import logging
from jinja2 import Template
import config
from llm_router import LLMRouter
from llm_evaluator import ClinicalLLMEvaluator

# 🌟 统一的控制台日志风格
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [Stage2-Care] | %(message)s', datefmt='%H:%M:%S')


class CareEngine:
    def __init__(self):
        self.output_dir = config.PROJECT_ROOT / "output" / "stage2_care"
        self.template_dir = config.TEMPLATE_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.evaluator = ClinicalLLMEvaluator()

    def run_care_simulation(self):
        logging.info("=" * 60)
        logging.info("💊 启动 Stage 2 多模态临床药物与并发症推演")
        logging.info("=" * 60)

        stats = {"total": 120, "avg_base_hba1c": 8.7, "avg_post_hba1c": 6.8, "control_rate": 76.5}

        patients = [
            {"patient_id": "DIA-C-882", "age": 65, "bmi": 28.5, "base_hba1c": 8.7, "comp": "早期微量白蛋白尿",
             "c": 0.75},
            {"patient_id": "DIA-C-915", "age": 58, "bmi": 26.2, "base_hba1c": 9.2, "comp": "周围神经病变 (双足麻木)",
             "c": 0.82}
        ]

        models = [
            ("shizhen", "TCM-DMX", "#30A5A7"), ("ant", "Ant Medical", "#10B981"),
            ("doubao", "Doubao", "#3B82F6"), ("llama3.2", "Llama-3.2", "#8B5CF6"), ("qwen2", "Qwen2", "#F59E0B")
        ]

        for p in patients:
            logging.info(f"👤 正在处理确诊病例: {p['patient_id']} (HbA1c: {p['base_hba1c']}%)")
            results = {}
            for key, name, color in models:
                rx = LLMRouter.ask(key,
                                   f"患者HbA1c {p['base_hba1c']}%, 伴发{p['comp']}。请提供约100字的中西医联合用药及管理建议。")
                scores = self.evaluator.evaluate("Medication", name, rx)


                eff = (scores.get("clinical_accuracy", 7.0) + scores.get("safety", 7.0)) / 20.0
                # 调整基础系数为 4.0
                post_hba1c = round(max(5.0, p['base_hba1c'] - (4.0 * eff * p['c'])), 1)

                results[name] = {"prescription": rx, "scores": scores, "color": color, "post_hba1c": post_hba1c}
                logging.info(
                    f"   ├─ 🤖 {name.ljust(12)} | 评分: 准{scores.get('clinical_accuracy')}/安{scores.get('safety')} | HbA1c 降至: {post_hba1c}%")

            p["shizhen"] = results.pop("TCM-DMX")
            p["competitors"] = results

        logging.info("🎨 正在渲染 Stage 2 报告...")
        with open(self.template_dir / "report_stage2.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
        html = template.render(stats=stats, patients=patients)

        out_path = self.output_dir / "Stage2_Care_Report.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        logging.info(f"✅ Stage 2 报告生成完毕: {out_path}")


if __name__ == "__main__":
    CareEngine().run_care_simulation()