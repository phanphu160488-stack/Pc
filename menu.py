# phedev_menu.py
# Build: pyinstaller --onefile --windowed --name "Phedev" phedev_menu.py

import os
import sys
import threading
import time
import ctypes
import winsound
import uuid
import random
import math
import json
import hashlib
from datetime import datetime
from pynput import keyboard, mouse
from colorama import init as colorama_init
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QVBoxLayout,
    QHBoxLayout, QPushButton, QFrame, QLineEdit, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect, QStackedWidget, QScrollArea, QGridLayout,
    QSlider, QCheckBox, QComboBox, QGroupBox, QTabWidget, QProgressBar,
    QSpacerItem, QSizePolicy, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import (
    pyqtSignal, pyqtSlot, QObject, Qt, QPointF, QTimer, QRectF,
    QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QPixmap, QIcon, QAction, QRadialGradient, QPalette, QFontDatabase,
    QPainterPath, QPolygonF, QImage
)
import psutil
import win32gui
import win32con
import win32process
import pydivert
import requests

colorama_init(autoreset=True)
user32 = ctypes.windll.user32

# ===== ĐƯỜNG DẪN =====
def _app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _path(f):
    return os.path.join(_app_dir(), f)

# ===== ANTIBAN SIÊU MẠNH =====
def _crack(r=''):
    ctypes.windll.user32.MessageBoxW(0, f"Crack?\n{r}", 'Anti-Crack', 16)
    ctypes.windll.kernel32.ExitProcess(1)

def check_debugger():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            _crack('Debugger')
        is_debug = ctypes.c_bool()
        ctypes.windll.kernel32.CheckRemoteDebuggerPresent(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(is_debug))
        if is_debug.value:
            _crack('Remote Debugger')
    except:
        pass

def check_vm():
    bad = ['vbox', 'vmware', 'qemu', 'hyper-v', 'virtualbox', 'parallels', 'xen', 'kvm']
    for p in psutil.process_iter(['name']):
        try:
            name = p.info['name'] or ''
            if any(b in name.lower() for b in bad):
                _crack(f'VM: {name}')
        except:
            pass

def check_monitor():
    bad = ['wireshark', 'fiddler', 'proxifier', 'charles', 'burp', 'httpanalyzer', 'netmon', 'processmonitor']
    for p in psutil.process_iter(['name']):
        try:
            name = p.info['name'] or ''
            if any(b in name.lower() for b in bad):
                _crack(f'Monitor: {name}')
        except:
            pass

def bg_anti():
    while True:
        try:
            check_debugger()
            if sys.gettrace():
                _crack('Tracer')
            check_vm()
            check_monitor()
            time.sleep(3)
        except:
            pass

# ===== LOGIC CORE =====
def key_to_str(key):
    try:
        if hasattr(key, 'char') and key.char and key.char.isprintable():
            return key.char.upper()
        raw = str(key)
        if 'KeyCode' in raw:
            if hasattr(key, 'vk') and 32 <= key.vk <= 126:
                return chr(key.vk).upper()
            if hasattr(key, 'vk'):
                return f"VK{key.vk}"
            return '??'
        raw = raw.replace('Key.', '').lower()
        mapping = {
            'ctrl_l': 'LCTRL', 'ctrl_r': 'RCTRL', 'ctrl': 'CTRL',
            'alt_l': 'LALT', 'alt_r': 'RALT', 'alt_gr': 'RALT', 'alt': 'ALT',
            'shift_l': 'LSHIFT', 'shift_r': 'RSHIFT', 'shift': 'SHIFT',
            'cmd_l': 'LWIN', 'cmd_r': 'RWIN', 'cmd': 'WIN',
            'space': 'SPACE', 'tab': 'TAB', 'enter': 'ENTER', 'return_': 'ENTER',
            'backspace': 'BKSP', 'delete': 'DEL', 'esc': 'ESC', 'escape': 'ESC',
            'up': 'UP', 'down': 'DOWN', 'left': 'LEFT', 'right': 'RIGHT',
            'home': 'HOME', 'end': 'END', 'page_up': 'PGUP', 'page_down': 'PGDN',
            'insert': 'INS', 'caps_lock': 'CAPS', 'num_lock': 'NUMLK',
            'scroll_lock': 'SCRLK', 'pause': 'PAUSE', 'print_screen': 'PRTSC',
            'menu': 'MENU',
            'f1': 'F1', 'f2': 'F2', 'f3': 'F3', 'f4': 'F4',
            'f5': 'F5', 'f6': 'F6', 'f7': 'F7', 'f8': 'F8',
            'f9': 'F9', 'f10': 'F10', 'f11': 'F11', 'f12': 'F12'
        }
        return mapping.get(raw[:8].upper(), '??')
    except:
        return '??'

def mouse_to_str(button):
    m = {
        mouse.Button.left: 'MOUSE1',
        mouse.Button.right: 'MOUSE2',
        mouse.Button.middle: 'MOUSE3',
        mouse.Button.x1: 'MOUSE4',
        mouse.Button.x2: 'MOUSE5'
    }
    return m.get(button, str(button).upper()[:8])

toggle_key = 'NONE'
stop_key = 'NONE'
filter_key = 'NONE'
aimlag_key = 'NONE'
beep_key = 'NONE'
binding_key = '5'
beep_enabled = True
_cap_lock = threading.Event()

def save_keys():
    try:
        open(_path('keybindings.txt'), 'w').write('\n'.join([
            toggle_key, stop_key, filter_key, aimlag_key, beep_key,
            binding_key, '1' if beep_enabled else '0'
        ]))
    except:
        pass

def load_keys_file():
    p = _path('keybindings.txt')
    if not os.path.exists(p):
        return False
    try:
        ls = open(p).read().splitlines()
        def g(i, d='NONE'):
            if i >= len(ls):
                return d
            v = ls[i].strip().upper()
            if v and v not in ('0', ''):
                return v
            return 'NONE'
        global toggle_key, stop_key, filter_key, aimlag_key, beep_key, binding_key, beep_enabled
        toggle_key = g(0)
        stop_key = g(1)
        filter_key = g(2)
        aimlag_key = g(3)
        beep_key = g(4)
        binding_key = g(5, '5')
        if len(ls) >= 7:
            beep_enabled = ls[6].strip() == '1'
        return True
    except:
        return False

EMULATOR_PATTERNS = [
    ('BlueStacks', 'BlueStacks'), ('BlueStacks_nxt', 'BlueStacks'),
    ('BlueStacksApp', 'BlueStacks'), ('HD-Player', ''),
    ('LDPlayer', 'LDPlayer'), ('MEmu', 'MEmu'), ('MemuConsole', ''),
    ('Nox', 'Nox'), ('NoxPlayer', 'NoxPlayer'), ('MSI', 'MSI'),
    ('MSIPlayer', 'MSI'), ('MSI App Player', 'MSI'),
    ('Qt5QWindow', ''), ('Qt5152QWindowIcon', ''),
    ('BSMainWClass', ''), ('AndroidEmulator', ''),
    ('Tencent', 'GameLoop'), ('GameLoop', 'GameLoop')
]

GAME_TITLE_KEYWORDS = [
    'pubg', 'free fire', 'mobile legends', 'bgmi', 'call of duty',
    'cod', 'arena of valor', 'aov', 'rules of survival', 'ros',
    'lien quan', 'toc chien'
]

