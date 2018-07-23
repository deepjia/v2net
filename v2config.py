#!/usr/bin/env python3
# coding=utf-8
import configparser

class Config:
    def __init__(self, file):
        class MyConfig(configparser.ConfigParser):
            def __init__(self):
                configparser.ConfigParser.__init__(self, defaults=None)

            def optionxform(self, optionstr):
                return optionstr

        self.config = MyConfig()
        self.file = file
        self.config.read(file, encoding='UTF-8')

    def get_items(self, section):
        return self.config[section].items()

    def get(self, section, key, fallback = None):
        return self.config[section].get(key, fallback)

    def write(self, section, key, value):
        self.config.set(section, key, value)
        with open(self.file, 'w+', encoding='UTF-8') as f:
            self.config.write(f)
