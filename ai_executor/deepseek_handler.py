import requests
import os
import re
from common.logger import logger


class DeepSeekHandler:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"


    def natural_to_playwright(self, natural_text: str) -> str:
        """
        调用 DeepSeek API，将自然语言翻译成 Playwright Python 代码
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        prompt=f""" 
                你是一个专业的 Playwright Python 脚本生成器。
                请将以下自然语言转换为 **可直接运行的 Python 代码**。
                要求：
                1. **只能使用现有的变量 page（Playwright Page 对象）**，不要生成浏览器启动代码、上下文管理器（with sync_playwright()）、async 关键字。
                2. 不要导入 playwright。
                3. 不要执行 launch、new_page、goto 等浏览器初始化动作，除非用户明确要求访问网址。
                4. 返回的必须是 **纯 Python 代码**，不能附加解释、中文文字或 Markdown 代码块标记。
                自然语言: {natural_text}
                """
        payload = {
            "model": "deepseek-chat",  # DeepSeek 对话模型
            "messages": [
                {"role": "system", "content": "你是一个专业的 Playwright 自动化脚本生成器。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }

        response = requests.post(self.base_url, headers=headers, json=payload)
        data = response.json()

        # 🚀 调试：打印 DeepSeek 返回的完整内容
        code = data["choices"][0]["message"]["content"].strip()
        logger.info("\n=== DeepSeek 给出的 Python 代码 ===")
        logger.info(code)
        logger.info("=======================\n")
        code_match = re.findall(r"```python(.*?)```", code, re.S)
        if code_match:
            code = code_match[0].strip()
        else:
            # 如果没有 markdown 格式，直接清理掉可能的中文提示
            code = code.strip()

        return code