def find_emulator():
    found = []
    def cb(h, _):
        if not win32gui.IsWindowVisible(h):
            return True
        try:
            cn = win32gui.GetClassName(h)
            t = win32gui.GetWindowText(h)
            cnl = cn.lower()
            tl = t.lower() if t else ''
            for cp, tp in EMULATOR_PATTERNS:
                cpl = cp.lower()
                tpl = tp.lower() if tp else ''
                if cpl in cnl or (tpl and tpl in tl):
                    found.append(h)
                    return True
        except:
            pass
        return True
    win32gui.EnumWindows(cb, None)
    return found[0] if found else None

def get_emulator_pid(hwnd):
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return pid
    except:
        return None

FILTER_O = 'udp.DstPort >= 10010 and udp.DstPort <= 10020 and udp.PayloadLength >= 35'
FILTER_I = '(udp.SrcPort >= 10011 and udp.SrcPort <= 10019) and ip and ip.Protocol == 17 and ip.Length >= 50 and ip.Length <= 1491'
FILTER_F = '(udp.PayloadLength >= 53 and udp.PayloadLength <= 170) and (udp.DstPort >= 10011 and udp.DstPort <= 10020)'
FILTER_AIMLAG = '(udp.SrcPort >= 10011 and udp.SrcPort <= 10019) and ip and ip.Protocol == 17 and ip.Length >= 50 and ip.Length <= 1491'

MAX_PACKETS = 1000
tele_mode = False
freeze_mode = False
ghost_mode = False
aimlag_mode = False
aimlag_active = False
mouse_held = False
R_O = False
R_I = False
R_F = False
R_A = False
W_I = None
W_F = None
packet_tele = []
packet_freeze = []
packet_ghost = []
packet_aimlag = []
lock = threading.Lock()

esp_window = None
mini_window = None
waiting_window = None
taiwan_overlay = None
center_crosshair = None
app_quit_flag = False
alive_timer = None

class Sig(QObject):
    ui = pyqtSignal(bool, bool, bool, bool)
    mini = pyqtSignal(bool, bool, bool, bool)
sig = Sig()

def _bcast():
    try:
        if esp_window and esp_window.isVisible():
            sig.ui.emit(freeze_mode, ghost_mode, tele_mode, aimlag_active)
        if mini_window and mini_window.isVisible():
            sig.mini.emit(freeze_mode, ghost_mode, tele_mode, aimlag_active)
    except:
        pass

def _beep(on):
    if not beep_enabled:
        return
    try:
        threading.Thread(target=lambda: winsound.Beep(1200 if on else 700, 80), daemon=True).start()
    except:
        pass

def send_packets(lst, f):
    if not lst:
        return
    try:
        with pydivert.WinDivert(f, layer=pydivert.Layer.NETWORK) as s:
            for pkt in lst:
                try:
                    s.send(pydivert.Packet(pkt.raw, pkt.interface, pkt.direction))
                except:
                    pass
    except:
        pass

def send_burst_packets(packets, filter_str, burst_size=15, delay_per_pkt=0.005, delay_between_burst=0.001):
    if not packets:
        return
    try:
        with pydivert.WinDivert(filter_str, layer=pydivert.Layer.NETWORK) as sender:
            total = len(packets)
            for i in range(0, total, burst_size):
                burst = packets[i:i+burst_size]
                for pkt in burst:
                    try:
                        sender.send(pydivert.Packet(pkt.raw, pkt.interface, pkt.direction))
                        time.sleep(delay_per_pkt)
                    except:
                        pass
                if i + burst_size < total:
                    time.sleep(delay_between_burst)
    except:
        send_packets(packets, filter_str)

def toggle_tele():
    global tele_mode
    try:
        if tele_mode:
            with lock:
                tele_mode = False
                to_send = list(packet_tele)
                packet_tele.clear()
            if to_send:
                threading.Thread(target=lambda: send_burst_packets(to_send, FILTER_O), daemon=True).start()
        else:
            with lock:
                tele_mode = True
                packet_tele.clear()
        _beep(tele_mode)
        _bcast()
    except:
        pass

def toggle_freeze():
    global freeze_mode, R_I, W_I
    try:
        if freeze_mode:
            freeze_mode = False
            R_I = False
            if W_I:
                try:
                    W_I.close()
                except:
                    pass
                W_I = None
            with lock:
                p = list(packet_freeze)
                packet_freeze.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_I), daemon=True).start()
        else:
            if W_I is None:
                W_I = pydivert.WinDivert(FILTER_I, layer=pydivert.Layer.NETWORK)
                W_I.open()
            freeze_mode = True
            R_I = True
        _beep(freeze_mode)
        _bcast()
    except:
        freeze_mode = False
        R_I = False

def toggle_ghost():
    global ghost_mode, R_F, W_F
    try:
        if ghost_mode:
            ghost_mode = False
            R_F = False
            if W_F:
                try:
                    W_F.close()
                except:
                    pass
                W_F = None
            with lock:
                p = list(packet_ghost)
                packet_ghost.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_F), daemon=True).start()
        else:
            if W_F is None:
                W_F = pydivert.WinDivert(FILTER_F, layer=pydivert.Layer.NETWORK)
                W_F.open()
            ghost_mode = True
            R_F = True
        _beep(ghost_mode)
        _bcast()
    except:
        ghost_mode = False
        R_F = False

def toggle_aimlag():
    global aimlag_active, aimlag_mode, mouse_held, R_A
    try:
        aimlag_active = not aimlag_active
        if not aimlag_active and mouse_held and aimlag_mode:
            aimlag_mode = False
            mouse_held = False
            R_A = False
            with lock:
                p = list(packet_aimlag)
                packet_aimlag.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_AIMLAG), daemon=True).start()
            _beep(False)
        _bcast()
    except:
        pass

def on_mouse_click(x, y, button, pressed):
    global mouse_held, aimlag_mode, R_A
    try:
        if not aimlag_active:
            return
        if button == mouse.Button.left:
            if pressed and not mouse_held:
                mouse_held = True
                aimlag_mode = True
                R_A = True
                with lock:
                    packet_aimlag.clear()
                _beep(True)
                _bcast()
            elif not pressed and mouse_held:
                mouse_held = False
                aimlag_mode = False
                R_A = False
                with lock:
                    p = list(packet_aimlag)
                    packet_aimlag.clear()
                if p:
                    threading.Thread(target=send_packets, args=(p, FILTER_AIMLAG), daemon=True).start()
                _beep(False)
                _bcast()
    except:
        pass

def stop_all():
    global R_O, R_I, R_F, R_A, tele_mode, freeze_mode, ghost_mode, aimlag_mode, mouse_held
    R_O = False
    R_I = False
    R_F = False
    R_A = False
    if tele_mode:
        tele_mode = False
        with lock:
            to_send = list(packet_tele)
            packet_tele.clear()
        if to_send:
            threading.Thread(target=lambda: send_burst_packets(to_send, FILTER_O), daemon=True).start()
    if freeze_mode:
        freeze_mode = False
        with lock:
            p = list(packet_freeze)
            packet_freeze.clear()
        if p:
            threading.Thread(target=send_packets, args=(p, FILTER_I), daemon=True).start()
    if ghost_mode:
        ghost_mode = False
        with lock:
            p = list(packet_ghost)
            packet_ghost.clear()
        if p:
            threading.Thread(target=send_packets, args=(p, FILTER_F), daemon=True).start()
    if aimlag_mode:
        aimlag_mode = False
        mouse_held = False
        with lock:
            p = list(packet_aimlag)
            packet_aimlag.clear()
        if p:
            threading.Thread(target=send_packets, args=(p, FILTER_AIMLAG), daemon=True).start()
    _bcast()

