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
        self.file = file
        self.config.read(file, encoding='UTF-8')

    def get_items(self, section):
        return self.config[section].items()

    def get(self, section, key):
        return self.config[section][key]

    def write(self, section, key, value):
        self.config.set(section, key, value)
        with open(self.file,'w+', encoding='UTF-8') as f:
            self.config.write(f)

base_path = os.path.dirname(os.path.realpath(__file__))
extension_path = os.path.join(base_path, 'extension')
profile_path = os.path.join(base_path, 'profile')
profile_file = os.path.join(profile_path, 'profile.ini')
profile = Config(profile_file)
skip_proxy = [x.strip() for x in profile.get('General', 'skip-proxy').split(',')]
http_port = ''
socks_port = ''
selected = {x:profile.get('General', x) for x in ('proxy', 'bypass', 'capture')}
current = {x:None for x in ('proxy', 'bypass', 'capture')}
system = True if profile.get('General','system').strip().lower()=='true' else False
app = QApplication([])
app.setQuitOnLastWindowClosed(False)


class Extension:
    def __init__(self, extension, *menus_to_enable):
        #self.type = ''
        self.menus_to_enable = menus_to_enable
        self.extension, *self.values = [x.strip() for x in extension[1].split(',')]
        self.name = extension[0]
        self.QAction = QAction(self.name)
        self.QAction.setCheckable(True)
        self.QAction.triggered.connect(self.select)

    def select(self):
        for menu_to_enable in self.menus_to_enable:
            menu_to_enable.setChecked(True)
            menu_to_enable.setDisabled(False)
        self.QAction.setChecked(True)
        #t = threading.Thread(target=self.run, name='Start Extension')
        #t.start()
        self.folder = os.path.join(extension_path, self.extension)
        with open(os.path.join(self.folder, 'extension.json'), 'r') as f:
            json_str = f.read()
            json_temp = json.loads(json_str)
            print(json_temp)
        self.default = json_temp['default']
        self.keys = json_temp['keys']
        self.http = json_temp['http']
        self.socks = json_temp['socks']
        # new json string
        self.jinja_dict = dict(self.default, **dict(filter(lambda x: x[1], zip(self.keys, self.values))))
        self.port = self.setport()
        self.jinja_dict['ExtensionPort'] = self.port
        self.json = json.loads(Template(json_str).render(**self.jinja_dict))
        print(self.json)
        self.bin = self.json['bin']
        self.render = self.json['render']
        self.url = self.json.get('url')
        self.args = self.json['args'].split()
        print('Runargs:',self.args,"Port",self.port)
        self.exitargs = self.json['exitargs'].split()
        print("Exitargs",self.exitargs)
        for src, dist in self.render.items():
            with open(os.path.join(self.folder, src), 'r') as f:
                content = Template(f.read()).render(**self.jinja_dict)
            with open(os.path.join(self.folder, dist), 'r+') as f:
                if content != Template(f.read()).render(**self.jinja_dict):
                    f.seek(0)
                    f.write(content)
                    f.truncate()
        print('Starting...')
        self.process = subprocess.Popen([self.bin, *self.args])
        self.pid = self.process.pid
        if system: setproxy()


    def setport(self):
        pass

    def stop(self):
        #global current
        if self.exitargs:
            subprocess.run([self.bin, *self.exitargs], check=True)
        if self.process.returncode is None:
            self.process.terminate()
            self.process.wait()
        #self.QAction.setChecked(False)
        #current[self.type] = None
        if system: setproxy()

    def disable(self, *menus_to_disable):
        for menu_to_disable in menus_to_disable:
            menu_to_disable.setDisabled(True)
        self.QAction.setChecked(False)
        self.stop()


class Proxy(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        print(self.name)
        print(selected['proxy'])
        if self.name == selected['proxy']:
            print('select')
            self.select()
        #self.QAction.triggered.connect(self.select)

    def select(self):
        if current['proxy']:
            print('Stoping proxy...')
            current['proxy'].stop()
        current['proxy'] = self
        profile.write('General', 'proxy', self.name)
        super().select()

    def stop(self):
        super().stop()
        current['proxy'] = None

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'proxy', '')

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
    def __init__(self, *args):
        super().__init__(*args)
        if self.name == selected['bypass']:
            self.select()
        #self.QAction.triggered.connect(self.select)

    def select(self):
        if current['bypass']:
            print('Stoping bypass...')
            current['bypass'].stop()
        current['bypass'] = self
        profile.write('General', 'bypass', self.name)
        super().select()

    def setport(self):
        if current["proxy"]:
            current["proxy"].select()
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
        super().stop()
        current['bypass'] = None
        if current['proxy']:
            current['proxy'].select()

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'bypass', '')


