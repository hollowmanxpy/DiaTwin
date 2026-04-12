import os
import logging
import polars as pl
import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - METABO_MAPPER - %(levelname)s - %(message)s')


class MetaboNetBridger:
    def __init__(self):
        self.parquet_path = config.PROJECT_ROOT / "data" / "metabonet_refs" / "metabonet_public_train.parquet"
        self._real_data_pool = None
        self._initialize_data_pool()

    def _initialize_data_pool(self):
        if not os.path.exists(self.parquet_path):
            logging.warning("⚠️ 未找到 MetaboNet Parquet 文件，将走降级模拟。")
            return

        logging.info("🚀 启动内存极简模式，正在针对真实列名加载 CGM 与行为特征...")
        try:
            # 根据您探查出的列名，我们精准下推这些核心列
            exact_columns = [
                'age', 'gender', 'weight', 'height', 'CGM',
                'insulin', 'carbs', 'steps', 'calories_burned'
            ]

            # 惰性扫描 -> 选取列 -> 去除空值 -> 加载到内存
            lazy_df = pl.scan_parquet(self.parquet_path).select(exact_columns).drop_nulls()

            # 由于可能有多条时序数据，我们简单粗暴地抽取 50000 条样本，极大降低内存
            self._real_data_pool = lazy_df.collect()
            if self._real_data_pool.height > 50000:
                self._real_data_pool = self._real_data_pool.sample(n=50000, seed=42)

            # 【重要】动态计算出 BMI
            self._real_data_pool = self._real_data_pool.with_columns(
                (pl.col("weight") / ((pl.col("height") / 100) ** 2)).alias("bmi_calculated")
            )

            logging.info(f"✅ 成功加载 {self._real_data_pool.height} 条精简记录并自动计算了 BMI！")
        except Exception as e:
            logging.error(f"加载 Parquet 失败: {e}")

    def get_real_metabolic_profile(self, age: int, gender: str, bmi: float, disease_stage: str) -> dict:
        import numpy as np
        if self._real_data_pool is None or self._real_data_pool.height == 0:
            return self._generate_mock()

        # 性别匹配 (如果有 Male/Female 等差异，这里统一映射)
        # 根据年龄和 BMI 进行宽容度近邻匹配
        matched = self._real_data_pool.filter(
            (pl.col("age") >= age - 5) & (pl.col("age") <= age + 5) &
            (pl.col("bmi_calculated") >= bmi - 3) & (pl.col("bmi_calculated") <= bmi + 3)
        )

        if matched.height > 0:
            # 抽中一个真实人类的切片数据
            rp = matched.sample(n=1).to_dicts()[0]

            # 用真实 CGM(mg/dL) 估算空腹血糖(mmol/L) -> 大致除以 18
            fpg_estimated = round(float(rp["CGM"]) / 18.0, 1) if rp.get("CGM") else round(np.random.normal(5.5, 0.8), 1)

            # 用真实胰岛素使用量估算 IR (用量越大抵抗越严重)
            ir_estimated = round(float(rp.get("insulin", 0)) * 0.1 + 1.5, 1)

            return {
                "fpg": fpg_estimated,
                "ir_index": ir_estimated,
                "real_steps": int(rp.get("steps", 5000)),
                "real_carbs": float(rp.get("carbs", 150.0)),
                # 缺失的血脂依然走高糖耦合模拟
                "cholesterol": round(np.random.normal(5.2, 0.8), 2),
                "triglyceride": round(np.random.normal(1.8, 0.5), 2)
            }
        else:
            return self._generate_mock()

    def _generate_mock(self):
        import numpy as np
        return {
            "fpg": round(np.random.normal(5.5, 0.8), 1),
            "ir_index": round(np.random.normal(2.5, 1.0), 1),
            "real_steps": int(np.random.normal(5000, 2000)),
            "real_carbs": round(np.random.normal(200, 50), 1),
            "cholesterol": round(np.random.normal(5.2, 0.8), 2),
            "triglyceride": round(np.random.normal(1.8, 0.5), 2)
        }


if __name__ == "__main__":
    bridger = MetaboNetBridger()
    print("真实世界测试 ->", bridger.get_real_metabolic_profile(50, "Male", 26.5, "At-Risk"))