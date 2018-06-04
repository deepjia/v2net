#!/usr/bin/env python3
import sys
import os
import subprocess
import configparser
import json
import pyperclip
from jinja2 import Template
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import *

class Config:
    def __init__(self, file):
        class MyConfig(configparser.ConfigParser):
            def __init__(self, defaults=None):
                configparser.ConfigParser.__init__(self, defaults=None)

            def optionxform(self, optionstr):
                return optionstr

        self.config = MyConfig()
        self.config.read(file, encoding='UTF-8')

    def get_items(self, section):
        return self.config[section].items()

    def get(self, section, key):
        return self.config[section][key]

base_path = os.path.dirname(os.path.realpath(__file__))
extension_path = os.path.join(base_path, 'extension')
profile_path = os.path.join(base_path, 'profile')
profile = Config(os.path.join(profile_path, 'profile.ini'))
http_port = ''
socks_port = ''
selected = [x.strip() for x in profile.get('General', 'selected').split(',')]
current = {
    'proxy': None,
    'bypass': None,
    'capture': None
}
system = True if profile.get('General','system').strip().lower()=='true' else False
current_proxy = None
current_bypass = None
current_capture = None
app = QApplication([])
app.setQuitOnLastWindowClosed(False)


class Extension:
    def __init__(self, extension, menu_enable, extension_type):
        self.type = extension_type
        self.menu_enable = menu_enable
        self.extension, *self.values = [x.strip() for x in extension[1].split(',')]
        self.name = extension[0]
        self.QAction = QAction(self.name)
        self.QAction.setCheckable(True)
        self.QAction.triggered.connect(self.select)
        if self.name in selected:
            self.QAction.setChecked(True)
            self.menu_enable.setChecked(True)
            self.select()

    def select(self):
        self.menu_enable.setChecked(True)
        self.menu_enable.setDisabled(False)
        #self.QAction.setChecked(True)
        #t = threading.Thread(target=self.run, name='Start Extension')
        #t.start()
        self.run()

    def run(self):
        global current
        if current[self.type]:
            current[self.type].stop()
        current[self.type] = self
        self.folder = os.path.join(extension_path, self.extension)
        with open(os.path.join(self.folder, 'extension.json'), 'r') as f:
            self.json = json.loads(f.read())
        self.bin = self.json['bin']
        self.keys = self.json['keys']
        self.render = self.json['render']
        self.http = self.json['http']
        self.socks = self.json['socks']
        self.default = self.json['default']
        #过滤掉空的
        self.jinja_dict = dict(self.default, **dict(filter(lambda x:x[1], zip(self.keys, self.values))))
        self.port = self.setport()
        self.jinja_dict['ExtensionPort'] = self.port
        self.args = Template(self.json['args']).render(**self.jinja_dict).split()
        print('args:',self.args,"Port",self.port)
        self.exitargs = Template(self.json['exitargs']).render(**self.jinja_dict).split()
        for src, dist in self.render.items():
            with open(os.path.join(self.folder, src), 'r') as f:
                content = Template(f.read()).render(**self.jinja_dict)
            with open(os.path.join(self.folder, dist), 'r+') as f:
                if content != Template(f.read()).render(**self.jinja_dict):
                    f.seek(0)
                    f.write(content)
                    f.truncate()
        self.process = subprocess.Popen([self.bin, *self.args])
        self.pid = self.process.pid
        if system: setproxy()


    def setport(self):
        pass

    def stop(self):
        self.stop_list()

    def stop_list(self):
        global current
        if self.exitargs:
            subprocess.run([self.bin, *self.exitargs], check=True)
        if self.process.returncode is None:
            self.process.terminate()
            self.process.wait()
        #self.QAction.setChecked(False)
        current[self.type] = None
        if system: setproxy()

    @staticmethod
    def disable_extension(menu_enable, extension_type):
        menu_enable.setDisabled(True)
        current[extension_type].QAction.setChecked(False)
        current[extension_type].stop()



class Proxy(Extension):
    def setport(self):
        if current["bypass"] or current["capture"]:
            self.port = profile.get('General', 'InnerPortProxy')
        else:
            self.port = profile.get('General', 'Port')
            global http_port, socks_port
            http_port = self.port if self.http else ''
            socks_port = self.port if self.socks else ''
        return self.port

class Bypass(Extension):
    def setport(self):
        if current["proxy"]:
            current["proxy"].run()
            self.jinja_dict['ServerPort'] = current["proxy"].port
        if current["capture"]:
            self.port = profile.get('General', 'InnerPortBypass')
        else:
            self.port = profile.get('General', 'Port')
            global http_port, socks_port
            http_port = self.port if self.http else ''
            socks_port = self.port if self.socks else ''
        return self.port

    def stop(self):
        self.stop_list()
        if current['proxy']:
            current['proxy'].run()

class Capture(Extension):
    def setport(self):
        if current["bypass"]:
            current["bypass"].run()
            self.jinja_dict['ServerPort'] = current["bypass"].port
        elif current["proxy"]:
            current["proxy"].select()
            self.jinja_dict['ServerPort'] = current["proxy"].port
        self.port = profile.get('General', 'Port')
        global http_port, socks_port
        http_port = self.port if self.http else ''
        socks_port = self.port if self.socks else ''
        return self.port
    def stop(self):
        self.stop_list()
        if current['bypass']:
            current['bypass'].run()


class Dashboard(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Dashboard, self).__init__(*args, **kwargs)
        self.resize(1280, 720)
        self.setWindowTitle('[Dashboard] Whistle Web Debugger')
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

    def show_dashboard(self):
        if current['capture']:
            self.browser.setUrl(QUrl("http://127.0.0.1:"+http_port+"/#Network"))
            self.show()