def quit_app():
    global app_quit_flag, esp_window, mini_window, waiting_window, taiwan_overlay, center_crosshair, W_I, W_F, alive_timer
    app_quit_flag = True
    stop_all()
    if alive_timer:
        try:
            alive_timer.stop()
        except:
            pass
    for win in [esp_window, mini_window, waiting_window, taiwan_overlay, center_crosshair]:
        if win:
            try:
                win.hide()
                win.close()
            except:
                pass
    if W_I:
        try:
            W_I.close()
        except:
            pass
    if W_F:
        try:
            W_F.close()
        except:
            pass
    os._exit(0)

def divert(filter_str, packet_list, cond_ref, flag_ref):
    h = None
    while not app_quit_flag:
        if not flag_ref():
            if h:
                try:
                    h.close()
                except:
                    pass
            h = None
            time.sleep(0.1)
            continue
        if h is None:
            try:
                h = pydivert.WinDivert(filter_str)
                h.open()
            except:
                time.sleep(0.1)
                continue
        try:
            for pkt in h:
                if app_quit_flag:
                    break
                if not flag_ref():
                    break
                with lock:
                    if cond_ref():
                        if len(packet_list) >= MAX_PACKETS:
                            packet_list.pop(0)
                        packet_list.append(pydivert.Packet(pkt.raw, pkt.interface, pkt.direction))
                    else:
                        h.send(pkt)
        except:
            if h:
                try:
                    h.close()
                except:
                    pass
            h = None
            time.sleep(0.1)

# ===== UI COMPONENTS =====
def F(fam, sz, bold=False):
    f = QFont(fam, sz)
    if bold:
        f.setWeight(QFont.Weight.Bold)
    return f

