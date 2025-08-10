from common.logger import logger

REGISTERED_METHODS = []

def register_method(display_name, category="通用", order=0):
    def decorator(func):
        from functools import wraps

        @wraps(func)
        def wrapper(*args, **kwargs):
            from playwright_controller.controller import browser_controller
            if not browser_controller.page:
                raise RuntimeError("浏览器未启动或 Page 未初始化")

            if len(args) > 0:
                self = args[0]
                self.page = browser_controller.page
            else:
                kwargs["page"] = browser_controller.page

            result = func(*args, **kwargs)
            logger.info(f"方法 {display_name} 执行结果: {result}")
            # 默认返回结构化结果（如果原函数没返回，就生成一个默认的）
            if result is None:
                result = {
                    "status": "success",
                    "message": f"执行成功：{display_name}",
                    "data": None
                }
            elif not isinstance(result, dict):
                result = {
                    "status": "success",
                    "message": str(result),
                    "data": result
                }
            return result

        REGISTERED_METHODS.append({
            "func_name": func.__name__,
            "display": display_name,
            "category": category,
            "order": order,
            "func": wrapper
        })
        return wrapper
    return decorator


def get_registered_methods():
    return sorted(REGISTERED_METHODS, key=lambda x: (x["category"], x["order"]))