def quitapp():
    for ins in filter(None, current.values()):
        ins.stop()
    app.exit()

def setproxy_menu(qaction):
    global system
    if qaction.isChecked():
        print("checked")
        system = True
        setproxy()
    else:
        print("not checked")
        system = False
        setproxy()

def setproxy():
    global system
    if system:
        print('setproxy')
        if http_port:
            subprocess.run('networksetup -setwebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
            subprocess.run('networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
            #subprocess.run('networksetup -setwebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
            #subprocess.run('networksetup -setsecurewebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
        if socks_port:
            subprocess.run('networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 ' + socks_port, shell=True)
            #subprocess.run('networksetup -setsocksfirewallproxy "Ethernet" 127.0.0.1 ' + socks_port,shell=True)
    else:
        subprocess.run('networksetup -setwebproxystate "Wi-Fi" off', shell=True)
        subprocess.run('networksetup -setsecurewebproxystate "Wi-Fi" off', shell=True)
        subprocess.run('networksetup -setsocksfirewallproxystate "Wi-Fi" off', shell=True)
        #subprocess.run('networksetup -setwebproxystate "Ethernet" off',shell=True)
        #subprocess.run('networksetup -setsecurewebproxystate "Ethernet" off',shell=True)
        #subprocess.run('networksetup -setsocksfirewallproxystate "Ethernet" off',shell=True)

def copy_shell():
    cmd = []
    if http_port:
        cmd.append('export https_proxy=http://127.0.0.1:' + http_port + ';export http_proxy=http://127.0.0.1:' + http_port)
    else:
        cmd.append('unset https_proxy;unset http_proxy')
    if socks_port:
        cmd.append('export all_proxy=http://127.0.0.1:' + socks_port)
    else:
        cmd.append('unset all_proxy')
    pyperclip.copy(';'.join(cmd))

def main():
    menu = QMenu()
    # Proxy
    m_proxy = QAction("ᴘʀᴏxʏ")
    m_proxy.setCheckable(True)
    m_proxy.setDisabled(True)
    m_proxy.triggered.connect(lambda: Extension.disable_extension(m_proxy, "proxy"))
    menu.addAction(m_proxy)
    proxy_dict = {}
    proxy_group = QActionGroup(menu)
    for proxy in profile.get_items('Proxy'):
        proxyname = proxy[0]
        proxy_dict[proxyname] = Proxy(proxy, m_proxy, "proxy")
        proxy_group.addAction(proxy_dict[proxyname].QAction)
        menu.addAction(proxy_dict[proxyname].QAction)


    # Bypass
    menu.addSeparator()
    m_bypass = QAction("ʙʏᴘᴀss")
    m_bypass.setCheckable(True)
    m_bypass.setDisabled(True)
    m_bypass.triggered.connect(lambda: Extension.disable_extension(m_bypass, "bypass"))
    menu.addAction(m_bypass)
    bypass_dict = {}
    bypass_group = QActionGroup(menu)
    for bypass in profile.get_items('Bypass'):
        bypassname = bypass[0]
        bypass_dict[bypassname] = Bypass(bypass, m_bypass, "bypass")
        bypass_group.addAction(bypass_dict[bypassname].QAction)
        menu.addAction(bypass_dict[bypassname].QAction)


    # Capture
    menu.addSeparator()
    m_capture = QAction("ᴄᴀᴘᴛᴜʀᴇ")
    m_capture.setCheckable(True)
    m_capture.setDisabled(True)
    m_capture.triggered.connect(lambda: Extension.disable_extension(m_capture, "capture"))
    menu.addAction(m_capture)
    capture_dict = {}
    capture_group = QActionGroup(menu)
    for capture in profile.get_items('Capture'):
        capturename = capture[0]
        capture_dict[capturename] = Capture(capture, m_capture, "capture")
        capture_group.addAction(capture_dict[capturename].QAction)
        menu.addAction(capture_dict[capturename].QAction)
    m_dashboard = QAction("Open Dashboard...")
    window = Dashboard()
    m_dashboard.triggered.connect(window.show_dashboard)
    menu.addAction(m_dashboard)

    # Common
    m_profile = QAction("Open Profile Folder")
    m_profile.triggered.connect(lambda: subprocess.call(["open", profile_path]))
    m_extension = QAction("Open Extension Folder")
    m_extension.triggered.connect(lambda: subprocess.call(["open", extension_path]))
    m_copy_shell = QAction("Copy Shell Command")
    m_set_system = QAction("Set As System Proxy")
    m_set_system.triggered.connect(lambda: setproxy_menu(m_set_system))
    m_copy_shell.triggered.connect(copy_shell)
    m_set_system.setCheckable(True)
    if system:
        m_set_system.setChecked(True)
        setproxy()
    menu.addSeparator()
    menu.addAction(m_set_system)
    menu.addSeparator()
    menu.addAction(m_profile)
    menu.addAction(m_extension)
    menu.addAction(m_copy_shell)
    menu.addSeparator()
    m_quit = QAction("Quit V2Net")
    m_quit.triggered.connect(quitapp)
    menu.addAction(m_quit)

    # Add Tray
    tray = QSystemTrayIcon()
    tray.setIcon(QIcon("icon.png"))
    tray.setVisible(True)
    tray.setContextMenu(menu)
    sys.exit(app.exec_())


if __name__ == '__main__':
    try:
        main()
    finally:
        quitapp()