class StarField(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.stars = []
        self.shooting_stars = []
        self._init_stars()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(33)

    def _init_stars(self):
        for _ in range(200):
            x = random.randint(0, 800)
            y = random.randint(0, 600)
            speed = random.uniform(0.2, 1.8)
            size = random.randint(1, 4)
            self.stars.append({
                'x': x, 'y': y, 'speed': speed,
                'size': size, 'phase': random.uniform(0, 6.28),
                'trail': [], 'twinkle': random.uniform(0.5, 1.5)
            })
        for _ in range(3):
            self.shooting_stars.append({
                'active': False,
                'x': 0, 'y': 0, 'dx': 0, 'dy': 0,
                'timer': random.randint(50, 200),
                'length': random.randint(30, 80)
            })

    def _update(self):
        for star in self.stars:
            star['x'] += star['speed'] * 0.5
            star['phase'] += 0.02 * star['twinkle']
            if star['x'] > self.width():
                star['x'] = 0
                star['y'] = random.randint(0, self.height())
            star['trail'].append((star['x'], star['y']))
            if len(star['trail']) > 30:
                star['trail'].pop(0)
        for ss in self.shooting_stars:
            if ss['active']:
                ss['x'] += ss['dx']
                ss['y'] += ss['dy']
                if ss['x'] > self.width() or ss['x'] < 0 or ss['y'] > self.height() or ss['y'] < 0:
                    ss['active'] = False
                    ss['timer'] = random.randint(100, 300)
            else:
                ss['timer'] -= 1
                if ss['timer'] <= 0:
                    ss['active'] = True
                    ss['x'] = random.randint(0, self.width() // 2)
                    ss['y'] = random.randint(0, self.height() // 3)
                    angle = random.uniform(0.2, 0.8)
                    speed = random.uniform(5, 15)
                    ss['dx'] = speed * math.cos(angle)
                    ss['dy'] = speed * math.sin(angle)
                    ss['length'] = random.randint(30, 80)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        for ss in self.shooting_stars:
            if ss['active']:
                for i in range(ss['length']):
                    alpha = int(255 * (1 - i / ss['length']))
                    painter.setPen(QPen(QColor(255, 255, 255, alpha), 1))
                    painter.drawLine(
                        int(ss['x'] - ss['dx'] * i),
                        int(ss['y'] - ss['dy'] * i),
                        int(ss['x'] - ss['dx'] * (i + 1)),
                        int(ss['y'] - ss['dy'] * (i + 1))
                    )
        for star in self.stars:
            if len(star['trail']) > 1:
                for i in range(1, len(star['trail'])):
                    alpha = int(200 * (i / len(star['trail'])))
                    painter.setPen(QPen(QColor(255, 255, 255, alpha), star['size'] * 0.4))
                    painter.drawLine(
                        int(star['trail'][i-1][0]), int(star['trail'][i-1][1]),
                        int(star['trail'][i][0]), int(star['trail'][i][1])
                    )
            glow = 50 + 50 * math.sin(star['phase'])
            color = QColor(255, 255, 255, int(180 + glow))
            painter.setPen(QPen(color, star['size']))
            painter.drawPoint(int(star['x']), int(star['y']))

class NeoButton(QPushButton):
    def __init__(self, text, parent=None, glow_color='#cc0000'):
        super().__init__(text, parent)
        self.glow_color = glow_color
        self.setFixedHeight(40)
        self.setFont(F('Segoe UI', 10, True))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(0)
        self._glow.setColor(QColor(glow_color))
        self._glow.setOffset(0, 0)
        self.setGraphicsEffect(self._glow)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a0000, stop:1 #0a0000);
                border: 2px solid {glow_color};
                border-radius: 8px;
                color: #ffffff;
                letter-spacing: 2px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2a0000, stop:1 #1a0000);
                border-color: #ff2222;
            }}
            QPushButton:pressed {{
                background: #000000;
            }}
        """)

    def enterEvent(self, event):
        self._glow.setBlurRadius(20)
        self._glow.setColor(QColor(self.glow_color))
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._glow.setBlurRadius(0)
        super().leaveEvent(event)

class CardWin(QWidget):
    def __init__(self, w, h, r, has_close=True):
        super().__init__()
        self._r = r
        self._has_close = has_close
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(w, h)
        self._center()
        self._ml = QVBoxLayout(self)
        self._ml.setContentsMargins(0, 0, 0, 0)
        self._ml.setSpacing(0)

    def _center(self):
        sc = QApplication.primaryScreen().geometry()
        self.move((sc.width() - self.width()) // 2, (sc.height() - self.height()) // 2)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(10, 10, 10, 230))
        painter.drawRoundedRect(QRectF(0, 0, w, h), self._r, self._r)
        g = QLinearGradient(0, 0, w, 0)
        g.setColorAt(0, QColor(0, 0, 0, 0))
        g.setColorAt(0.2, QColor(200, 0, 0, 50))
        g.setColorAt(0.5, QColor(200, 0, 0, 80))
        g.setColorAt(0.8, QColor(200, 0, 0, 50))
        g.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(QPen(QBrush(g), 2))
        painter.drawLine(QPointF(0, 0.75), QPointF(w, 0.75))
        painter.end()

    def _tbar(self, title, close_fn=None):
        tb = QWidget()
        tb.setFixedHeight(40)
        tb.setStyleSheet('background:transparent;')
        tl = QHBoxLayout(tb)
        tl.setContentsMargins(16, 0, 12, 0)
        tl.setSpacing(6)
        for col in ('#cc0000', '#1e1e1e', '#141414'):
            d = QLabel()
            d.setFixedSize(8, 8)
            d.setStyleSheet(f'background:{col};border-radius:4px;')
            tl.addWidget(d)
        tl.addSpacing(8)
        lbl = QLabel(title)
        lbl.setFont(F('Segoe UI', 9, True))
        lbl.setStyleSheet('color:#ffffff;background:transparent;letter-spacing:3px;')
        tl.addWidget(lbl)
        tl.addStretch()
        if close_fn and self._has_close:
            xb = QPushButton('✕')
            xb.setFixedSize(24, 24)
            xb.setStyleSheet(
                'QPushButton{background:transparent;color:#666;border:none;font-size:14px;border-radius:12px;}'
                'QPushButton:hover{background:#cc0000;color:#fff;}'
            )
            xb.clicked.connect(close_fn)
            tl.addWidget(xb)
        def native_drag(event):
            if event.button() == Qt.MouseButton.LeftButton:
                user32.ReleaseCapture()
                hwnd = int(self.winId())
                user32.SendMessageW(hwnd, 161, 2, 0)
        tb.mousePressEvent = native_drag
        self._ml.addWidget(tb)
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet('background:#1a1a1a;')
        self._ml.addWidget(sep)
        return tb

    def _body(self, mg=(24, 20, 24, 20)):
        w = QWidget()
        w.setStyleSheet('background:transparent;')
        ly = QVBoxLayout(w)
        ly.setContentsMargins(*mg)
        ly.setSpacing(0)
        self._ml.addWidget(w)
        return ly

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            user32.ReleaseCapture()
            hwnd = int(self.winId())
            user32.SendMessageW(hwnd, 161, 2, 0)

# ===== SPLASH SCREEN =====
class SplashScreen(CardWin):
    done = pyqtSignal()

    def __init__(self):
        super().__init__(450, 320, 18, False)
        body = self._body((0, 0, 0, 0))
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        
        self.starfield = StarField()
        self.starfield.setFixedSize(450, 320)
        body.addWidget(self.starfield)
        
        overlay = QWidget()
        overlay.setStyleSheet('background:rgba(0,0,0,100);border-radius:18px;')
        overlay_layout = QVBoxLayout(overlay)
        overlay_layout.setContentsMargins(30, 30, 30, 30)
        overlay_layout.setSpacing(8)
        
        logo = QLabel('PHEDEV')
        logo.setFont(F('Segoe UI', 32, True))
        logo.setStyleSheet('color:#ffffff;background:transparent;letter-spacing:10px;')
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(logo)
        
        sub = QLabel('DARK INFINITY • v5.0')
        sub.setFont(F('Segoe UI', 10, True))
        sub.setStyleSheet('color:#888888;background:transparent;letter-spacing:4px;')
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(sub)
        
        overlay_layout.addSpacing(20)
        
        track = QWidget()
        track.setFixedSize(300, 2)
        track.setStyleSheet('background:#151515;border-radius:1px;')
        overlay_layout.addWidget(track, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._fill = QWidget(track)
        self._fill.setFixedSize(0, 2)
        self._fill.move(0, 0)
        self._fill.setStyleSheet('background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff0000,stop:0.5 #ffffff,stop:1 #ff0000);border-radius:1px;')
        
        overlay_layout.addSpacing(12)
        
        self._stat = QLabel('INITIALIZING')
        self._stat.setFont(F('Segoe UI', 8, True))
        self._stat.setStyleSheet('color:#888888;background:transparent;letter-spacing:3px;')
        self._stat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self._stat)
        
        body.addWidget(overlay)
        
        self._prog = 0.0
        self._t = QTimer()
        self._t.timeout.connect(self._tick)
        self._t.start(30)

    def _tick(self):
        self._prog = min(100.0, self._prog + 1.5)
        self._fill.setFixedWidth(int(300 * self._prog / 100))
        for th, txt in ((20, 'INITIALIZING'), (40, 'LOADING'), (60, 'CHECKING'),
                        (80, 'CONNECTING'), (100, 'READY')):
            if self._prog <= th:
                self._stat.setText(txt)
                break
        if self._prog >= 100:
            self._t.stop()
            QTimer.singleShot(300, self.done.emit)

# ===== SETTINGS PANEL =====
class SettingsPanel(CardWin):
    def __init__(self):
        super().__init__(400, 350, 14, True)
        self._tbar('SETTINGS', self.hide)
        body = self._body((20, 20, 20, 20))
        body.setSpacing(12)
        
        # Crosshair toggle
        self.crosshair_check = QCheckBox('Show Center Crosshair')
        self.crosshair_check.setStyleSheet('color:#ffffff;background:transparent;font-size:11px;')
        self.crosshair_check.setChecked(True)
        body.addWidget(self.crosshair_check)
        
        # Beep toggle
        self.beep_check = QCheckBox('Enable Beep Sounds')
        self.beep_check.setStyleSheet('color:#ffffff;background:transparent;font-size:11px;')
        self.beep_check.setChecked(beep_enabled)
        body.addWidget(self.beep_check)
        
        # Burst size slider
        lbl = QLabel('Burst Size:')
        lbl.setStyleSheet('color:#888888;background:transparent;font-size:11px;')
        body.addWidget(lbl)
        
        self.burst_slider = QSlider(Qt.Orientation.Horizontal)
        self.burst_slider.setRange(5, 30)
        self.burst_slider.setValue(15)
        self.burst_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: #222;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #cc0000;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
        """)
        body.addWidget(self.burst_slider)
        
        self.burst_label = QLabel('Current: 15')
        self.burst_label.setStyleSheet('color:#888888;background:transparent;font-size:10px;')
        self.burst_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self.burst_label)
        self.burst_slider.valueChanged.connect(lambda v: self.burst_label.setText(f'Current: {v}'))
        
        body.addSpacing(8)
        
        btn = NeoButton('SAVE SETTINGS', glow_color='#00ff66')
        btn.clicked.connect(self._save_settings)
        body.addWidget(btn)

    def _save_settings(self):
        global beep_enabled
        beep_enabled = self.beep_check.isChecked()
        save_keys()
        self.hide()

# ===== HOTKEY PANEL =====
_MODES = [
    ('toggle_key', 'TELE'),
    ('stop_key', 'FREEZE'),
    ('filter_key', 'GHOST'),
    ('aimlag_key', 'AIMLAG'),
    ('beep_key', 'BEEP'),
    ('binding_key', 'BIND MENU')
]

