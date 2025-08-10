from playwright_controller.methods_registry import register_method
from playwright_controller.base_module import BaseModule

class AwardModule(BaseModule):

    @register_method("登录", category="通用", order=1)
    def login(self):
        pass
