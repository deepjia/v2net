#!/usr/bin/env python3
#coding=utf-8
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import subprocess


class Dashboard(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(1280, 720)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

    def show_dashboard(self, extesnion_name, url):
        self.setWindowTitle('[V2Net Dashboard] ' + extesnion_name + ' Web Debugger')
        self.browser.setUrl(QUrl(url))
        #self.show()
        #self.activateWindow()
        subprocess.run('open -a Safari ' + url, shell=True, check=True)


APP = QApplication([])
APP.setQuitOnLastWindowClosed(False)
WINDOW = Dashboard()
