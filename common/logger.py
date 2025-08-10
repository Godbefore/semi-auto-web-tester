# coding:utf8
import logging
import os
import sys
import time


class Logger:
    def __init__(self, set_level="INFO", name=None, log_name=None, log_path=None, console_level="INFO"):
        """
        :param set_level: 日志级别["NOTSET"|"DEBUG"|"INFO"|"WARNING"|"ERROR"|"CRITICAL"]，默认为INFO
        :param log_name: 日志文件的名字，默认为当前时间（年-月-日.log）
        :param log_path: 日志文件夹的路径，默认为logger.py同级目录中的log文件夹
        :param console_level: 控制台打印的最低日志级别，默认为WARNING
        """
        if name is None:
            name = os.path.split(os.path.splitext(sys.argv[0])[0])[-1]
        if log_name is None:
            log_name = time.strftime("%Y-%m-%d.log", time.localtime())
        if log_path is None:
            log_path = os.path.join(os.getcwd(), "log")

        if not set_level:
            set_level = self._exec_type()  # 设置set_level为None，自动获取当前运行模式

        self.__logger = logging.getLogger(name)
        self.__logger.setLevel(
            getattr(logging, set_level.upper()) if hasattr(logging, set_level.upper()) else logging.INFO)

        if not os.path.exists(log_path):  # 创建日志目录
            os.makedirs(log_path)

        formatter = logging.Formatter("[%(asctime)s][%(filename)s][%(lineno)d][%(levelname)s] %(message)s")

        file_handler = logging.FileHandler(os.path.join(log_path, log_name), encoding="utf-8")
        file_handler.setFormatter(formatter)
        self.__logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(
            getattr(logging, console_level.upper()) if hasattr(logging, console_level.upper()) else logging.WARNING)
        console_handler.setFormatter(formatter)
        self.__logger.addHandler(console_handler)

    def _exec_type(self):
        # Dummy implementation of _exec_type for demonstration
        return "INFO"

    def get_logger(self):
        return self.__logger

    def __getattr__(self, item):
        return getattr(self.logger, item)

    @property
    def logger(self):
        return self.__logger

    @logger.setter
    def logger(self, func):
        self.__logger = func

    def _exec_type(self):
        return "DEBUG" if os.environ.get("IPYTHONENABLE") else "INFO"


logger = Logger()


if __name__ == '__main__':
    logger.critical('critical level')
    logger.error('error level')
    logger.warning('warning level')
    logger.info('info level')
    logger.debug('debug level')
