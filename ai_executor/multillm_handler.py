import requests
import os
import re
from common.logger import logger


class MultiLLMHandler:
    def __init__(self, provider: str, api_key: str = None):
        """
        provider: deepseek | openai | claude | gemini
        api_key: 对应平台的 API Key（可不传，自动从环境变量读取）
        """
        self.provider = provider.lower()

        # 直接在 init 读取 API key
        env_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "CLAUDE_API_KEY",
            "gemini": "GEMINI_API_KEY"
        }
        self.api_key = api_key or os.getenv(env_map.get(self.provider, ""))

        if not self.api_key:
            raise ValueError(f"{self.provider} API key 未提供且环境变量未设置。")
        self.base_url, self.headers_template = self._get_api_config()

    def _get_api_config(self):
        if self.provider == "deepseek":
            return (
                "https://api.deepseek.com/v1/chat/completions",
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        elif self.provider == "openai":
            return (
                "https://api.openai.com/v1/chat/completions",
                {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
            )
        elif self.provider == "claude":
            return (
                "https://api.anthropic.com/v1/messages",
                {
                    "x-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                }
            )
        elif self.provider == "gemini":
            return (
                f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={self.api_key}",
                {
                    "Content-Type": "application/json"
                }
            )
        else:
            raise ValueError(f"未知 provider: {self.provider}")

    def natural_to_playwright(self, natural_text: str) -> str:
        """
        通用方法：将自然语言转为 Playwright Python 代码
        """
        prompt = f"""
        你是一个专业的 Playwright Python 脚本生成器。
        请将以下自然语言转换为 **可直接运行的 Python 代码**。
        要求：
        1. **只能使用现有的变量 page（Playwright Page 对象）**，不要生成浏览器启动代码、上下文管理器（with sync_playwright()）、async 关键字。
        2. 不要导入 playwright。
        3. 不要执行 launch、new_page、goto 等浏览器初始化动作，除非用户明确要求访问网址。
        4. 返回的必须是 **纯 Python 代码**，不能附加解释、中文文字或 Markdown 代码块标记。
        自然语言: {natural_text}
        """

        payload = self._build_payload(prompt)
        response = requests.post(self.base_url, headers=self.headers_template, json=payload)
        data = response.json()
        code = self._extract_code(data)

        logger.info(f"\n=== {self.provider.capitalize()} 给出的 Python 代码 ===")
        logger.info(code)
        logger.info("=======================\n")

        return code

    def _build_payload(self, prompt: str):
        if self.provider in ["deepseek", "openai"]:
            return {
                "model": "deepseek-chat" if self.provider == "deepseek" else "gpt-4o",
                "messages": [
                    {"role": "system", "content": "你是一个专业的 Playwright 自动化脚本生成器。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
        elif self.provider == "claude":
            return {
                "model": "claude-3-opus-20240229",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        elif self.provider == "gemini":
            return {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }

    def _extract_code(self, data):
        if self.provider in ["deepseek", "openai"]:
            code = data["choices"][0]["message"]["content"].strip()
        elif self.provider == "claude":
            code = data["content"][0]["text"].strip()
        elif self.provider == "gemini":
            code = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            code = ""

        code_match = re.findall(r"```python(.*?)```", code, re.S)
        return code_match[0].strip() if code_match else code.strip()
