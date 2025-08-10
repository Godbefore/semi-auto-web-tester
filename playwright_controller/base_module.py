from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from playwright.sync_api import Page

class BaseModule:
    page: Optional["Page"]

    def __init__(self):
        self.page = None

    def click_button(self, selector):
        self.page.click(selector)
        return f"点击了按钮：{selector}"

    def input_text(self, selector, text):
        self.page.fill(selector, text)
        return f"在{selector}输入了文本：{text}"

    def select_option(self, selector, value):
        self.page.select_option(selector, value)
        return f"选择了{selector}的选项：{value}"
