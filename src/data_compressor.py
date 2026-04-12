import polars as pl
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - COMPRESSOR - %(message)s')


def compress_metabonet():
    """将 1.5GB 的原始 Parquet 极限压缩为 1MB 的精华基石数据"""
    base_dir = Path(__file__).parent.parent
    raw_parquet_path = base_dir / "data" / "metabonet_refs" / "metabonet_public_train.parquet"
    output_parquet_path = base_dir / "data" / "metabonet_essential.parquet"

    if not raw_parquet_path.exists():
        logging.error(f"找不到原始文件: {raw_parquet_path}")
        return

    logging.info("🚀 正在从 1.5GB 原始文件中精准剥离核心生信/穿戴特征...")

    # 1. 仅提取系统需要的 9 个核心列
    core_columns = [
        'age', 'gender', 'weight', 'height', 'CGM',
        'insulin', 'carbs', 'steps', 'calories_burned'
    ]

    try:
        # 2. 惰性加载并去空值
        lazy_df = pl.scan_parquet(raw_parquet_path).select(core_columns).drop_nulls()

        # 3. 收集到内存，并计算 BMI
        df = lazy_df.collect()
        df = df.with_columns(
            (pl.col("weight") / ((pl.col("height") / 100) ** 2)).alias("bmi_calculated")
        )

        # 4. 随机抽取 10000 名代表性患者 (足够任何孪生匹配使用)
        if df.height > 10000:
            df = df.sample(n=10000, seed=42)

        # 5. 保存为极其轻量的 GitHub 专用基石文件
        df.write_parquet(output_parquet_path)

        logging.info(f"✅ 数据极限提纯完成！")
        logging.info(f"原文件大小: ~1.5 GB")
        logging.info(f"新文件大小: ~{output_parquet_path.stat().st_size / (1024 * 1024):.2f} MB")
        logging.info(f"精华基石数据已保存至: {output_parquet_path}")

    except Exception as e:
        logging.error(f"压缩失败: {e}")


if __name__ == "__main__":
    compress_metabonet()