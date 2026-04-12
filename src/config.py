from dotenv import load_dotenv
load_dotenv() # 自动寻找根目录下的 .env 并加载为环境变量
import os
from pathlib import Path

# ==========================================
# 基础路径配置
# ==========================================
# 自动定位项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 模板与输出路径
TEMPLATE_DIR = PROJECT_ROOT / "templates"
STAGE1_OUT = PROJECT_ROOT / "output" / "stage1_prevention"
STAGE2_OUT = PROJECT_ROOT / "output" / "stage2_care"
STAGE3_OUT = PROJECT_ROOT / "output" / "stage3_rehab"

# ==========================================
# 算力路由配置 (从环境变量读取)
# ==========================================

# 1. 自研 TCM-DMX (远程 GPU 节点)
# 默认指向本地回环或占位符，通过环境变量注入真实 IP
SHIZHEN_API_URL = os.getenv("SHIZHEN_API_URL", "http://your-remote-ip:8000/v1/chat/completions")
SHIZHEN_API_KEY = os.getenv("SHIZHEN_API_KEY", "your_shizhen_key_here")

# 2. 字节跳动 - 豆包 (Ark API)
DOUBAO_API_URL = os.getenv("DOUBAO_API_URL", "https://ark.cn-beijing.volces.com/api/v3/chat/completions")
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "your_doubao_key_here")
DOUBAO_MODEL_ID = os.getenv("DOUBAO_MODEL_ID", "doubao-seed-1-8-251228")

# 3. 本地推理引擎 - Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
LOCAL_QWEN_NAME = os.getenv("LOCAL_QWEN_NAME", "qwen2:0.5b")
LOCAL_LLAMA_NAME = os.getenv("LOCAL_LLAMA_NAME", "llama3.2:1b")

# ==========================================
# 数据集路径 (建议使用相对路径)
# ==========================================
SYNTHEA_CSV_DIR = os.getenv("SYNTHEA_CSV_DIR", str(PROJECT_ROOT / "data" / "synthea_sample"))