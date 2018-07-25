#!/usr/bin/env python3
# coding=utf-8
import configparser
import sys
import subprocess
from PyQt5.QtWidgets import QWidget, QMessageBox

class Config:
    def __init__(self, file):
        class MyConfig(configparser.ConfigParser):
            def __init__(self):
                configparser.ConfigParser.__init__(self, defaults=None)

            def optionxform(self, optionstr):
                return optionstr

        self.config = MyConfig()
        self.file = file
        try:
            self.config.read(file, encoding='UTF-8')
        except Exception as e:
            QMessageBox.critical(QWidget(), 'Critical', repr(e))
            subprocess.run(["open", file])
            sys.exit(1)

    def get_items(self, section):
        try:
            return self.config[section].items()
        except Exception as e:
            QMessageBox.critical(QWidget(), 'Critical', repr(e) + ' in file: ' + self.file)
            subprocess.run(["open", self.file])
            sys.exit(1)

    def get(self, section, key, fallback = None):
        return self.config[section].get(key, fallback)

    def write(self, section, key, value):
        self.config.set(section, key, value)
        with open(self.file, 'w+', encoding='UTF-8') as f:
            self.config.write(f)
