#!/usr/bin/env python3
import sys
import os
import shutil
import subprocess
import json
import pyperclip
import logging
from jinja2 import Template
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QAction, QActionGroup, QSystemTrayIcon
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from v2config import Config
from v2widget import APP, WINDOW
version = '0.2.4'
base_path = os.path.dirname(os.path.realpath(__file__))
ext_path = os.path.join(base_path, 'extension')
profile_path = os.path.join(base_path, 'profile')
profile = Config(os.path.join(profile_path, 'profile.ini'))
skip_proxy = [x.strip() for x in profile.get('General', 'skip-proxy').split(',')]
http_port = ''
socks5_port = ''
user_port = profile.get('General', 'Port', '8014')
user_inner_port_proxy = profile.get('General', 'InnerPortProxy', '8114')
user_inner_port_bypass = profile.get('General', 'InnerPortBypass', '8214')
selected = {x: profile.get('General', x) for x in ('proxy', 'bypass', 'capture')}
current = {x: None for x in ('proxy', 'bypass', 'capture')}
system = True if profile.get('General', 'system', 'false').strip().lower() == 'true' else False
mutex = QMutex()
log_path = os.path.join(base_path, 'log')
shutil.rmtree(log_path, True)
os.mkdir(log_path)
logging.basicConfig(
    level=getattr(logging, profile.get('General', 'loglevel', 'INFO').upper()),
    handlers=(logging.FileHandler(
        os.path.join(log_path, 'V2Net.log'), encoding='UTF-8'),),
    format='%(asctime)s %(levelname)s: %(message)s'
)