class HotkeyPanel(CardWin):
    _sig_done = pyqtSignal(str, str)

    def __init__(self):
        super().__init__(340, 400, 14, False)
        self._tbar('BINDINGS', None)
        self._vals = {a: 'NONE' for a, _ in _MODES}
        self._vals['binding_key'] = '5'
        self._tags = {}
        self._cap = None
        self._kl = None
        body = self._body((22, 16, 22, 18))
        
        for attr, label in _MODES:
            rw = QWidget()
            rw.setFixedHeight(46)
            rw.setStyleSheet('background:transparent;')
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(0, 0, 0, 0)
            
            lbl = QLabel(label)
            lbl.setFont(F('Segoe UI', 12, True))
            lbl.setStyleSheet('color:#ffffff;background:transparent;')
            
            v = self._vals[attr]
            tag = QPushButton(v)
            tag.setFixedSize(100, 32)
            tag.setFont(F('Segoe UI', 11, True))
            tag.setStyleSheet(self._ts(v == 'NONE'))
            tag.clicked.connect(lambda checked=False, a=attr: self._start_binding(a))
            tag.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self._tags[attr] = tag
            
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(tag)
            body.addWidget(rw)
            
            sep = QWidget()
            sep.setFixedHeight(1)
            sep.setStyleSheet('background:#151515;')
            body.addWidget(sep)
        
        body.addSpacing(8)
        self._hint = QLabel('Click button to bind key')
        self._hint.setFont(F('Segoe UI', 8, True))
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setStyleSheet('color:#888888;background:transparent;')
        self._hint.setFixedHeight(16)
        body.addWidget(self._hint)
        self._sig_done.connect(self._apply_finish)

    def _ts(self, cap=False, is_none=False):
        if cap:
            return ('QPushButton{background:#140505;border:2px solid #ff5500;'
                    'border-radius:8px;color:#ff6600;font-size:12px;font-weight:bold;'
                    'letter-spacing:1px;}')
        if is_none:
            return ('QPushButton{background:#0c0c0c;border:1.5px solid #252525;'
                    'border-radius:8px;color:#666666;font-size:12px;font-weight:bold;'
                    'letter-spacing:1px;}QPushButton:hover{border-color:#550000;color:#999999;}')
        return ('QPushButton{background:#1a0000;border:2px solid #660000;'
                'border-radius:8px;color:#ff4444;font-size:12px;font-weight:bold;'
                'letter-spacing:1px;}QPushButton:hover{border-color:#cc0000;'
                'background:#220000;color:#ff6666;}')

    def _start_binding(self, attr):
        if self._cap and self._cap != attr:
            self._cancel_binding(self._cap)
        self._cap = attr
        _cap_lock.set()
        tag = self._tags[attr]
        tag.setStyleSheet(self._ts(cap=True))
        tag.setText('...')
        tag.setFocus()
        self._hint.setText('PRESS ANY KEY NOW...')
        self._hint.setStyleSheet('color:#ff6600;background:transparent;font-weight:bold;')
        if self._kl:
            try:
                self._kl.stop()
            except:
                pass
        self._kl = keyboard.Listener(on_press=self._on_key_press)
        self._kl.start()

    def _on_key_press(self, key):
        if not self._cap:
            return True
        try:
            name = key_to_str(key)
            self._sig_done.emit(self._cap, name)
        except:
            pass
        return False

    @pyqtSlot(str, str)
    def _apply_finish(self, attr, name):
        if self._kl:
            try:
                self._kl.stop()
            except:
                pass
            self._kl = None
        self._vals[attr] = name
        if attr in self._tags:
            self._tags[attr].setStyleSheet(self._ts(False))
            self._tags[attr].setText(name)
            self._tags[attr].clearFocus()
        self._cap = None
        _cap_lock.clear()
        self._hint.setText('Click button to bind key')
        self._hint.setStyleSheet('color:#888888;background:transparent;font-weight:normal;')
        self._save_globals()

    def _cancel_binding(self, attr):
        if self._kl:
            try:
                self._kl.stop()
            except:
                pass
            self._kl = None
        self._vals[attr] = 'NONE'
        if attr in self._tags:
            self._tags[attr].setStyleSheet(self._ts(True))
            self._tags[attr].setText('NONE')
            self._tags[attr].clearFocus()
        self._cap = None
        _cap_lock.clear()
        self._hint.setText('Click button to bind key')
        self._hint.setStyleSheet('color:#888888;background:transparent;font-weight:normal;')
        self._save_globals()

    def _save_globals(self):
        global toggle_key, stop_key, filter_key, aimlag_key, beep_key, binding_key
        toggle_key = self._vals['toggle_key']
        stop_key = self._vals['stop_key']
        filter_key = self._vals['filter_key']
        aimlag_key = self._vals['aimlag_key']
        beep_key = self._vals['beep_key']
        binding_key = self._vals['binding_key']
        save_keys()

    def refresh_from_globals(self):
        gmap = {
            'toggle_key': toggle_key,
            'stop_key': stop_key,
            'filter_key': filter_key,
            'aimlag_key': aimlag_key,
            'beep_key': beep_key,
            'binding_key': binding_key
        }
        for attr, _ in _MODES:
            v = gmap.get(attr, 'NONE')
            if not v or v.upper() in ('NONE', '0', ''):
                v = 'NONE'
            else:
                v = v.upper()
            if attr == 'binding_key' and v == 'NONE':
                v = '5'
            self._vals[attr] = v
            if attr in self._tags:
                self._tags[attr].setText(v)
                self._tags[attr].setStyleSheet(self._ts(v == 'NONE'))

    def toggle_vis(self):
        if self.isVisible():
            self.hide()
        else:
            self._center()
            self.show()
            self.raise_()
            self.activateWindow()

    def closeEvent(self, e):
        if self._cap:
            self._cancel_binding(self._cap)
        super().closeEvent(e)

