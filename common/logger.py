"""写日志文件."""
# -*- coding :utf-8 -*-
import logging
import time
import os.path


class Logger(object):
    """日志类."""
    def __init__(self):
        """init vales."""
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)  # Log等级总开关

        strtime = time.strftime('%Y%m%d', time.localtime(time.time()))
        log_path = os.path.dirname(os.getcwd()) + '\\logs\\'
        try:
            if not os.path.exists(log_path):
                os.makedirs(log_path)
        except IOError as ex:
            print(ex)

        log_name = log_path + strtime + '.log'
        if not os.path.exists(log_name):
            file = open(log_name, 'w')
            file.close()

        # 创建一个handler，用于写入日志文件
        filehandler = logging.FileHandler(log_name, encoding='utf-8')
        filehandler.setLevel(logging.DEBUG)  # 输出到file的log等级的开关

        # 创建一个handler，用于输出到控制台
        streamhandler = logging.StreamHandler()
        streamhandler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s'
                                      ' - %(filename)s[line:%(lineno)d]'
                                      '- %(levelname)s: %(message)s')
        filehandler.setFormatter(formatter)
        streamhandler.setFormatter(formatter)

        self.logger.addHandler(filehandler)
        self.logger.addHandler(streamhandler)

    def getlog(self):
        """ 获取日志对象 """
        return self.logger
