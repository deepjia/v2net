#!/usr/bin/env python3
# coding=utf-8
import sys
import os
import shutil
import subprocess
import yaml
import pyperclip
import logging
import threading
from logging.handlers import RotatingFileHandler
from jinja2 import Template
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMenu, QAction, QActionGroup, QSystemTrayIcon, QWidget, QMessageBox
from PyQt5.QtCore import QThread, QMutex, pyqtSignal
from v2config import Config

VERSION = '0.6.2'
APP = QApplication([])
APP.setQuitOnLastWindowClosed(False)
if getattr(sys, 'frozen', False):
    # PyInstaller Bundle
    BASE_PATH = sys._MEIPASS
    os.chdir(BASE_PATH)
    ENV_PATH = '/usr/local/bin:/usr/local/sbin:/usr/bin:/bin:/usr/sbin:/sbin'
else:
    # Normal Python Environment
    BASE_PATH = os.path.dirname(os.path.realpath(__file__))
    ENV_PATH = os.environ['PATH']

EXT_PATH = os.path.join(BASE_PATH, 'extension')
LOG_PATH = os.path.join(os.environ.get('HOME'), 'Library', 'Logs', 'V2Net')
os.mkdir(LOG_PATH) if not os.path.exists(LOG_PATH) else None
LOG_PATH_EXT = os.path.join(LOG_PATH, 'extension_log')
shutil.rmtree(LOG_PATH_EXT, True)
os.mkdir(LOG_PATH_EXT)
MUTEX = QMutex()
LOCK = threading.Lock()

# Create and read setting
SETTING_PATH = os.path.join(os.environ.get('HOME'), 'Library', 'Application Support', 'V2Net')
TEMP_PATH = os.path.join(SETTING_PATH, 'temp')
os.mkdir(SETTING_PATH) if not os.path.exists(SETTING_PATH) else None
shutil.rmtree(TEMP_PATH, True)
os.mkdir(TEMP_PATH)
SETTING_FILE = os.path.join(SETTING_PATH, 'setting.ini')
SETTING_EXAMPLE = os.path.join(BASE_PATH, 'setting.ini')
shutil.copy(SETTING_EXAMPLE, SETTING_FILE) if not os.path.exists(SETTING_FILE) else None
SETTING = Config(SETTING_FILE)
CUSTOM_PATH = SETTING.get('Global', 'custom-path', SETTING.get('Global', 'CustomPath', SETTING_PATH))
os.environ['PATH'] = SETTING.get('Global', 'env-path', ENV_PATH)
PORT = SETTING.get('Global', 'port', '8014')
PORT_PROXY = SETTING.get('Global', 'port-proxy', '8114')
PORT_BYPASS = SETTING.get('Global', 'port-bypass', '8214')

# Create and read profile
STORAGE_PATH = CUSTOM_PATH if os.path.exists(CUSTOM_PATH) else SETTING_PATH
PROFILE_PATH = os.path.join(STORAGE_PATH, 'profile')
PROFILE_FILE = os.path.join(PROFILE_PATH, 'profile.ini')
PROFILE_PATH_EXAMPLE = os.path.join(BASE_PATH, 'profile')
shutil.copytree(PROFILE_PATH_EXAMPLE, PROFILE_PATH) if not os.path.exists(PROFILE_PATH) else None
PROFILE = Config(PROFILE_FILE)
logging.basicConfig(
    level=getattr(logging, PROFILE.get('General', 'loglevel', 'INFO').upper()),
    handlers=(RotatingFileHandler(
        os.path.join(LOG_PATH, 'V2Net.log'), maxBytes=1024*1024, backupCount=5, encoding='UTF-8'),
    ),
    format='%(asctime)s %(levelname)s: %(message)s'
)
SKIP_PROXY = [x.strip() for x in PROFILE.get('General', 'skip-proxy').split(',')]

# Global vars
selected = {x: SETTING.get('Global', x) for x in ('proxy', 'bypass', 'capture')}
system = SETTING.get('Global', 'system', 'false').strip().lower() == 'true'
http_port = ''
socks5_port = ''
current = {x: None for x in ('proxy', 'bypass', 'capture')}


