import polars as pl
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SYNTHEA_COMPRESSOR - %(message)s')


def compress_synthea():
    base_dir = Path(__file__).parent.parent
    # 指向您电脑真实的巨大 Synthea 目录
    raw_dir = Path(r"D:\synthea\output\csv")

    # 我们将在项目中创建一个微型的 demo 数据夹用于上传 GitHub
    out_dir = base_dir / "data" / "synthea_sample"
    out_dir.mkdir(parents=True, exist_ok=True)

    logging.info("🚀 正在从 D 盘的海量 Synthea 数据中抽取 200 名糖尿病患者作为 Demo 基盘...")

    try:
        # 1. 读取疾病表，找出患有糖尿病的患者
        df_cond = pl.read_csv(raw_dir / "conditions.csv", ignore_errors=True)
        diabetes_pids = df_cond.filter(
            pl.col("DESCRIPTION").str.contains("(?i)diabetes")
        )["PATIENT"].unique().to_list()

        # 只抽取前 200 人
        sample_pids = diabetes_pids[:200]

        logging.info("✂️ 正在切片对应的患者基本信息表与观察指标表...")
        # 2. 切片其他表格 (注意：patients表的患者ID列叫 'Id'，其他表叫 'PATIENT')
        df_patients = pl.read_csv(raw_dir / "patients.csv", ignore_errors=True).filter(pl.col("Id").is_in(sample_pids))
        df_obs = pl.read_csv(raw_dir / "observations.csv", ignore_errors=True).filter(
            pl.col("PATIENT").is_in(sample_pids))
        df_cond_filtered = df_cond.filter(pl.col("PATIENT").is_in(sample_pids))

        # 3. 写入项目内的 demo 文件夹
        df_patients.write_csv(out_dir / "patients.csv")
        df_obs.write_csv(out_dir / "observations.csv")
        df_cond_filtered.write_csv(out_dir / "conditions.csv")

        logging.info("✅ Synthea 极简版 Demo 数据生成成功！")
        logging.info(f"已保存至: {out_dir}")
        logging.info("此文件夹极其轻量，可随代码一并上传至 GitHub。")

    except Exception as e:
        logging.error(f"抽取失败: {e}。请检查您的 D 盘路径。")


if __name__ == "__main__":
    compress_synthea()