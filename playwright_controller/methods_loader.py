import importlib
import pkgutil

def load_all_methods_from(package_name: str):
    """递归加载指定包下的所有模块"""
    package = importlib.import_module(package_name)
    for module_info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(module_info.name)

def load_all_modules():
    # 你可以在这里加多个根目录
    method_packages = [
        "playwright_controller.a_methods",
        "playwright_controller.b_methods",
        "playwright_controller.common_methods",
    ]
    for pkg in method_packages:
        load_all_methods_from(pkg)
