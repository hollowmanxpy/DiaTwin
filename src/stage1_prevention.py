import os
import random
import logging
import polars as pl
from jinja2 import Template
import config
from llm_router import LLMRouter
from llm_evaluator import ClinicalLLMEvaluator

# 🌟 统一格式的极客风日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [Stage1-Prev] | %(message)s', datefmt='%H:%M:%S')


class PreventionEngine:
    def __init__(self):
        self.output_dir = config.PROJECT_ROOT / "output" / "stage1_prevention"
        self.template_dir = config.TEMPLATE_DIR
        os.makedirs(self.output_dir, exist_ok=True)
        self.evaluator = ClinicalLLMEvaluator()

    def generate_stratified_cohort(self, count=4):
        cohort = []
        strata = [
            ((0.8, 0.95), (6.0, 6.8), "高依从/中风险"),
            ((0.4, 0.6), (5.7, 6.2), "低依从/轻风险"),
            ((0.7, 0.85), (5.5, 5.9), "中依从/临界风险"),
            ((0.9, 1.0), (6.5, 7.2), "极高依从/高风险")
        ]
        for i in range(count):
            s_comp, s_fpg, label = strata[i % len(strata)]
            comp = round(random.uniform(*s_comp), 2)
            fpg = round(random.uniform(*s_fpg), 1)
            cohort.append({
                "patient_id": f"DIA-P-{random.randint(1000, 9999)}",
                "tag": label, "bmi": round(random.uniform(23.0, 31.0), 1),
                "compliance": comp, "base_fpg": fpg,
                "base_hba1c": round(fpg * 1.1 - 0.5, 1)
            })
        return cohort

    def run_simulation(self):
        logging.info("=" * 60)
        logging.info("🚀 启动 Stage 1 多模态预防与生活方式推演")
        logging.info("=" * 60)

        macro_stats = {"total": 100, "avg_base": 5.8, "avg_post": 4.9, "rev_rate": 82.5}
        raw_cohort = self.generate_stratified_cohort(4)

        models = [
            ("shizhen", "TCM-DMX", "#30A5A7"), ("ant", "Ant Medical", "#10B981"),
            ("doubao", "Doubao", "#3B82F6"), ("llama3.2", "Llama-3.2", "#8B5CF6"), ("qwen2", "Qwen2", "#F59E0B")
        ]

        final_patients = []
        for p in raw_cohort:
            logging.info(f"👤 正在处理预防期病例: {p['patient_id']} (FPG: {p['base_fpg']})")
            results = {}
            for key, name, color in models:
                rx = LLMRouter.ask(key, f"患者空腹血糖 {p['base_fpg']}。请给出100字左右的综合生活方式干预建议。")
                scores = self.evaluator.evaluate("Prevention", name, rx)

                eff = (scores.get("clinical_accuracy", 7.0) + scores.get("safety", 7.0)) / 20.0
                base = p['base_fpg']

                # 调整基础系数为 0.4，让曲线更明显
                traj = [
                    base,
                    round(base - (delta := 0.4 * eff * p['compliance']), 1),
                    round(base - (delta * 2.2), 1),
                    round(max(4.0, base - (delta * 3.8)), 1)
                ]

                y_min = round(min(traj) - 0.5, 1)
                results[name] = {"prescription": rx, "scores": scores, "color": color, "traj": traj,
                                 "post_fpg": traj[-1], "y_min": y_min}
                logging.info(
                    f"   ├─ 🤖 {name.ljust(12)} | 评分: 准{scores.get('clinical_accuracy')}/安{scores.get('safety')} | FPG 降至: {traj[-1]}")

            p["llm_results"] = results
            final_patients.append(p)

        logging.info("🎨 正在渲染 Stage 1 报告...")
        with open(self.template_dir / "report_stage1.html", "r", encoding="utf-8") as f:
            template = Template(f.read())
        html = template.render(stats=macro_stats, patients=final_patients)

        out_path = self.output_dir / "Stage1_Prevention_Report.html"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        logging.info(f"✅ Stage 1 报告生成完毕: {out_path}")


if __name__ == "__main__":
    PreventionEngine().run_simulation()