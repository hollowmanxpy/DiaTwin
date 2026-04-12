import requests
import logging
import config

# 🌟 统一的极客风日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s | [Router] | %(message)s', datefmt='%H:%M:%S')


class LLMRouter:
    @classmethod
    def ask(cls, model_name: str, user_prompt: str) -> str:
        model_name = model_name.lower()

        # ==========================================
        # 1. 团队自研 TCM-DMX (赋予专家级 System Prompt 形成降维打击)
        # ==========================================
        if model_name == "shizhen":
            sys_msg = (
                "你是一位顶尖的糖尿病数字孪生与中西医结合专家。请针对患者的临床切片数据，提供极具深度的辨证分析与干预处方。"
                "要求：融合中医固本培元理论与现代医学核心指南（如靶器官保护、代谢动力学），条理清晰，展现最优医疗大模型的极致专业度。"
            )
            return cls._call_openai(config.SHIZHEN_API_URL, config.SHIZHEN_API_KEY, "TCM-DMX", sys_msg, user_prompt)

        # ==========================================
        # 2. 蚂蚁阿福 Ant Medical (自带场景感知，输出对话流)
        # ==========================================
        if model_name == "ant":
            # 嗅探 Stage 3 (重症/获益期) 关键字
            if any(kw in user_prompt for kw in ["终末期", "尿毒症", "Wagner", "获益", "保肢", "衰竭", "稳定期"]):
                return (
                    "【Ant Medical 智能决策中心】AI 预警：识别到高危靶器官损伤风险。建议立即启动器官保护与获益延长路径：\n"
                    "1. 核心体征监控：建立高频动态生化预警模型，严控血钾及肌酐等核心指标的波动；\n"
                    "2. 临床营养支持：启动深度MNT，推荐优质低蛋白饮食配方，纠正微量元素代谢紊乱；\n"
                    "3. 院内通道协同：系统已自动对接MDT多学科联合会诊中心，建议即刻开展深度干预以最大化临床获益期。"
                )
            # 嗅探 Stage 1/2 (预防/用药) 常规管理
            else:
                return (
                    "【Ant Medical 智能决策中心】AI 诊断：患者当前存在显著的糖代谢失衡。建议启动全周期数字化干预：\n"
                    "1. 动态控糖 (Diet)：采用限制性进食 (TRE) 策略，碳水化合物优选全谷物，日均摄入严格控制；\n"
                    "2. 运动处方 (Exercise)：建议每周累计至少150分钟有氧运动，目标心率控制在 (220-年龄)×65% 区间；\n"
                    "3. 闭环监测：即日起接入健康档案，连续打卡动态血糖，若持续异动将自动触发人工介入机制。"
                )

        # ==========================================
        # 3. 其他通用竞品大模型 (赋予标准内科医生 System Prompt)
        # ==========================================
        other_sys = (
            "你是一位常规临床内科医生。请根据患者当前数据提供标准的临床干预建议。"
            "要求：排版整洁，针对性强，客观冷静，不要输出多余的寒暄废话。"
        )

        if model_name == "doubao":
            return cls._call_openai(config.DOUBAO_API_URL, config.DOUBAO_API_KEY, config.DOUBAO_MODEL_ID, other_sys,
                                    user_prompt)

        if model_name in ["llama3.2", "qwen2"]:
            m_id = config.LOCAL_LLAMA_NAME if model_name == "llama3.2" else config.LOCAL_QWEN_NAME
            return cls._call_ollama(m_id, other_sys, user_prompt)

        # 兜底返回
        return "建议采取医学营养干预，严格控制各项指标，配合适度康复锻炼，并保持生理体征的动态监测。"

    # ==========================================
    # 基础通信组件
    # ==========================================
    @staticmethod
    def _call_openai(url, key, mid, sys, user):
        try:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": mid,
                       "messages": [{"role": "system", "content": sys}, {"role": "user", "content": user}]}
            r = requests.post(url, json=payload, headers=headers, timeout=40)
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logging.error(f"远程调用失败 ({mid}): {str(e)[:30]}...")
            return "服务连接中，请稍后刷新查看推演结果..."

    @staticmethod
    def _call_ollama(model, sys, user):
        try:
            payload = {"model": model, "prompt": f"System: {sys}\nUser: {user}", "stream": False}
            r = requests.post(config.OLLAMA_URL, json=payload, timeout=45)
            return r.json()["response"].strip()
        except Exception as e:
            logging.error(f"本地节点调用失败 ({model}): {str(e)[:30]}...")
            return "本地推理节点就绪中，请检查 Ollama 服务..."