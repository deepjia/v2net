#!/usr/bin/env python3
#coding=utf-8
import sys
import os
import shutil
import subprocess
import json
import pyperclip
import logging
from logging.handlers import RotatingFileHandler
from jinja2 import Template
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QActionGroup, QSystemTrayIcon, QWidget, QLabel
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from v2config import Config


VERSION = '0.4.8'
APP = QApplication([])
APP.setQuitOnLastWindowClosed(False)

if getattr(sys, 'frozen', False):
    # PyInstaller Bundle
    BASE_PATH = sys._MEIPASS
    os.chdir(BASE_PATH)
    os.environ['PATH']='/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin'
else:
    # Normal Python Environment
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))
EXT_PATH = os.path.join(BASE_PATH, 'extension')
LOG_PATH = os.path.join(os.environ.get('HOME'), 'Library', 'Logs', 'V2Net')
LOG_PATH_EXT = os.path.join(LOG_PATH, 'extension_log')
# Built-in examples
PROFILE_PATH_EXAMPLE = os.path.join(BASE_PATH, 'profile')
SETTING_EXAMPLE = os.path.join(BASE_PATH, 'setting.ini')
# Application Support Folder
AS_PATH = os.path.join(os.environ.get('HOME'), 'Library', 'Application Support', 'V2Net')
if not os.path.exists(AS_PATH):
    os.mkdir(AS_PATH)
SETTING_FILE = os.path.join(AS_PATH, 'setting.ini')
# Copy example setting and confirm profile path
if not os.path.exists(SETTING_FILE):
    shutil.copy(SETTING_EXAMPLE, SETTING_FILE)
SETTING = Config(SETTING_FILE)
CUSTOM_PATH = SETTING.get('Global', 'custom-path', SETTING.get('Global', 'CustomPath', AS_PATH))
# Use Application Support Folder as Default STORAGE_PATH
STORAGE_PATH = CUSTOM_PATH if os.path.exists(CUSTOM_PATH) else AS_PATH
PROFILE_PATH = os.path.join(STORAGE_PATH, 'profile')
PROFILE_FILE = os.path.join(PROFILE_PATH, 'profile.ini')
# Copy example profiles
if not os.path.exists(PROFILE_PATH):
    shutil.copytree(PROFILE_PATH_EXAMPLE, PROFILE_PATH)
if not os.path.exists(LOG_PATH):
    os.mkdir(LOG_PATH)
shutil.rmtree(LOG_PATH_EXT, True)
os.mkdir(LOG_PATH_EXT)
MUTEX = QMutex()