# ===== TAIWAN OVERLAY =====
class TaiwanOverlay(QMainWindow):
    def __init__(self, emulator_hwnd=None):
        super().__init__()
        self._emulator_hwnd = emulator_hwnd
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        central.setStyleSheet('background: transparent;')
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.label = QLabel('⚡ PHEDEV TAIWAN')
        self.label.setFont(QFont('Segoe UI', 16, QFont.Weight.Bold))
        self.label.setStyleSheet('color: #FF3333; background: transparent; padding: 0px; border: none;')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        self.setFixedSize(260, 42)
        
        self._color_timer = QTimer(self)
        self._color_timer.timeout.connect(self._color_effect)
        self._color_timer.start(50)
        self._color_index = 0
        
        if self._emulator_hwnd:
            self._sync_timer = QTimer(self)
            self._sync_timer.timeout.connect(self._sync_position)
            self._sync_timer.start(16)
            self._sync_position()
        else:
            self._center_top()

    def _center_top(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, 10)

    def _sync_position(self):
        try:
            if self._emulator_hwnd and win32gui.IsWindow(self._emulator_hwnd):
                rect = win32gui.GetWindowRect(self._emulator_hwnd)
                x = rect[0] + (rect[2] - rect[0] - self.width()) // 2
                y = rect[1] + 8
                self.move(x, y)
                self._force_top()
        except:
            pass

    def _force_top(self):
        try:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
        except:
            pass

    def _color_effect(self):
        self._color_index = (self._color_index + 1) % 360
        colors = [
            QColor.fromHsv(self._color_index, 255, 255).name(),
            f"#{255:02X}{max(0, min(255, int(150 + 105 * abs((self._color_index % 120) - 60) / 60))):02X}{max(0, min(255, int(150 + 105 * abs((self._color_index % 120) - 60) / 60))):02X}",
            f"#{255:02X}{max(0, min(255, int(200 + 55 * abs((self._color_index % 90) - 45) / 45))):02X}{max(0, min(255, int(100 + 100 * abs((self._color_index % 90) - 45) / 45))):02X}"
        ]
        color = colors[(self._color_index // 180) % len(colors)]
        self.label.setStyleSheet(f'color: {color}; background: transparent; padding: 0px; border: none;')

    def set_emulator_hwnd(self, hwnd):
        self._emulator_hwnd = hwnd
        if not hasattr(self, '_sync_timer') or self._sync_timer is None:
            self._sync_timer = QTimer(self)
            self._sync_timer.timeout.connect(self._sync_position)
            self._sync_timer.start(16)
        self._sync_position()

# ===== MINI OVERLAY =====
class MiniOverlay(QMainWindow):
    def __init__(self, hwnd):
        super().__init__()
        self._hwnd = hwnd
        self._closing = False
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        c = QWidget()
        c.setStyleSheet('background:transparent;border:none;')
        self.setCentralWidget(c)
        
        ml = QVBoxLayout(c)
        ml.setContentsMargins(0, 0, 0, 4)
        ml.setSpacing(4)
        ml.setSizeConstraint(QVBoxLayout.SizeConstraint.SetFixedSize)
        
        self._lbls = {}
        _off = "color:#ffffff;font-family:'Segoe UI';font-size:11px;font-weight:bold;background:transparent;border:none;"
        _on = "color:#00ff66;font-family:'Segoe UI';font-size:11px;font-weight:bold;background:transparent;border:none;"
        self._soff = _off
        self._son = _on
        
        for sh, full in (('Freeze', 'Freeze'), ('Ghost', 'Ghost'),
                         ('Telekill', 'Telekill'), ('AimLag', 'AimLag')):
            rw = QWidget()
            rw.setFixedSize(120, 24)
            rl = QHBoxLayout(rw)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(0)
            rl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            
            bar = QWidget()
            bar.setFixedSize(3, 24)
            bar.setStyleSheet('background:#ff3333;border-top-left-radius:2px;border-bottom-left-radius:2px;border:none;')
            rl.addWidget(bar)
            
            tc = QFrame()
            tc.setFixedSize(110, 24)
            tc.setStyleSheet('QFrame{background:rgba(8,8,8,0.95);border:1px solid rgba(255,255,255,0.1);border-left:none;border-top-right-radius:2px;border-bottom-right-radius:2px;}')
            tcl = QHBoxLayout(tc)
            tcl.setContentsMargins(8, 0, 8, 0)
            
            lbl = QLabel(sh)
            lbl.setStyleSheet(_off)
            lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tcl.addWidget(lbl)
            rl.addWidget(tc)
            self._lbls[full] = lbl
            ml.addWidget(rw)
        
        self.setFixedWidth(125)
        self._pt = QTimer(self)
        self._pt.timeout.connect(self._sync)
        self._pt.start(16)
        self._sync()
        self.show()
        self._force_top()

    def _force_top(self):
        try:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
        except:
            pass

    def _sync(self):
        if self._closing:
            return
        try:
            if self._hwnd and win32gui.IsWindow(self._hwnd):
                r = win32gui.GetWindowRect(self._hwnd)
                x = r[0] + 8
                y = r[1] + 50
                if abs(self.pos().x() - x) > 2 or abs(self.pos().y() - y) > 2:
                    self.move(x, y)
                self._force_top()
        except:
            pass

    @pyqtSlot(bool, bool, bool, bool)
    def update_status(self, fr, gh, te, al):
        if self._closing:
            return
        try:
            for n, a in (('Freeze', fr), ('Ghost', gh), ('Telekill', te), ('AimLag', al)):
                if n in self._lbls:
                    self._lbls[n].setStyleSheet(self._son if a else self._soff)
        except RuntimeError:
            self._closing = True
        except:
            pass

    def closeEvent(self, e):
        self._closing = True
        self._pt.stop()
        super().closeEvent(e)

# ===== CENTER CROSSHAIR =====
class CenterCrosshair(QMainWindow):
    def __init__(self, emulator_hwnd=None):
        super().__init__()
        self._emulator_hwnd = emulator_hwnd
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.NoDropShadowWindowHint |
            Qt.WindowType.X11BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        central.setStyleSheet('background: transparent;')
        self.setCentralWidget(central)
        self.setFixedSize(50, 50)
        
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate)
        self._anim_timer.start(30)
        self._angle = 0
        self._pulse = 0
        self._center_screen()
        self._sync_timer = QTimer(self)
        self._sync_timer.timeout.connect(self._center_screen)
        self._sync_timer.start(1000)

    def _center_screen(self):
        screen = QApplication.primaryScreen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
        self._force_top()

    def _force_top(self):
        try:
            hwnd = int(self.winId())
            win32gui.SetWindowPos(
                hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
                win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
        except:
            pass

    def _animate(self):
        self._angle = (self._angle + 2.5) % 360
        self._pulse = (self._pulse + 1) % 100
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2
        
        pulse_phase = abs((self._pulse % 100) - 50) / 50.0
        pulse_scale = 1.0 + 0.15 * (1.0 - pulse_phase)
        
        painter.setPen(QPen(QColor(255, 40, 40, 40), 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), 20 * pulse_scale, 20 * pulse_scale)
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self._angle)
        gradient = QLinearGradient(-18, -18, 18, 18)
        gradient.setColorAt(0.0, QColor(255, 30, 30, 120))
        gradient.setColorAt(0.5, QColor(255, 80, 80, 60))
        gradient.setColorAt(1.0, QColor(255, 30, 30, 120))
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        radius = int(16 * pulse_scale)
        painter.drawEllipse(QPointF(0, 0), radius, radius)
        painter.restore()
        
        painter.setPen(QPen(QColor(255, 20, 20, 220), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        gap = 3
        line_len = 10
        painter.drawLine(cx - line_len, cy, cx - gap, cy)
        painter.drawLine(cx + gap, cy, cx + line_len, cy)
        painter.drawLine(cx, cy - line_len, cx, cy - gap)
        painter.drawLine(cx, cy + gap, cx, cy + line_len)
        
        painter.setPen(Qt.PenStyle.NoPen)
        glow = QRadialGradient(cx, cy, 6)
        glow.setColorAt(0, QColor(255, 80, 80, 255))
        glow.setColorAt(0.5, QColor(255, 150, 150, 200))
        glow.setColorAt(1, QColor(255, 200, 200, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)
        
        painter.setPen(QPen(QColor(255, 30, 30, 80), 1))
        corner_dist = 18
        corner_size = 3
        for dx, dy in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            x = cx + dx * corner_dist
            y = cy + dy * corner_dist
            painter.drawLine(x - dx * corner_size, y, x, y - dy * corner_size)
            painter.drawLine(x, y - dy * corner_size, x + dx * corner_size, y)
            painter.drawLine(x + dx * corner_size, y, x, y + dy * corner_size)
            painter.drawLine(x, y + dy * corner_size, x - dx * corner_size, y)

    def set_emulator_hwnd(self, hwnd):
        self._emulator_hwnd = hwnd

# ===== GRADIENT LINE =====
class GradientLine(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(4)

    def paintEvent(self, event):
        painter = QPainter(self)
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0.0, QColor(255, 0, 0, 0))
        gradient.setColorAt(0.2, QColor(255, 0, 0, 200))
        gradient.setColorAt(0.5, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.8, QColor(255, 0, 0, 200))
        gradient.setColorAt(1.0, QColor(255, 0, 0, 0))
        painter.setPen(QPen(QBrush(gradient), 2))
        painter.setBrush(QBrush(gradient))
        painter.drawRect(self.rect())

# ===== PHEDEV ESP MENU =====
class PhedevESP(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PHEDEV 999+')
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(280, 380)
        
        central = QWidget()
        central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        central.setStyleSheet('background:rgba(10,10,10,230);border-radius:12px;border:1px solid #1a1a1a;')
        self.setCentralWidget(central)
        
        ml = QVBoxLayout(central)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        
        ml.addWidget(GradientLine())
        
        # Title bar
        tf = QWidget()
        tf.setFixedHeight(40)
        tf.setStyleSheet('background:rgba(10,10,10,200);')
        tl = QHBoxLayout(tf)
        tl.setContentsMargins(12, 0, 12, 0)
        
        self.title_label = QLabel('⚡ PHEDEV 999+')
        self.title_label.setFont(QFont('Consolas', 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet('color:#FF2222;background:transparent;')
        tl.addWidget(self.title_label)
        tl.addStretch()
        
        # Settings button
        self.settings_btn = QPushButton('⚙')
        self.settings_btn.setFixedSize(30, 30)
        self.settings_btn.setStyleSheet('QPushButton{background:transparent;color:#666;border:none;font-size:16px;}QPushButton:hover{color:#fff;}')
        self.settings_btn.clicked.connect(self._open_settings)
        tl.addWidget(self.settings_btn)
        
        ml.addWidget(tf)
        
        sep = QWidget()
        sep.setFixedHeight(2)
        sep.setStyleSheet('background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #ff0000,stop:0.5 #ffffff,stop:1 #ff0000);')
        ml.addWidget(sep)
        
        # Mode buttons
        self.modes = [
            ('Freeze', toggle_freeze),
            ('Ghost', toggle_ghost),
            ('Telekill', toggle_tele),
            ('AimLag', toggle_aimlag)
        ]
        self.mode_buttons = {}
        self.selected_mode = None
        
        for mode, func in self.modes:
            row = QWidget()
            row.setFixedHeight(44)
            row.setStyleSheet('background:rgba(17,17,17,200);')
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            
            bar = QWidget()
            bar.setFixedWidth(3)
            bar.setStyleSheet('background:#FF2222;')
            
            lbl = QLabel(mode)
            lbl.setFont(QFont('Consolas', 11, QFont.Weight.Bold))
            lbl.setStyleSheet('color:#FF3333;background:transparent;padding-left:8px;')
            
            status = QLabel('○')
            status.setFont(QFont('Consolas', 12))
            status.setStyleSheet('color:#333333;background:transparent;padding-right:12px;')
            status.setAlignment(Qt.AlignmentFlag.AlignRight)
            
            rl.addWidget(bar)
            rl.addWidget(lbl)
            rl.addStretch()
            rl.addWidget(status)
            
            def make_click(m, r, l, s, f):
                def handler(event):
                    self._click(m, r, l, s, f)
                return handler
            row.mousePressEvent = make_click(mode, row, lbl, status, func)
            
            self.mode_buttons[mode] = (row, lbl, status)
            ml.addWidget(row)
        
        # Hotkey button
        hk_btn = NeoButton('🔑 BIND KEYS', glow_color='#666666')
        hk_btn.setFixedHeight(36)
        hk_btn.clicked.connect(self._open_hotkeys)
        ml.addWidget(hk_btn)
        
        # Quit button
        quit_btn = NeoButton('✕ EXIT', glow_color='#ff0000')
        quit_btn.setFixedHeight(36)
        quit_btn.clicked.connect(quit_app)
        ml.addWidget(quit_btn)
        
        def native_drag(event):
            if event.button() == Qt.MouseButton.LeftButton:
                user32.ReleaseCapture()
                hwnd = int(self.winId())
                user32.SendMessageW(hwnd, 161, 2, 0)
        tf.mousePressEvent = native_drag
        
        sig.ui.connect(self._upd)
        self._gs = 0
        at = QTimer(self)
        at.timeout.connect(self._glitch)
        at.start(33)
        
        self.settings_panel = None
        self.hotkey_panel = None

    def _open_settings(self):
        if self.settings_panel is None:
            self.settings_panel = SettingsPanel()
        self.settings_panel.show()
        self.settings_panel.raise_()

    def _open_hotkeys(self):
        if self.hotkey_panel is None:
            self.hotkey_panel = HotkeyPanel()
            self.hotkey_panel.refresh_from_globals()
        self.hotkey_panel.toggle_vis()

    def _click(self, mode, row, lbl, status, func):
        try:
            if self.selected_mode and self.selected_mode in self.mode_buttons:
                pr, pl, ps = self.mode_buttons[self.selected_mode]
                pr.setStyleSheet('background:rgba(17,17,17,200);')
                pl.setStyleSheet('color:#FF3333;background:transparent;padding-left:8px;')
                ps.setStyleSheet('color:#333333;background:transparent;padding-right:12px;')
            
            self.selected_mode = mode
            row.setStyleSheet('background:rgba(26,0,0,220);')
            lbl.setStyleSheet('color:#FF6666;background:transparent;padding-left:8px;')
            status.setStyleSheet('color:#FF6666;background:transparent;padding-right:12px;')
            
            func()
        except:
            pass

    @pyqtSlot(bool, bool, bool, bool)
    def _upd(self, fr, gh, te, al):
        try:
            mp = {'Freeze': fr, 'Ghost': gh, 'Telekill': te, 'AimLag': al}
            for m, (r, l, s) in self.mode_buttons.items():
                if mp.get(m, False):
                    l.setStyleSheet('color:#00FF66;background:transparent;padding-left:8px;')
                    s.setStyleSheet('color:#00FF66;background:transparent;padding-right:12px;')
                    r.setStyleSheet('background:rgba(0,40,0,220);')
                else:
                    r.setStyleSheet('background:rgba(17,17,17,200);')
                    if m == self.selected_mode:
                        l.setStyleSheet('color:#FF6666;background:transparent;padding-left:8px;')
                        s.setStyleSheet('color:#FF6666;background:transparent;padding-right:12px;')
                    else:
                        l.setStyleSheet('color:#FF3333;background:transparent;padding-left:8px;')
                        s.setStyleSheet('color:#333333;background:transparent;padding-right:12px;')
        except RuntimeError:
            pass

    def _glitch(self):
        try:
            self._gs = (self._gs + 1) % 120
            if self._gs % 8 == 0:
                colors = ['#FF2222', '#FF4444', '#FF1111', '#FF3333']
                c = colors[self._gs // 8 % len(colors)]
                self.title_label.setStyleSheet(f'color:{c};background:transparent;')
        except:
            pass

    def closeEvent(self, event):
        if self.settings_panel:
            self.settings_panel.close()
        if self.hotkey_panel:
            self.hotkey_panel.close()
        super().closeEvent(event)

# ===== WAITING WINDOW =====
class WaitingWindow(CardWin):
    def __init__(self):
        super().__init__(400, 180, 14, True)
        self._tbar('PHEDEV', lambda: os._exit(0))
        body = self._body((30, 25, 30, 25))
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._dots = 0
        self._label = QLabel('Loading...')
        self._label.setFont(F('Segoe UI', 14, True))
        self._label.setStyleSheet('color:#ff4444;background:transparent;letter-spacing:2px;')
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self._label)
        
        body.addSpacing(12)
        
        self._sub = QLabel('Detecting emulator...')
        self._sub.setFont(F('Segoe UI', 10, True))
        self._sub.setStyleSheet('color:#666666;background:transparent;letter-spacing:1px;')
        self._sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.addWidget(self._sub)
        
        body.addSpacing(12)
        
        self._progress = QWidget()
        self._progress.setFixedSize(300, 2)
        self._progress.setStyleSheet('background:#151515;border-radius:1px;')
        body.addWidget(self._progress, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._progress_fill = QWidget(self._progress)
        self._progress_fill.setFixedSize(0, 2)
        self._progress_fill.move(0, 0)
        self._progress_fill.setStyleSheet('background:#cc0000;border-radius:1px;')
        
        self._timer = QTimer()
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)
        self._pulse_val = 0

    def _animate(self):
        self._dots = (self._dots + 1) % 4
        dots = '.' * self._dots
        self._label.setText(f'Loading{dots}')
        self._pulse_val = (self._pulse_val + 3) % 310
        if self._pulse_val > 300:
            self._pulse_val = 300
        self._progress_fill.setFixedWidth(self._pulse_val)

    def update_status(self, text):
        try:
            self._sub.setText(text)
            QApplication.processEvents()
        except:
            pass

    def closeEvent(self, e):
        if self._timer.isActive():
            self._timer.stop()
        super().closeEvent(e)

# ===== MAIN =====
def run():
    try:
        check_debugger()
        if sys.gettrace():
            _crack('Tracer')
        check_vm()
        check_monitor()
        threading.Thread(target=bg_anti, daemon=True).start()
        
        _app = QApplication(sys.argv)
        _app.setStyle('Fusion')
        _app.setQuitOnLastWindowClosed(False)
        
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        _app.setPalette(palette)
        
        splash = SplashScreen()
        ms = [False]
        hk_ref = [None]

        def after_splash():
            splash.hide()
            start_main()

        def start_main():
            if ms[0]:
                return
            ms[0] = True
            wait_win = WaitingWindow()
            global waiting_window
            waiting_window = wait_win
            wait_win.show()
            hwnd_found = [None]
            attempt = [0]

            def try_find_emulator():
                hwnd_found[0] = find_emulator()
                attempt[0] += 1
                if hwnd_found[0]:
                    wait_win.update_status('Emulator found! Loading...')
                    QTimer.singleShot(500, lambda: init_modules(hwnd_found[0], wait_win))
                    return
                if app_quit_flag:
                    wait_win.close()
                    return
                status_msgs = [
                    'Searching for emulator...',
                    'Please open your emulator...',
                    'Waiting for emulator...',
                    'Scanning windows...',
                    'Looking for game emulator...'
                ]
                wait_win.update_status(status_msgs[attempt[0] % len(status_msgs)])
                QTimer.singleShot(500, try_find_emulator)

            def init_modules(found_hwnd, ww):
                ww.close()
                global waiting_window, taiwan_overlay, esp_window, mini_window, alive_timer, center_crosshair
                waiting_window = None
                
                taiwan_overlay = TaiwanOverlay(found_hwnd)
                taiwan_overlay.show()
                
                load_keys_file()
                
                esp = PhedevESP()
                esp_window = esp
                esp.show()
                
                mini = MiniOverlay(found_hwnd)
                mini_window = mini
                mini.show()
                sig.mini.connect(mini.update_status)
                
                center_crosshair = CenterCrosshair(found_hwnd)
                center_crosshair.show()
                
                emulator_pid = get_emulator_pid(found_hwnd)

                def check_emulator_alive():
                    if app_quit_flag:
                        return
                    try:
                        if emulator_pid:
                            psutil.Process(emulator_pid)
                        if not win32gui.IsWindow(found_hwnd):
                            quit_app()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        quit_app()
                    except:
                        pass

                alive_timer = QTimer()
                alive_timer.timeout.connect(check_emulator_alive)
                alive_timer.start(500)

                def watch_emu_thread():
                    while not app_quit_flag:
                        try:
                            if emulator_pid:
                                psutil.Process(emulator_pid)
                            if not win32gui.IsWindow(found_hwnd):
                                QTimer.singleShot(0, quit_app)
                                return
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            QTimer.singleShot(0, quit_app)
                            return
                        except:
                            pass
                        time.sleep(1)

                threading.Thread(target=watch_emu_thread, daemon=True).start()
                pressed = set()

                def on_ev(ev, down):
                    if _cap_lock.is_set():
                        return None
                    if isinstance(ev, mouse.Button):
                        kn = mouse_to_str(ev).upper()
                    else:
                        kn = key_to_str(ev).upper()
                    if not kn:
                        return None
                    if down:
                        if kn in pressed:
                            return None
                        pressed.add(kn)
                        if toggle_key != 'NONE' and kn == toggle_key:
                            toggle_tele()
                            return None
                        if stop_key != 'NONE' and kn == stop_key:
                            toggle_freeze()
                            return None
                        if filter_key != 'NONE' and kn == filter_key:
                            toggle_ghost()
                            return None
                        if aimlag_key != 'NONE' and kn == aimlag_key:
                            toggle_aimlag()
                            return None
                        if beep_key != 'NONE' and kn == beep_key:
                            global beep_enabled
                            beep_enabled = not beep_enabled
                            save_keys()
                            return None
                        if binding_key != 'NONE' and kn == binding_key:
                            if esp:
                                esp._open_hotkeys()
                            return None
                        if kn == 'F10':
                            quit_app()
                            return None
                    else:
                        pressed.discard(kn)
                    return None

                keyboard.Listener(
                    on_press=lambda k: on_ev(k, True),
                    on_release=lambda k: on_ev(k, False)
                ).start()
                mouse.Listener(
                    on_click=lambda x, y, b, p: on_ev(b, p)
                ).start()
                mouse.Listener(on_click=on_mouse_click).start()

                global R_O, R_I, R_F, R_A
                R_O = True
                R_I = True
                R_F = True
                R_A = True

                divert_configs = [
                    (FILTER_O, lambda: packet_tele, lambda: tele_mode, lambda: R_O),
                    (FILTER_I, lambda: packet_freeze, lambda: freeze_mode, lambda: R_I),
                    (FILTER_F, lambda: packet_ghost, lambda: ghost_mode, lambda: R_F),
                    (FILTER_AIMLAG, lambda: packet_aimlag, lambda: aimlag_mode, lambda: R_A)
                ]
                for f, p, c, r in divert_configs:
                    threading.Thread(target=divert, args=(f, p, c, r), daemon=True).start()

            QTimer.singleShot(100, try_find_emulator)

        splash.done.connect(after_splash)
        splash.show()
        sys.exit(_app.exec())
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run()