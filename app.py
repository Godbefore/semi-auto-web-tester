import os
import base64
import io, sys, traceback
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from common.logger import logger
from playwright_controller.controller import browser_controller
from playwright_controller.methods_registry import REGISTERED_METHODS, get_registered_methods
from common.read_data import read_yaml
from collections import defaultdict
from ai_executor.multillm_handler import MultiLLMHandler
from playwright_controller.methods_loader import load_all_modules

app = Flask(__name__)
app.url_map.strict_slashes = False
load_all_modules()

# 存储最近一次错误
last_error = ''

config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
deepseek_api = read_yaml(config_path)["api_keys"]["deepseek"]
deepseek_handler = MultiLLMHandler("deepseek", deepseek_api)


class DummyPage:
    def __getattr__(self, name):
        def method(*args, **kwargs):
            logger.warning(f"DummyPage: 调用了不存在的方法 {name}，无操作。")
            return None
        return method

@app.errorhandler(Exception)
def handle_exception(e):
    global last_error
    last_error = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:\n{traceback.format_exc()}"
    if "浏览器未启动或 Page 未初始化" in str(e):
        logger.error("浏览器未启动或 Page 未初始化")
        last_error = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}：请先初始化浏览器"
    elif "Target page, context or browser has been closed" in str(e):
        logger.error("Page可能被关闭")
        last_error = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}：浏览器未启动或已关闭，请初始化浏览器"
    elif "Timeout" in str(e):
        last_error = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 处理超时：\n{str(e)}"
        logger.error(f"处理超时：{str(e)}")
    else:
        logger.error(f"处理过程中发现未知异常: {e}")
    return index(), 200


@app.route('/')
def index():
    grouped_methods = defaultdict(list)
    for m in get_registered_methods():
        grouped_methods[m["category"]].append(m)
    return render_template('index.html',
                           code_output='',
                           error_message=last_error,
                           screenshot_data=None,
                           grouped_methods=dict(grouped_methods))

@app.route('/start', methods=['POST'])
def start():
    try:
        browser_controller.start_browser()
        logger.info("浏览器已启动（或重启）")
    except Exception as e:
        logger.error(f"启动浏览器失败: {e}")
    return redirect(url_for('index'))

@app.route('/load', methods=['POST'])
def load_page():
    url = request.form.get('url')
    if url:
        try:
            browser_controller.load_url(url)
        except Exception as e:
            logger.error(f"加载出错: {e}")
    return redirect(url_for('index'))

@app.route('/refresh', methods=['POST'])
def refresh_page():
    browser_controller.refresh()
    return redirect(url_for('index'))

@app.route('/run_func/<name>', methods=['POST'])
def run_func(name):
    # 从注册表里找对应的方法
    method_entry = next((m for m in REGISTERED_METHODS if m["func_name"] == name), None)
    if not method_entry:
        raise AttributeError(f"未找到方法: {name}")
    # 调用方法，把 browser_controller 作为 self 传入
    func = method_entry["func"]
    func(browser_controller)  # 如果 func 是类方法，需要传入 browser_controller

    return redirect(url_for('index'))


@app.route('/execute_code', methods=['POST'])
def execute_code():
    code = request.form.get('code')
    logger.info(f"将要执行的python代码是：{code}")
    output = ''
    if code:
        if browser_controller.page is None:
            raise Exception("Target page, context or browser has been closed")
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        try:
            # 只在 page 未初始化时才使用 DummyPage
            if browser_controller.page is None:
                exec_page = DummyPage()
            else:
                exec_page = browser_controller.page

            exec_globals = {
                "page": exec_page,
                "browser_controller": browser_controller,
            }
            exec(code, exec_globals)
            output = f"执行代码\n{code}\n成功：\n" + sys.stdout.getvalue()
        except Exception:
            output = "执行代码出错：" + traceback.format_exc()
        finally:
            sys.stdout = old_stdout

    grouped_methods = defaultdict(list)
    for m in sorted(REGISTERED_METHODS, key=lambda x: (x["category"], x["order"])):
        grouped_methods[m["category"]].append(m)
    return render_template(
        'index.html',
        code_output=output,
        grouped_methods=dict(grouped_methods)
    )

@app.route('/screenshot', methods=['POST'])
def screenshot():
    if browser_controller.page is None:
        return jsonify({"error": "浏览器未启动"}), 500
    try:
        img_bytes = browser_controller.page.screenshot()
        b64_str = base64.b64encode(img_bytes).decode('utf-8')
        return jsonify({"success": True, "image": b64_str})
    except Exception as e:
        if "browser has been closed" in str(e):
            e = "浏览器已关闭"
        return jsonify({"error": str(e)}), 500


@app.route('/nl_to_code', methods=['POST'])
def nl_to_code():
    generated_code = ""
    grouped_methods = defaultdict(list)
    for m in sorted(REGISTERED_METHODS, key=lambda x: (x["category"], x["order"])):
        grouped_methods[m["category"]].append(m)
    try:
        natural_text = request.form.get('nl_text', '').strip()
        if browser_controller.page is None:
            raise Exception("Target page, context or browser has been closed")
        if not natural_text:
            return redirect(url_for('index'))

        # 1. 调用 DeepSeek API 获取代码
        generated_code = deepseek_handler.natural_to_playwright(natural_text)

        # 安全过滤：删除可能导致冲突的代码
        import re
        forbidden_patterns = [
            r"with\s+sync_playwright\([^)]*\)\s*:",  # 删除 with sync_playwright()
            r"async\s+def\s+.*?:",  # 删除 async 定义
            r"await\s+.*",  # 删除 await
            r"launch\(.*\)",  # 删除 launch()
            r"new_page\(.*\)",  # 删除 new_page()
        ]
        for pattern in forbidden_patterns:
            generated_code = re.sub(pattern, "", generated_code, flags=re.S)

        logger.info("\n=== 最终要执行的 Python 代码 ===")
        logger.info(generated_code)
        logger.info("================================\n")

        # 执行
        local_vars = {"page": browser_controller.page}
        exec(generated_code, {}, local_vars)


        # 2. 执行代码（使用已有的 page）
        local_vars = {"page": browser_controller.page}
        exec(generated_code, {}, local_vars)

        # 3. 返回页面并显示生成的代码
        return render_template(
            'index.html',
            generated_code=generated_code,
            code_output=f"成功执行自然语言指令：{natural_text}",
            grouped_methods=dict(grouped_methods)
        )

    except Exception as e:
        err_msg = traceback.format_exc()
        return render_template(
            'index.html',
            generated_code=generated_code,
            code_output=f"执行代码出错:\n{err_msg}",
            grouped_methods=dict(grouped_methods)
        )

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, ''),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/<path:unknown_path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def catch_all(unknown_path):
    logger.warning(f"⚠️ 未匹配的请求路径: /{unknown_path}, 方法: {request.method}")
    return f"未匹配的路径: /{unknown_path}", 404

if __name__ == '__main__':
    app.run(debug=True, threaded=False)  # 单线程，避免跨线程问题
    #app.run(host='0.0.0.0', debug=True, threaded=False)  # 单线程，避免跨线程问题