# Profile
PROFILE = Config(PROFILE_FILE)
SKIP_PROXY = [x.strip() for x in PROFILE.get('General', 'skip-proxy').split(',')]
PORT = PROFILE.get('General', 'port', PROFILE.get('General', 'Port', '8014'))
PORT_PROXY = PROFILE.get('General', 'port-proxy', PROFILE.get('General', 'InnerPortProxy', '8114'))
PORT_BYPASS = PROFILE.get('General', 'port-bypass', PROFILE.get('General', 'InnerPortBypass', '8214'))
logging.basicConfig(
    level=getattr(logging, PROFILE.get('General', 'loglevel', 'INFO').upper()),
    handlers=(RotatingFileHandler(
        os.path.join(LOG_PATH, 'V2Net.log'), maxBytes=1024*1024, backupCount=5, encoding='UTF-8'),
    ),
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Profile Vars
http_port = ''
socks5_port = ''
selected = {x: PROFILE.get('General', x) for x in ('proxy', 'bypass', 'capture')}
current = {x: None for x in ('proxy', 'bypass', 'capture')}
system = True if PROFILE.get('General', 'system', 'false').strip().lower() == 'true' else False


class Extension(QThread):
    # 定义信号
    update = pyqtSignal()

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
        self.QAction.triggered.connect(self.manual_select)
        self.last = None
        self.ext_log = None

    def select(self):
        # 绑定信号的动作
        def update():
            # update current
            current[self.role] = self
            self.menus_to_enable[0].setText(self.role.title() + ": " + self.local_port)
            if self.local_port == PORT:
                global http_port, socks5_port
                http_port = self.local_port if self.http else ''
                socks5_port = self.local_port if self.socks5 else ''
            # set proxy
            if system:
                setproxy()
            PROFILE.write('General', self.role, self.name)
            # 设置菜单选中状态
            self.QAction.setChecked(True)
            self.menus_to_enable[0].setChecked(True)
            self.menus_to_enable[0].setDisabled(False)
            for menu_to_enable in self.menus_to_enable[1:]:
                if self.url:
                    menu_to_enable.setDisabled(False)
                else:
                    menu_to_enable.setDisabled(True)

        self.update.connect(update)
        # 在新线程中启动组件
        self.last = current[self.role]
        current[self.role] = self
        self.start()

    def manual_select(self):
        self.select()
        self.reset_downstream()

    def reset_downstream(self):
        for role in ('capture', 'bypass', 'proxy'):
            if role == self.role:
                break
            if current[role]:
                current[role].select()
                break

    def reset_upstream(self):
        begin = False
        for role in ('capture', 'bypass', 'proxy'):
            if role == self.role:
                begin = True
                continue
            if begin and current[role]:
                current[role].select()
                break

    def run(self):
        MUTEX.lock()
        logging.debug('[' + self.ext_name + ']' + self.name + ' get Lock.')
        # 关闭已启动的同类组件
        if self.last:
            #self.last.stop_and_reset()
            self.last.stop()
            self.last.reset_upstream()
            self.last = None
        # 读取配置文件，获得 json 字符串
        try:
            ext_dir = os.path.join(EXT_PATH, self.ext_name)
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
            self.jinja_dict['ProfileDir'] = PROFILE_PATH
            self.jinja_dict['HomeDir'] = os.environ.get('HOME')
            # 确定 Local Port
            self.local_port = PORT
            begin = False
            for role in ('proxy', 'bypass', 'capture'):
                if role == self.role:
                    begin = True
                    continue
                if begin and current[role]:
                    self.local_port = PORT_PROXY if self.role == 'proxy' else PORT_BYPASS
                    break

            # 确定 Server Port 和 Protocol
            server_port = self.jinja_dict.get('ServerPort')
            begin = False
            for role in ('capture', 'bypass', 'proxy'):
                if role == self.role:
                    begin = True
                    continue
                if begin and current[role]:
                    logging.info('[' + self.ext_name + ']' + self.name + "Will stop pid=" + str(
                        current[role].process.pid if current[role].process else None))
                    # current[role].stop_and_reset()
                    current[role].stop()
                    current[role].reset_upstream()
                    current[role].start()
                    if not server_port:
                        if role == 'proxy':
                            # 上级代理默认为 socks5
                            if not self.jinja_dict.get('ServerProtocol'):
                                self.jinja_dict['ServerProtocolSocks5'] = current[role].socks5
                                self.jinja_dict['ServerProtocolHttp'] = current[role].http
                                self.jinja_dict['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                            server_port = PORT_PROXY
                        else:
                            if not self.jinja_dict.get('ServerProtocol'):
                                self.jinja_dict['ServerProtocolSocks5'] = current[role].socks5
                                self.jinja_dict['ServerProtocolHttp'] = current[role].http
                                self.jinja_dict['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                            server_port = PORT_BYPASS
                        self.jinja_dict['ServerPort'] = server_port

            logging.info(
                '[' + self.ext_name + ']' + self.name + " Local Prot" + self.local_port)
            logging.info(
                '[' + self.ext_name + ']' + self.name + " Server Prot" + str(server_port))
            # jinja2 渲染参数
            self.jinja_dict['ExtensionPort'] = self.local_port
            json_dict = json.loads(Template(json_str).render(**self.jinja_dict))
            self.bin = json_dict['bin']
            render = json_dict['render']
            self.url = json_dict.get('url')
            args = json_dict.get('args', '')
            pre = json_dict.get('pre')
            self.kill = json_dict.get('kill')
            self.exitargs = json_dict.get('exitargs')
            for src, dist in render.items():
                with open(src, 'r') as f:
                    content = Template(f.read()).render(**self.jinja_dict)
                with open(dist, 'r+') as f:
                    if content != Template(f.read()).render(**self.jinja_dict):
                        f.seek(0)
                        f.write(content)
                        f.truncate()
            # 启动子进程
            self.ext_log = open(os.path.join(LOG_PATH_EXT, self.name + '.log'), 'a', encoding='UTF-8')
            if pre:
                subprocess.run(pre, shell=True, check=True,
                               stdout=self.ext_log, stderr=subprocess.STDOUT)
            self.process = subprocess.Popen(self.bin + ' ' + args, shell=True,
                                            stdout=self.ext_log, stderr=subprocess.STDOUT)
            logging.info('[' + self.ext_name + ']' + self.name + " started, pid=" + str(
                self.process.pid if self.process else None))
            self.update.emit()
        except Exception as e:
            logging.error(
                '[' + self.ext_name + ']' + self.name + " start failed. Error: " + str(e))
        finally:
            logging.debug(
                '[' + self.ext_name + ']' + self.name + " release Lock.")
            MUTEX.unlock()

    def stop(self):
        logging.info('[' + self.ext_name + ']' + self.name + " is going to stop. pid=" + str(
            self.process.pid if self.process else None))
        # 调用停止命令
        try:
            if self.exitargs:
                subprocess.run(self.bin + ' ' + self.exitargs, shell=True, check=True,
                               stdout=self.ext_log, stderr=subprocess.STDOUT)
            # 结束启动进程
            if self.process.returncode is None:
                self.process.terminate()
                self.process.wait()
            if self.kill:
                subprocess.run(self.kill, shell=True,
                               stdout=self.ext_log, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            logging.error(
                '[' + self.ext_name + ']' + self.name + " stop failed. Error: " + str(e))
        finally:
            try:
                self.ext_log.close()
            finally:
                if system:
                    setproxy()

    #def stop_and_reset(self):
        #self.stop()

    def disable(self, *menus_to_disable):
        for menu_to_disable in menus_to_disable:
            menu_to_disable.setDisabled(True)
        menus_to_disable[0].setText(self.role.title() + ": Disabled")
        self.QAction.setChecked(False)
        self.stop()
        self.reset_upstream()
        #self.stop_and_reset()
        current[self.role] = None
        self.reset_downstream()


class Proxy(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'proxy'
        # 自动启动上次启动的扩展
        if self.name == selected['proxy']:
            self.select()

    def disable(self, *args):
        super().disable(*args)
        PROFILE.write('General', 'proxy', '')


class Bypass(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'bypass'
        # 自动启动上次启动的扩展
        if self.name == selected['bypass']:
            self.select()

    #def stop_and_reset(self):
        #super().stop()
        #if current['proxy']:
            #current['proxy'].select()

    def disable(self, *args):
        super().disable(*args)
        PROFILE.write('General', 'bypass', '')


class Capture(Extension):
    def __init__(self, *args):
        super().__init__(*args)
        self.role = 'capture'
        # 自动启动上次启动的扩展
        if self.name == selected['capture']:
            self.select()

    def select(self):
        super().select()
        self.menus_to_enable[1].triggered.connect(lambda: show_dashboard(self.url))
        #self.menus_to_enable[1].triggered.connect(
        #    lambda: WINDOW.show_dashboard(self.ext_name.title(), self.url))

    #def stop_and_reset(self):
    #    super().stop()
    #    if current['bypass']:
    #        current['bypass'].select()

    def disable(self, *args):
        super().disable(*args)
        PROFILE.write('General', 'capture', '')


def quitapp(code=0):
    logging.info("Quiting App...")
    for ins in filter(None, current.values()):
        ins.stop()
    if system:
        unset_http_proxy()
        unset_socks5_proxy()
    logging.info("Bye")
    APP.exit(code)


def show_dashboard(url):
    subprocess.Popen('open -a Safari ' + url, shell=True)

def setproxy_menu(qaction):
    global system
    if qaction.isChecked():
        system = True
        setproxy()
        PROFILE.write('General', 'system', 'true')
    else:
        system = False
        setproxy()
        PROFILE.write('General', 'system', 'false')


def setproxy():
    if system:
        logging.info('Setting proxy bypass...')
        subprocess.Popen(['bash', 'setproxy.sh', *SKIP_PROXY])
        subprocess.Popen(['networksetup', '-setproxybypassdomains', 'Wi-Fi', *SKIP_PROXY])
    if system and http_port:
        logging.info('Setting http proxy...')
        subprocess.Popen(['bash', 'setproxy.sh', 'httpon', http_port])
        subprocess.Popen('networksetup -setwebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
        subprocess.Popen('networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True)
    else:
        unset_http_proxy()
    if system and socks5_port:
        logging.info('Setting socks5 proxy...')
        subprocess.Popen(['bash', 'setproxy.sh', 'socks5on', socks5_port])
        subprocess.Popen('networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 ' + socks5_port, shell=True)
    else:
        unset_socks5_proxy()

def unset_http_proxy():
    logging.info('Unsetting http proxy...')
    subprocess.Popen(['bash', 'setproxy.sh', 'httpoff'])
    subprocess.Popen('networksetup -setwebproxystate "Wi-Fi" off', shell=True)
    subprocess.Popen('networksetup -setsecurewebproxystate "Wi-Fi" off', shell=True)

def unset_socks5_proxy():
    logging.info('Unsetting socks5 proxy...')
    subprocess.Popen(['bash', 'setproxy.sh', 'socks5off'])
    subprocess.Popen('networksetup -setsocksfirewallproxystate "Wi-Fi" off', shell=True)

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
        # Add Tray
        tray = QSystemTrayIcon()
        tray.setIcon(QIcon(os.path.join(BASE_PATH, "icon.png")))
        tray.setVisible(True)
        tray.setContextMenu(menu)
        # Proxy
        m_proxy = QAction("Proxy: Disabled")
        m_proxy.setShortcut('Ctrl+P')
        m_proxy.setCheckable(True)
        m_proxy.setDisabled(True)
        m_proxy.triggered.connect(lambda: current['proxy'].disable(m_proxy))
        menu.addAction(m_proxy)
        proxy_dict = {}
        proxy_group = QActionGroup(menu)
        for proxy in PROFILE.get_items('Proxy'):
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
        for bypass in PROFILE.get_items('Bypass'):
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
        for capture in PROFILE.get_items('Capture'):
            capturename = capture[0]
            capture_dict[capturename] = Capture(capture, m_capture, m_dashboard)
            capture_group.addAction(capture_dict[capturename].QAction)
            menu.addAction(capture_dict[capturename].QAction)
        menu.addAction(m_dashboard)

        # Common
        m_setting = QAction("Open Setting File")
        m_setting.setShortcut('Ctrl+O')
        m_setting.triggered.connect(lambda: subprocess.run(["open", SETTING_FILE]))
        m_profile = QAction("Open Profile Folder")
        m_profile.setShortcut('Ctrl+P')
        m_profile.triggered.connect(lambda: subprocess.run(["open", PROFILE_PATH]))
        m_log = QAction("Open Log Folder")
        m_log.setShortcut('Ctrl+L')
        m_log.triggered.connect(lambda: subprocess.run(["open", LOG_PATH]))
        m_extension = QAction("Open Extension Folder")
        m_extension.setShortcut('Ctrl+E')
        m_extension.triggered.connect(lambda: subprocess.run(["open", EXT_PATH]))
        m_copy_shell = QAction("Copy Shell Command")
        m_copy_shell.setShortcut('Ctrl+S')
        m_set_system = QAction("As System Proxy: " + PORT)
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
        menu.addAction(m_setting)
        menu.addAction(m_profile)
        menu.addAction(m_log)
        menu.addAction(m_extension)
        menu.addAction(m_copy_shell)
        menu.addSeparator()
        m_update = QAction("Check Update")
        m_update.setShortcut("Ctrl+U")
        m_update.triggered.connect(lambda: show_dashboard("https://github.com/deepjia/v2net/releases"))
        m_quit = QAction('Quit V2Net (' + VERSION + ')')
        m_quit.setShortcut('Ctrl+Q')
        m_quit.triggered.connect(APP.quit)
        menu.addAction(m_update)
        menu.addAction(m_quit)
        # sys.exit(app.exec_())
        exitcode = APP.exec_()
    finally:
        quitapp(exitcode)


if __name__ == '__main__':
    sys.exit(main())