class Extension(QThread):
    # define signal
    update = pyqtSignal()
    critical = pyqtSignal(str)

    def __init__(self, item, role, *menus):
        super().__init__()
        self.role = role
        self.kv = None
        self.http = None
        self.socks5 = None
        self.local_port = ''
        self.bin = None
        self.url = None
        self.pre = None
        self.exitargs = None
        self.kill = None
        self.process = None
        self.menus = menus
        self.ext_name, *self.values = [x.strip() for x in item[1].split(',')]
        self.name = item[0]
        self.QAction = QAction(self.name)
        self.QAction.setCheckable(True)
        self.QAction.triggered.connect(lambda :self.select(manual=True))
        self.last = None
        self.ext_log = None
        self.msg = None

    def select(self, manual=False):
        logging.info(self.name + " selected.")
        # bind action to signal
        def update():
            try:
                # update current
                current[self.role] = self
                self.menus[0].setText(self.role.title() + ": " + self.local_port)
                if self.local_port == PORT:
                    global http_port, socks5_port
                    http_port = self.local_port if self.http else ''
                    socks5_port = self.local_port if self.socks5 else ''
                # set proxy
                if system and self.local_port == PORT:
                    # set_proxy()
                    logging.debug('[' + self.ext_name + ']' + self.name + ' update proxy.')
                    threading.Thread(target=set_proxy).start()
                SETTING.write('Global', self.role, self.name)
                # set menu as checked
                self.QAction.setChecked(True)
                self.menus[0].setChecked(True)
                self.menus[0].setDisabled(False)
                if len(self.menus)>1:
                    if self.url:
                        #self.menus[1].triggered.disconnect()
                        self.menus[1].triggered.connect(lambda: show_url(self.url))
                        # self.menus[1].triggered.connect(lambda: WINDOW.show_dashboard(self.ext_name.title(), self.url))
                        self.menus[1].setDisabled(False)
                    else:
                        self.menus[1].setDisabled(True)
                if manual:
                    logging.debug(
                        '[' + self.ext_name + ']' + self.name + " is going to reset downstream proxy.")
                    self.reset_downstream()
            finally:
                self.update.disconnect(update)

        def critical(msg):
            if not self.msg:
                self.msg = msg
                QMessageBox.critical(QWidget(), 'Critical', self.name + ": " + msg)
            self.disable()
            self.critical.disconnect(critical)

        # start extension in new thread
        self.last = current[self.role]
        current[self.role] = self
        if manual:
            logging.debug(
                '[' + self.ext_name + ']' + self.name + " is going to reset upstream proxy.")
            self.reset_upstream()
        self.update.connect(update)
        self.critical.connect(critical)
        if self.last and not self.last.isFinished():
            logging.debug(
                '[' + self.last.ext_name + ']' + self.last.name + " is going to exit.")
            self.last.exit()
            self.last.wait()
        self.start()

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
        try:
            logging.debug('[' + self.ext_name + ']' + self.name + ' get Lock.')
            # stop extension of the same type
            if self.last:
                self.last.stop()
                # self.last.reset_upstream()
                self.last = None
            # 读取配置文件，获得 yaml 字符串
            ext_dir = os.path.join(EXT_PATH, self.ext_name)
            ext_file = os.path.join(ext_dir, 'extension.yaml')
            if not os.path.exists(ext_file):
                ext_file = os.path.join(ext_dir, 'extension.json')
            with open(ext_file, 'r') as f:
                yaml_str = f.read()
                param_temp = yaml.load(yaml_str)
            # 从临时的 yaml 词典中提取关键数据
            default = param_temp.get('default', dict())
            keys = param_temp.get('keys', list())
            self.http = param_temp.get('http', False)
            self.socks5 = param_temp.get('socks5', False)
            # 使用关键数据，渲染 yaml 字符串，然后重新提取 yaml 词典
            self.kv = dict(default, **dict(filter(lambda x: x[1], zip(keys, self.values))))
            self.kv['ExtensionDir'] = ext_dir
            self.kv['ProfileDir'] = PROFILE_PATH
            self.kv['HomeDir'] = os.environ.get('HOME')
            temp_dir = os.path.join(TEMP_PATH, self.role)
            self.kv['TempDir'] = temp_dir
            os.mkdir(temp_dir) if not os.path.exists(temp_dir) else None
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
            server_port = self.kv.get('ServerPort')
            begin = False
            for role in ('capture', 'bypass', 'proxy'):
                if role == self.role:
                    begin = True
                    continue
                if begin and current[role]:
                    if not server_port:
                        if role == 'proxy':
                            # 上级代理默认为 socks5
                            if not self.kv.get('ServerProtocol'):
                                self.kv['ServerProtocolSocks5'] = current[role].socks5
                                self.kv['ServerProtocolHttp'] = current[role].http
                                self.kv['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                            server_port = PORT_PROXY
                        else:
                            if not self.kv.get('ServerProtocol'):
                                self.kv['ServerProtocolSocks5'] = current[role].socks5
                                self.kv['ServerProtocolHttp'] = current[role].http
                                self.kv['ServerProtocol'] = 'socks5' if current[role].socks5 else 'http'
                            server_port = PORT_BYPASS
                        self.kv['ServerPort'] = server_port
                    break

            logging.info(
                '[' + self.ext_name + ']' + self.name + " Local Prot: " + self.local_port)
            logging.info(
                '[' + self.ext_name + ']' + self.name + " Server Prot: " + str(server_port))
            # jinja2 渲染参数
            self.kv['ExtensionPort'] = self.local_port
            param = yaml.load(Template(yaml_str).render(**self.kv))
            self.bin = param['bin']
            render = param.get('render', dict())
            self.url = param.get('url')
            args = param.get('args', '')
            # arglist = param.get('arglist')
            pre = param.get('pre')
            self.kill = param.get('kill')
            self.exitargs = param.get('exitargs')
            for src, dist in render.items():
                with open(src, 'r') as f:
                    content = Template(f.read()).render(**self.kv)
                with open(dist, 'w') as f:
                    f.write(content)
            # 启动子进程
            self.ext_log = open(os.path.join(LOG_PATH_EXT, self.name + '.log'), 'a', encoding='UTF-8')
            if pre:
                subprocess.run(pre, shell=True, check=True,
                               stdout=self.ext_log, stderr=subprocess.STDOUT)
            self.process = subprocess.Popen(self.bin + ' ' + args, shell=True,
                                            stdout=self.ext_log, stderr=subprocess.STDOUT)
            logging.info('[' + self.ext_name + ']' + self.name + " started, pid=" + str(
                self.process.pid if self.process else None))
            logging.debug("EMIT: " + self.name + ', pid=' + str(self.process.pid))
            self.update.emit()
        except Exception as e:
            logging.error(
                '[' + self.ext_name + ']' + self.name + " start failed. Error: " + str(e))
            self.critical.emit(repr(e))
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
        except Exception as e:
            logging.error(
                '[' + self.ext_name + ']' + self.name + " stop failed. Error: " + str(e))
        finally:
            if self.ext_log:
                self.ext_log.close()

    def disable(self):
        for menu_to_disable in self.menus:
            menu_to_disable.setDisabled(True)
        self.menus[0].setText(self.role.title() + ": Disabled")
        self.QAction.setChecked(False)
        stop_thread = threading.Thread(target=self.stop)
        stop_thread.start()
        stop_thread.join()
        current[self.role] = None
        self.reset_upstream()
        self.reset_downstream()
        SETTING.write('Global', self.role, '')
        if system:
            threading.Thread(target=set_proxy).start()


def quit_app(code=0):
    logging.info("Quiting App...")
    for ins in filter(None, current.values()):
        # ins.stop()
        stop_thread = threading.Thread(target=ins.stop)
        stop_thread.start()
        stop_thread.join()
    if system:
        unset_http_proxy()
        unset_socks5_proxy()
    logging.info("Good Bye! 👋")
    APP.exit(code)


def show_url(url):
    subprocess.Popen('open -a Safari ' + url, shell=True)


def set_proxy_menu(q_action):
    global system
    if q_action.isChecked():
        system = True
        # set_proxy()
        threading.Thread(target=set_proxy).start()
        SETTING.write('Global', 'system', 'true')
    else:
        system = False
        # set_proxy()
        threading.Thread(target=set_proxy).start()
        SETTING.write('Global', 'system', 'false')


def set_proxy():
    LOCK.acquire()
    try:
        if system:
            logging.info('Setting proxy bypass...')
            subprocess.Popen(['bash', 'setproxy.sh', *SKIP_PROXY]).wait()
            subprocess.Popen(['networksetup', '-setproxybypassdomains', 'Wi-Fi', *SKIP_PROXY]).wait()
        if system and http_port:
            logging.info('Setting http proxy...')
            subprocess.Popen(['bash', 'setproxy.sh', 'httpon', http_port]).wait()
            subprocess.Popen('networksetup -setwebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True).wait()
            subprocess.Popen('networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 ' + http_port, shell=True).wait()
        else:
            unset_http_proxy()
        if system and socks5_port:
            logging.info('Setting socks5 proxy...')
            subprocess.Popen(['bash', 'setproxy.sh', 'socks5on', socks5_port]).wait()
            subprocess.Popen('networksetup -setsocksfirewallproxy "Wi-Fi" 127.0.0.1 ' + socks5_port, shell=True).wait()
        else:
            unset_socks5_proxy()
    except Exception as e:
        logging.error('Setting proxy failed: ' + str(e))
    finally:
        LOCK.release()


def unset_http_proxy():
    logging.info('Unsetting http proxy...')
    subprocess.Popen(['bash', 'setproxy.sh', 'httpoff']).wait()
    subprocess.Popen('networksetup -setwebproxystate "Wi-Fi" off', shell=True).wait()
    subprocess.Popen('networksetup -setsecurewebproxystate "Wi-Fi" off', shell=True).wait()


def unset_socks5_proxy():
    logging.info('Unsetting socks5 proxy...')
    subprocess.Popen(['bash', 'setproxy.sh', 'socks5off']).wait()
    subprocess.Popen('networksetup -setsocksfirewallproxystate "Wi-Fi" off', shell=True).wait()


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
    logging.info("Hello! 👋")
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
        m_proxy.triggered.connect(lambda: current['proxy'].disable())
        menu.addAction(m_proxy)
        proxy_group = QActionGroup(menu)
        for item in PROFILE.get_items('Proxy'):
            proxy = Extension(item, 'proxy', m_proxy)
            proxy_group.addAction(proxy.QAction)
            menu.addAction(proxy.QAction)
            if item[0] == selected['proxy']:
                proxy.select(manual=True)

        # Bypass
        menu.addSeparator()
        m_bypass = QAction("Bypass: Disabled")
        m_bypass.setShortcut('Ctrl+B')
        m_bypass.setCheckable(True)
        m_bypass.setDisabled(True)
        m_bypass.triggered.connect(lambda: current['bypass'].disable())
        menu.addAction(m_bypass)
        bypass_group = QActionGroup(menu)
        for item in PROFILE.get_items('Bypass'):
            bypass = Extension(item, 'bypass', m_bypass)
            bypass_group.addAction(bypass.QAction)
            menu.addAction(bypass.QAction)
            if item[0] == selected['bypass']:
                bypass.select(manual=True)

        # Capture
        menu.addSeparator()
        m_capture = QAction("Capture: Disabled")
        m_capture.setShortcut('Ctrl+C')
        m_capture.setCheckable(True)
        m_capture.setDisabled(True)
        m_dashboard = QAction("Open Dashboard...")
        m_dashboard.setShortcut('Ctrl+D')
        m_dashboard.setDisabled(True)
        m_capture.triggered.connect(lambda: current['capture'].disable())
        menu.addAction(m_capture)
        capture_group = QActionGroup(menu)
        for item in PROFILE.get_items('Capture'):
            capture = Extension(item, 'capture', m_capture, m_dashboard)
            capture_group.addAction(capture.QAction)
            menu.addAction(capture.QAction)
            if item[0] == selected['capture']:
                capture.select(manual=True)
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
        m_set_system.triggered.connect(lambda: set_proxy_menu(m_set_system))
        m_copy_shell.triggered.connect(copy_shell)
        m_set_system.setCheckable(True)
        if system:
            m_set_system.setChecked(True)
            # set_proxy()
            threading.Thread(target=set_proxy).start()
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
        m_update.triggered.connect(lambda: show_url("https://github.com/deepjia/v2net/releases"))
        m_quit = QAction('Quit V2Net (' + VERSION + ')')
        m_quit.setShortcut('Ctrl+Q')
        m_quit.triggered.connect(APP.quit)
        menu.addAction(m_update)
        menu.addAction(m_quit)
        # sys.exit(app.exec_())
        exitcode = APP.exec_()
    finally:
        quit_app(exitcode)


if __name__ == '__main__':
    sys.exit(main())