class Extension(QThread):
    # 定义信号
    update_port = pyqtSignal()

    def __init__(self, extension, *menus_to_enable):
        super().__init__()
        self.role = None
        self.jinja_dict = None
        self.http = None
        self.socks5 = None
        self.local_port = ''
        self.bin = None
        self.url = None
        self.pre = None
        self.exitargs = None
        self.process = None
        self.menus_to_enable = menus_to_enable
        self.ext_name, *self.values = [x.strip() for x in extension[1].split(',')]
        self.name = extension[0]
        self.QAction = QAction(self.name)
        self.QAction.setCheckable(True)
        self.QAction.triggered.connect(self.select)
        self.last = None
        self.ext_log = None

    def select(self):
        # 设置菜单选中状态
        self.QAction.setChecked(True)
        for menu_to_enable in self.menus_to_enable:
            menu_to_enable.setChecked(True)
            menu_to_enable.setDisabled(False)

        # 绑定信号的动作
        def update_port():
            current[self.role] = self
            self.menus_to_enable[0].setText(self.role.title() + ": " + self.local_port)
            if self.local_port == user_port:
                global http_port, socks5_port
                http_port = self.local_port if self.http else ''
                socks5_port = self.local_port if self.socks5 else ''

        self.update_port.connect(update_port)
        # 在新线程中启动组件
        self.last = current[self.role]
        current[self.role] = self
        self.start()

    def run(self):
        mutex.lock()
        logging.debug('[' + self.ext_name + ']' + self.name + ' get Lock.')
        # 关闭已启动的同类组件
        if self.last:
            self.last.stop_and_reset()
            self.last = None
        # 读取配置文件，获得 json 字符串
        ext_dir = os.path.join(ext_path, self.ext_name)
        with open(os.path.join(ext_dir, 'extension.json'), 'r') as f:
            json_str = f.read()
            json_temp = json.loads(json_str)
        # 从临时的 json 词典中提取关键数据
        default = json_temp['default']
        keys = json_temp['keys']
        self.http = json_temp['http']
        self.socks5 = json_temp['socks5']
        # 使用关键数据，渲染 json 字符串，然后重新提取 json 词典
        self.jinja_dict = dict(default, **dict(filter(lambda x: x[1], zip(keys, self.values))))
        self.jinja_dict['ExtensionDir'] = ext_dir
        # 确定 Local Port
        self.local_port = user_port
        begin = False
        for role in ('proxy', 'bypass', 'capture'):
            if role == self.role:
                begin = True
                continue
            if begin and current[role]:
                self.local_port = user_inner_port_proxy if self.role == 'proxy' else user_inner_port_bypass
                break

        # 确定 Server Port 和 Protocol
        server_port = ''
        begin = False
        for role in ('capture', 'bypass', 'proxy'):
            if role == self.role:
                begin = True
                continue
            if begin and current[role]:
                logging.info(
                    '[' + self.ext_name + ']' + self.name + "Will stop pid=" + str(current[role].process.pid))
                current[role].stop_and_reset()
                current[role].start()
                if not server_port:
                    if role == 'proxy':
                        # 上级代理默认为 socks5
                        if not self.jinja_dict.get('ServerProtocol'):
                            self.jinja_dict['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                        server_port = user_inner_port_proxy
                    else:
                        if not self.jinja_dict.get('ServerProtocol'):
                            self.jinja_dict['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                        server_port = user_inner_port_bypass
                    self.jinja_dict['ServerPort'] = server_port

        logging.info(
            '[' + self.ext_name + ']' + self.name + " Local Prot" + self.local_port)
        logging.info(
            '[' + self.ext_name + ']' + self.name + " Server Prot" + server_port)
        # jinja2 渲染参数
        self.jinja_dict['ExtensionPort'] = self.local_port
        json_dict = json.loads(Template(json_str).render(**self.jinja_dict))
        self.bin = json_dict['bin']
        render = json_dict['render']
        self.url = json_dict.get('url')
        args = json_dict.get('args', '')
        pre = json_dict.get('pre')
        self.exitargs = json_dict.get('exitargs')
        for src, dist in render.items():
            with open(os.path.join(ext_dir, src), 'r') as f:
                content = Template(f.read()).render(**self.jinja_dict)
            with open(os.path.join(ext_dir, dist), 'r+') as f:
                if content != Template(f.read()).render(**self.jinja_dict):
                    f.seek(0)
                    f.write(content)
                    f.truncate()
        # 启动子进程
        self.ext_log = open(os.path.join(log_path, self.name + '.log'), 'a', encoding='UTF-8')
        if pre:
            subprocess.run(pre, shell=True, check=True,
                           stdout=self.ext_log, stderr=subprocess.PIPE)
        self.process = subprocess.Popen(self.bin + ' ' + args, shell=True,
                                        stdout=self.ext_log, stderr=subprocess.PIPE)
        logging.info(
            '[' + self.ext_name + ']' + self.name + " started, pid=" + str(self.process.pid))
        self.update_port.emit()
        if system:
            setproxy()
        profile.write('General', self.role, self.name)
        logging.debug(
            '[' + self.ext_name + ']' + self.name + " release Lock.")
        mutex.unlock()

    def stop(self):
        logging.info(
            '[' + self.ext_name + ']' + self.name + " is going to stop. pid=" + str(self.process.pid))
        # 调用停止命令
        if self.exitargs:
            subprocess.run(self.bin + ' ' + self.exitargs, shell=True, check=True,
                           stdout=self.ext_log, stderr=subprocess.PIPE)
        # 结束启动进程
        if self.process.returncode is None:
            self.process.terminate()
            self.process.wait()
        self.ext_log.close()
        if system:
            setproxy()

    def stop_and_reset(self):
        self.stop()

    def disable(self, *menus_to_disable):
        for menu_to_disable in menus_to_disable:
            menu_to_disable.setDisabled(True)
        menus_to_disable[0].setText(self.role.title() + ": Disabled")
        self.QAction.setChecked(False)
        self.stop_and_reset()
        current[self.role] = None


class Proxy(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'proxy'
        # 自动启动上次启动的扩展
        if self.name == selected['proxy']:
            self.select()

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'proxy', '')


class Bypass(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'bypass'
        # 自动启动上次启动的扩展
        if self.name == selected['bypass']:
            self.select()

    def stop_and_reset(self):
        super().stop()
        if current['proxy']:
            current['proxy'].select()

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'bypass', '')


class Capture(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'capture'
        # 自动启动上次启动的扩展
        if self.name == selected['capture']:
            self.select()

    def select(self):
        super().select()
        self.menus_to_enable[1].triggered.connect(
            lambda: WINDOW.show_dashboard(self.ext_name.title(), self.url))

    def stop_and_reset(self):
        super().stop()
        if current['bypass']:
            current['bypass'].select()

    def disable(self, *args):
        super().disable(*args)
        profile.write('General', 'capture', '')


def quitapp(code=0):
    logging.info("Quiting App...")
    for ins in filter(None, current.values()):
        ins.stop()
    logging.info("Bye")
    APP.exit(code)


def setproxy_menu(qaction):
    global system
    if qaction.isChecked():
        system = True
        setproxy()
        profile.write('General', 'system', 'true')
    else:
        system = False
        setproxy()
        profile.write('General', 'system', 'false')


def setproxy():
    logging.info('Unsetting system proxy...')
    subprocess.run('networksetup -setwebproxystate "Wi-Fi" off', shell=True)
    subprocess.run('networksetup -setsecurewebproxystate "Wi-Fi" off', shell=True)
    subprocess.run('networksetup -setsocksfirewallproxystate "Wi-Fi" off', shell=True)
    # subprocess.run('networksetup -setwebproxystate "Ethernet" off',shell=True)
    # subprocess.run('networksetup -setsecurewebproxystate "Ethernet" off',shell=True)
    # subprocess.run('networksetup -setsocksfirewallproxystate "Ethernet" off',shell=True)
    if system:
        logging.info('Setting system proxy...')
        if http_port:
            subprocess.run('networksetup -setwebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
            subprocess.run('networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
            # subprocess.run('networksetup -setwebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
            # subprocess.run('networksetup -setsecurewebproxy "Ethernet" 127.0.0.1 ' + http_port,shell=True)
        if socks5_port:
            subprocess.run('networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 ' + socks5_port, shell=True)
            # subprocess.run('networksetup -setsocksfirewallproxy "Ethernet" 127.0.0.1 ' + socks5_port,shell=True)
        subprocess.run(['networksetup', '-setproxybypassdomains', 'Wi-Fi', *skip_proxy])
        # subprocess.run(['networksetup', '-setproxybypassdomains', 'Ethernet', *skip_proxy])


def copy_shell():
    cmd = []
    if http_port:
        cmd.append(
            'export https_proxy=http://127.0.0.1:' + http_port + ';export http_proxy=http://127.0.0.1:' + http_port)
    else:
        cmd.append('unset https_proxy;unset http_proxy')
    if socks5_port:
        cmd.append('export all_proxy=http://127.0.0.1:' + socks5_port)
    else:
        cmd.append('unset all_proxy')
    pyperclip.copy(';'.join(cmd))


def main():
    exitcode = 0
    try:
        menu = QMenu()
        # Proxy
        m_proxy = QAction("Proxy: Disabled")
        m_proxy.setShortcut('Ctrl+P')
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
        m_bypass = QAction("Bypass: Disabled")
        m_bypass.setShortcut('Ctrl+B')
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
        m_capture = QAction("Capture: Disabled")
        m_capture.setShortcut('Ctrl+C')
        m_capture.setCheckable(True)
        m_capture.setDisabled(True)
        m_dashboard = QAction("Open Dashboard...")
        m_dashboard.setShortcut('Ctrl+D')
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
        m_log = QAction("Log Folder")
        m_log.setShortcut('Ctrl+L')
        m_log.triggered.connect(lambda: subprocess.call(["open", log_path]))
        m_profile = QAction("Profile Folder")
        m_profile.setShortcut('Ctrl+F')
        m_profile.triggered.connect(lambda: subprocess.call(["open", profile_path]))
        m_extension = QAction("Extension Folder")
        m_extension.setShortcut('Ctrl+E')
        m_extension.triggered.connect(lambda: subprocess.call(["open", ext_path]))
        m_copy_shell = QAction("Copy Shell Command")
        m_copy_shell.setShortcut('Ctrl+S')
        m_set_system = QAction("As System Proxy: " + user_port)
        m_set_system.setShortcut('Ctrl+A')
        m_set_system.triggered.connect(lambda: setproxy_menu(m_set_system))
        m_copy_shell.triggered.connect(copy_shell)
        m_set_system.setCheckable(True)
        if system:
            m_set_system.setChecked(True)
            setproxy()
        menu.addSeparator()
        menu.addAction(m_set_system)
        menu.addSeparator()
        menu.addAction(m_log)
        menu.addAction(m_profile)
        menu.addAction(m_extension)
        menu.addAction(m_copy_shell)
        menu.addSeparator()
        m_quit = QAction('Quit V2Net (' + version + ')')
        m_quit.setShortcut('Ctrl+Q')
        m_quit.triggered.connect(APP.quit)
        menu.addAction(m_quit)

        # Add Tray
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon("icon.png"))
        tray.setVisible(True)
        tray.setContextMenu(menu)
        # sys.exit(app.exec_())
        exitcode = APP.exec_()
    finally:
        quitapp(exitcode)


if __name__ == '__main__':
    sys.exit(main())
