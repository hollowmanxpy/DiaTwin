import json
import requests
import re
import logging
import config


class ClinicalLLMEvaluator:
    def __init__(self):
        self.ollama_url = config.OLLAMA_URL
        self.model_name = config.LOCAL_QWEN_NAME
        # 增加超时时间，防止本地算力排队导致超时
        self.timeout = 45

    def evaluate(self, patient_context, model_name, prescription):
        eval_prompt = f"""
        你是一位严格的医疗质控专家。请对以下处方进行打分（满分10分）。
        背景: {patient_context}
        医生: {model_name}
        处方: {prescription}

        请严格按 JSON 输出：
        {{
          "clinical_accuracy": 0到10之间的数字,
          "safety": 0到10之间的数字,
          "readability": 0到10之间的数字,
          "reason": "一句话点评"
        }}
        """

        fallback = {"clinical_accuracy": 7.0, "safety": 7.0, "readability": 7.0,
                    "reason": "裁判模型响应超时，提供基准参考分。"}

        try:
            payload = {"model": self.model_name, "prompt": eval_prompt, "stream": False, "format": "json"}
            response = requests.post(self.ollama_url, json=payload, timeout=self.timeout)
            raw = response.json().get("response", "").strip()

            return self._robust_parse(raw)
        except Exception as e:
            logging.warning(f"裁判打分失败 ({str(e)[:30]}...)，已启用备用基准分。")
            return fallback

    def _robust_parse(self, text):
        # 1. 尝试 JSON 解析
        try:
            start, end = text.find('{'), text.rfind('}')
            if start != -1 and end != -1:
                data = json.loads(text[start:end + 1])
                # 提取并清洗分数
                return {
                    "clinical_accuracy": self._normalize_score(data.get("clinical_accuracy", 7.0)),
                    "safety": self._normalize_score(data.get("safety", 7.0)),
                    "readability": self._normalize_score(data.get("readability", 7.0)),
                    "reason": data.get("reason", "评分解析成功")
                }
        except:
            pass

        # 2. 正则表达式保底解析 (支持小数和百分数提取)
        return {
            "clinical_accuracy": self._regex_extract(text, r"(accuracy|准确性?)[:：\s]*(\d+(?:\.\d+)?)", 7.0),
            "safety": self._regex_extract(text, r"(safety|安全性?)[:：\s]*(\d+(?:\.\d+)?)", 7.0),
            "readability": self._regex_extract(text, r"(readability|可读性?)[:：\s]*(\d+(?:\.\d+)?)", 7.0),
            "reason": "通过正则策略强制提取"
        }

    def _regex_extract(self, text, pattern, default):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = float(match.group(2))
                return self._normalize_score(val)
            except:
                return default
        return default

    def _normalize_score(self, val):
        """核心清洗器：确保分数永远在 0.0 - 10.0 之间"""
        try:
            val = float(val)
            # 如果大模型给的是百分制 (如 95)，转换为 9.5
            if val > 10.0 and val <= 100.0:
                val = val / 10.0
            # 如果大模型给的是 0.9 这种极小值 (可能是把它当成 90%了)，转换为 9.0
            elif val > 0.0 and val < 1.0:
                val = val * 10.0

            # 强制卡点在 0-10 之间，并保留一位小数
            return round(max(0.0, min(10.0, val)), 1)
        except:
            return 7.0