class Capture(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        if self.name == selected['capture']:
            self.select()
        #self.QAction.triggered.connect(self.select)

    def select(self):
        if current['capture']:
            print('Stoping capture...')
            current['capture'].stop()
        current['capture'] = self
        super().select()
        profile.write('General', 'capture', self.name)
        window = Dashboard()
        self.menus_to_enable[1].triggered.connect(lambda :window.show_dashboard(self.extension.title(), self.url))

    def setport(self):
        if current["bypass"]:
            current["bypass"].select()
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
        super().stop()
        current['capture'] = None
        if current['bypass']:
            current['bypass'].select()

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'capture', '')


class Dashboard(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(Dashboard, self).__init__(*args, **kwargs)
        self.resize(1280, 720)
        self.browser = QWebEngineView()
        self.setCentralWidget(self.browser)

    def show_dashboard(self, extesnion_name, url):
        self.setWindowTitle('[V2Net Dashboard] '+ extesnion_name +' Web Debugger')
        self.browser.setUrl(QUrl(url))
        self.show()



def quitapp():
    for ins in filter(None, current.values()):
        ins.stop()
    print("Quiting")
    app.exit()

def setproxy_menu(qaction):
    global system
    if qaction.isChecked():
        print("checked")
        system = True
        setproxy()
        profile.write('General', 'system', 'true')
    else:
        print("not checked")
        system = False
        setproxy()
        profile.write('General', 'system', 'false')

def setproxy():
    print('setproxy')
    subprocess.run('networksetup -setwebproxystate "Wi-Fi" off', shell=True)
    subprocess.run('networksetup -setsecurewebproxystate "Wi-Fi" off', shell=True)
    subprocess.run('networksetup -setsocksfirewallproxystate "Wi-Fi" off', shell=True)
    # subprocess.run('networksetup -setwebproxystate "Ethernet" off',shell=True)
    # subprocess.run('networksetup -setsecurewebproxystate "Ethernet" off',shell=True)
    # subprocess.run('networksetup -setsocksfirewallproxystate "Ethernet" off',shell=True)
    if http_port:
        subprocess.run('networksetup -setwebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
        subprocess.run('networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
        # subprocess.run('networksetup -setwebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
        # subprocess.run('networksetup -setsecurewebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
    if socks_port:
        subprocess.run('networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 ' + socks_port, shell=True)
        # subprocess.run('networksetup -setsocksfirewallproxy "Ethernet" 127.0.0.1 ' + socks_port,shell=True)
    subprocess.run(['networksetup', '-setproxybypassdomains', 'Wi-Fi', *skip_proxy])
    # subprocess.run(['networksetup', '-setproxybypassdomains', 'Ethernet', *skip_proxy])


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
    try:
        menu = QMenu()
        # Proxy
        m_proxy = QAction("ᴘʀᴏxʏ")
        m_proxy.setCheckable(True)
        m_proxy.setDisabled(True)
        m_proxy.triggered.connect(lambda: current['proxy'].disable(m_proxy))
        menu.addAction(m_proxy)
        proxy_dict = {}
        proxy_group = QActionGroup(menu)
        for proxy in profile.get_items('Proxy'):
            proxyname = proxy[0]
            proxy_dict[proxyname] = Proxy(proxy, m_proxy)
            proxy_group.addAction(proxy_dict[proxyname].QAction)
            menu.addAction(proxy_dict[proxyname].QAction)

        # Bypass
        menu.addSeparator()
        m_bypass = QAction("ʙʏᴘᴀss")
        m_bypass.setCheckable(True)
        m_bypass.setDisabled(True)
        m_bypass.triggered.connect(lambda: current['bypass'].disable(m_bypass))
        menu.addAction(m_bypass)
        bypass_dict = {}
        bypass_group = QActionGroup(menu)
        for bypass in profile.get_items('Bypass'):
            bypassname = bypass[0]
            bypass_dict[bypassname] = Bypass(bypass, m_bypass)
            bypass_group.addAction(bypass_dict[bypassname].QAction)
            menu.addAction(bypass_dict[bypassname].QAction)

        # Capture
        menu.addSeparator()
        m_capture = QAction("ᴄᴀᴘᴛᴜʀᴇ")
        m_capture.setCheckable(True)
        m_capture.setDisabled(True)
        m_dashboard = QAction("Open Dashboard...")
        m_dashboard.setDisabled(True)
        m_capture.triggered.connect(lambda: current['capture'].disable(m_capture, m_dashboard))
        menu.addAction(m_capture)
        capture_dict = {}
        capture_group = QActionGroup(menu)
        for capture in profile.get_items('Capture'):
            capturename = capture[0]
            capture_dict[capturename] = Capture(capture, m_capture, m_dashboard)
            capture_group.addAction(capture_dict[capturename].QAction)
            menu.addAction(capture_dict[capturename].QAction)
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
        m_quit.triggered.connect(app.quit)
        menu.addAction(m_quit)

        # Add Tray
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon("icon.png"))
        tray.setVisible(True)
        tray.setContextMenu(menu)
        # sys.exit(app.exec_())
        app.exec_()
    finally:
        quitapp()


if __name__ == '__main__':
    sys.exit(main())