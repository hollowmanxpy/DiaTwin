# 🧬 DiaTwin: Multi-LLM Diabetes Digital Twin Platform

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-green.svg)
![Standard](https://img.shields.io/badge/Standard-HL7_FHIR_R4-blueviolet.svg)
![Status](https://img.shields.io/badge/status-Active_Development-success.svg)

DiaTwin (糖尿病数字孪生平台) 是一个基于真实世界数据 (RWD) 与多模态大模型 (Multi-LLM) 的全周期临床推演引擎。平台以团队自研的 **TCM-DMX (时珍中医数字化演进版)** 为核心，并行调度 Qwen2、Llama-3.2、Doubao 等先进大模型，通过动力学模拟，推演患者在不同干预路径下的代谢走向与临床获益。

## 🌟 核心特性 (Key Features)

- **HL7 FHIR 孪生数据扩增 (Digital Twin Generator)**：内置数据合成引擎，基于患者基线切片与代谢动力学漂移算法，自动化扩增连续30天的动态血糖与生活方式序列，并严格序列化为国际通用的 `HL7 FHIR R4` 标准 JSON 数据包。
- **多模型平行推演 (Parallel Simulation)**：构建并行调度架构，同步输出五大模型的干预方案，直观对比不同临床决策（中医/西医/营养学）下的血糖衰减与获益曲线差异。
- **全周期覆盖 (Full-Cycle Care)**：
  - `Stage 1`: 预防与生活方式干预 (Prevention & Lifestyle)
  - `Stage 2`: 临床用药与并发症管理 (Medication & Complications)
  - `Stage 3`: 终末期重症靶器官保护与临床获益 (End-Stage Rehab & Clinical Benefit)
- **AI 智能评估体系 (LLM Evaluator)**：引入本地部署的 Qwen2 模型作为独立质控评估引擎，基于 JSON 结构化格式，严格量化评估各干预方案的「临床有效性」与「安全性」。
- **数据驱动的可视化大屏**：基于 HTML5 与 Chart.js 构建高保真、响应式的临床数据交互与推演可视化报告。

## 🏗️ 架构概览 (Architecture)

```text
DiaTwin_MultiLLM_Platform/
├── data/                       # 真实世界 RWD 与 Synthea 合成数据集样例
├── src/
│   ├── app_diatwin_generator.py # Streamlit 交互式数据生成舱 (Web App)
│   ├── diatwin_fhir_generator.py# FHIR 数据扩增与序列化底层引擎
│   ├── llm_router.py            # 多模型并行路由调度器 (含场景感知 Prompt)
│   ├── llm_evaluator.py         # 量化评估与裁判引擎 (De-biased)
│   └── stage1~3_*.py            # 三阶段平行推演核心引擎
├── templates/                   # 临床可视化大屏 Jinja2 模板
└── output/                      # 动态生成的 HTML 推演报告输出区
🚀 快速启动 (Quick Start)
1. 环境准备
Bash
conda create -n DiaTwin_Multi python=3.9
conda activate DiaTwin_Multi
pip install -r requirements.txt
2. 配置模型节点
在 src/config.py 中配置您的 API Key 和本地 Ollama 节点。
(注：本项目默认支持通过 API 调用远程 GPU 节点部署的 TCM-DMX 大模型进行跨网推理。)

3. 启动交互式数据生成舱 (Web App)
启动基于 Streamlit 的 Web 界面，一键生成符合 FHIR 标准的数字孪生体：

Bash
streamlit run src/app_diatwin_generator.py
4. 执行全周期多模态推演
运行以下脚本，引擎将自动生成多模型平行推演大屏（输出至 output/ 对应子目录）：

Bash
# 执行 Stage 1 预防推演
python src/stage1_prevention.py

# 执行 Stage 2 临床用药推演
python src/stage2_care.py

# 执行 Stage 3 终末期临床获益推演
python src/stage3_rehab.py
📜 声明 (Disclaimer)
本项目生成的临床路径、药物干预建议及生存期推演结果，仅供学术研究、系统互操作性测试与数字孪生推演演示使用，不构成任何实际的医疗诊断或治疗方案。

Built with ❤️ by the TCM-DMX Team.