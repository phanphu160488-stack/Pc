# ==================== PHEDEV FAKELAG SYSTEM ====================
# phedev_menu.py — Build: pyinstaller --onefile --windowed --name "Phedev" phedev_menu.py

import webbrowser
import os
import sys
import threading
import time
import ctypes
import winsound
import json
import pydivert
import keyboard
import subprocess
import re
from pynput import mouse
import win32gui
import win32api
import win32process
import psutil
from colorama import init, Fore, Style
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMainWindow, QSystemTrayIcon, QMenu,
    QGridLayout, QGraphicsDropShadowEffect, QLineEdit, QSlider,
    QColorDialog, QStackedWidget, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QPixmap

init(autoreset=True)

# ==================== PHEDEV CONSTANTS ====================
APP_NAME = "⚡ PHEDEV FAKELAG"
BRAND_COLOR = "#d4af37"
BRAND_COLOR_DARK = "#b38f00"
ACCENT_COLOR = "#38ef7d"
ACCENT_COLOR_DARK = "#11998e"

# ==================== GLOBAL VARIABLES ====================
ghost_mode = False
R_F = False
R_I = False
R_O = False
packet_tele = []
packet_freeze = []
packet_ghost = []
freeze_mode = False
tele_mode = False
aimlag_enabled = False
running = True
sound_enabled = True
overlay_enabled = True
lock = threading.Lock()

main_window_instance = None
overlay_instance = None
hotkey_listener_thread = None

# ==================== WIN DIVERT FILTERS ====================
FILTER_O = '(udp.DstPort >= 10010 and udp.DstPort <= 10020) and udp.PayloadLength >= 40'
FILTER_I = 'inbound and udp.SrcPort >= 10000 and udp.SrcPort <= 10099 and ip and ip.Protocol == 17 and ip.Length >= 50 and ip.Length <= 1491'
FILTER_F = 'udp and udp.DstPort >= 10000 and udp.DstPort <= 10099 and ip.Length and udp.PayloadLength >= 54 and udp.PayloadLength <= 63'

# ==================== CONFIG ====================
HOTKEY_FILE = 'phedev_config.json'

class HotkeyConfig:
    def __init__(self, key='', is_valid=False):
        self.key = key
        self.is_valid = is_valid

class AppConfig:
    def __init__(self):
        self.accent_color = '#38ef7d'
        self.tele_hotkey = HotkeyConfig()
        self.freeze_hotkey = HotkeyConfig()
        self.ghost_hotkey = HotkeyConfig()
        self.menu_hotkey = HotkeyConfig()
        self.tele_speed = 5
        self.tele_filter = 'goc'
        self.freeze_filter = 'goc'

app_config = AppConfig()

# ==================== MOUSE MAP ====================
MOUSE_DISPLAY = {
    'mouse:left': 'LMB', 'mouse:right': 'RMB', 'mouse:middle': 'MMB',
    'mouse:x1': 'MB4', 'mouse:x2': 'MB5'
}

# ==================== SIGNALS ====================
class Signals(QObject):
    update_overlay = pyqtSignal(bool, bool, bool)
    toggle_overlay = pyqtSignal(bool)
    update_status = pyqtSignal()
    hotkey_pressed = pyqtSignal(str, str)
    toggle_menu = pyqtSignal()

signals = Signals()

# ==================== AUDIO MANAGER ====================
class AudioManager:
    def play_on(self):
        try:
            winsound.Beep(1200, 80)
            time.sleep(0.06)
            winsound.Beep(1600, 100)
        except:
            pass

    def play_off(self):
        try:
            winsound.Beep(1000, 100)
            time.sleep(0.06)
            winsound.Beep(800, 120)
        except:
            pass

audio = AudioManager()

# ==================== UTILITY FUNCTIONS ====================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def log_error(msg):
    print(f"{Fore.RED}[ERROR] {msg}{Style.RESET_ALL}")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    try:
        if hasattr(sys, 'frozen') or '__compiled__' in globals():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, "", None, 1)
        else:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{__file__}"', None, 1)
        sys.exit()
    except:
        pass

def load_config():
    global app_config
    try:
        if os.path.exists(HOTKEY_FILE):
            with open(HOTKEY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for key, value in data.items():
                    if hasattr(app_config, key):
                        if key in ['tele_hotkey', 'freeze_hotkey', 'ghost_hotkey', 'menu_hotkey']:
                            hk = HotkeyConfig()
                            hk.key = value.get('key', '')
                            hk.is_valid = value.get('is_valid', False)
                            setattr(app_config, key, hk)
                        else:
                            setattr(app_config, key, value)
    except:
        pass

def save_config():
    try:
        data = {}
        for key, value in app_config.__dict__.items():
            if isinstance(value, HotkeyConfig):
                data[key] = {'key': value.key, 'is_valid': value.is_valid}
            else:
                data[key] = value
        with open(HOTKEY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except:
        pass

def set_native_window_icon(hwnd):
    try:
        icon_path = resource_path('Logo.ico')
        user32 = ctypes.windll.user32
        WM_SETICON = 0x0080
        ICON_SMALL = 0
        ICON_BIG = 1
        hicon = ctypes.windll.user32.LoadImageW(0, icon_path, 1, 0, 0, 0x00000010)
        if hicon:
            user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
            user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    except:
        pass

# ==================== PHEDEV BUTTON ====================
class PhedevButton(QPushButton):
    def __init__(self, text="", parent=None, color=BRAND_COLOR):
        super().__init__(text, parent)
        self.color = color
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {color}, stop:1 {BRAND_COLOR_DARK});
                color: black;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {BRAND_COLOR_DARK}, stop:1 {color});
            }}
        """)

# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PHEDEV FAKELAG")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._dragging = False
        self._drag_pos = QPoint()
        self.menu_open = True
        self.animating = False
        self.setting_hotkey_type = None
        self.keyboard_hook = None

        # Central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # ===== HEADER =====
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"""
            QFrame {{
                background: #121015;
                border: 1px solid {BRAND_COLOR};
                border-radius: 12px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 10, 0)

        logo = QLabel("⚡")
        logo.setStyleSheet(f"font-size: 20px; color: {BRAND_COLOR}; border: none;")
        header_layout.addWidget(logo)

        title = QLabel("PHEDEV FAKELAG")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self.btn_toggle = QPushButton("☰ MENU ON")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_toggle.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 {BRAND_COLOR}, stop:1 {BRAND_COLOR_DARK});
                color: black;
                border: 1px solid #ffe066;
                border-radius: 6px;
                padding: 0 10px;
            }}
            QPushButton:hover {{ background: {BRAND_COLOR}; }}
        """)
        self.btn_toggle.clicked.connect(self.toggle_menu)
        header_layout.addWidget(self.btn_toggle)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {BRAND_COLOR};
                border: 1px solid {BRAND_COLOR};
                border-radius: 13px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #ef4444;
                border-color: #ef4444;
            }}
        """)
        close_btn.clicked.connect(self.close_app)
        header_layout.addWidget(close_btn)

        main_layout.addWidget(header)

        # ===== BODY =====
        body = QFrame()
        body.setStyleSheet("background: transparent;")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(10)

        # Navigation
        nav = QFrame()
        nav.setFixedWidth(180)
        nav.setStyleSheet(f"""
            QFrame {{
                background: #121015;
                border: 1px solid {BRAND_COLOR};
                border-radius: 12px;
            }}
        """)
        nav_layout = QVBoxLayout(nav)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(4)

        nav_items = [
            ("⚡", "FAKELAG"),
            ("⌨️", "HOTKEYS"),
            ("⚙️", "FILTERS"),
            ("🎵", "AUDIO"),
            ("📖", "ABOUT")
        ]

        self.nav_btns = []
        for icon, text in nav_items:
            btn = QPushButton(f"{icon}  {text}")
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: #c5a059;
                    font-weight: bold;
                    border: 1px solid transparent;
                    border-radius: 6px;
                    text-align: left;
                    padding-left: 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255, 215, 0, 0.12);
                    color: {BRAND_COLOR};
                    border-color: #c5a059;
                }}
            """)
            btn.clicked.connect(lambda checked, idx=len(self.nav_btns): self.switch_tab(idx))
            nav_layout.addWidget(btn)
            self.nav_btns.append(btn)

        nav_layout.addStretch()
        body_layout.addWidget(nav)

        # Content
        self.stacked = QStackedWidget()
        self.stacked.setStyleSheet(f"""
            QStackedWidget {{
                background: #121015;
                border: 1px solid {BRAND_COLOR};
                border-radius: 12px;
            }}
        """)

        # Tab 0: FAKELAG
        p0 = QWidget()
        p0_layout = QVBoxLayout(p0)
        p0_layout.setContentsMargins(20, 20, 20, 20)
        p0_layout.setSpacing(15)

        p0_title = QLabel("⚡ FAKELAG SETTINGS")
        p0_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p0_title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        p0_layout.addWidget(p0_title)

        # Lag slider
        lag_lay = QHBoxLayout()
        lag_lay.addWidget(QLabel("LAG (ms):"))
        self.slider_lag = QSlider(Qt.Orientation.Horizontal)
        self.slider_lag.setRange(0, 5000)
        self.slider_lag.setValue(300)
        self.slider_lag.setStyleSheet("""
            QSlider::groove:horizontal {
                border-radius: 4px; height: 6px; background: #141216;
            }
            QSlider::handle:horizontal {
                background: #ffd700; width: 16px; height: 16px;
                margin: -5px 0; border-radius: 8px; border: 2px solid #c5a059;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #d4af37, stop:1 #ffd700);
                border-radius: 4px;
            }
        """)
        self.lag_label = QLabel("300")
        self.lag_label.setFixedWidth(50)
        self.lag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lag_label.setStyleSheet("color: #ffd700; font-weight: bold;")
        self.slider_lag.valueChanged.connect(lambda v: self.lag_label.setText(str(v)))
        lag_lay.addWidget(self.slider_lag)
        lag_lay.addWidget(self.lag_label)
        p0_layout.addLayout(lag_lay)

        # Presets
        preset_lay = QHBoxLayout()
        for name, val in [("Low", 200), ("Med", 800), ("High", 2026)]:
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255,215,0,0.06);
                    color: #c5a059;
                    border: 1px solid #554422;
                    border-radius: 5px;
                    padding: 6px 12px;
                }}
                QPushButton:hover {{
                    background: rgba(255,215,0,0.15);
                    color: {BRAND_COLOR};
                    border-color: #d4af37;
                }}
            """)
            btn.clicked.connect(lambda checked, v=val: self.slider_lag.setValue(v))
            preset_lay.addWidget(btn)
        p0_layout.addLayout(preset_lay)

        # Mode buttons
        mode_lay = QHBoxLayout()
        mode_lay.setSpacing(10)

        self.btn_tele = QPushButton("⚡ TELE")
        self.btn_freeze = QPushButton("🧊 FREEZE")
        self.btn_ghost = QPushButton("👻 GHOST")
        self.btn_aimlag = QPushButton("🎯 AIMLAG")

        for btn in [self.btn_tele, self.btn_freeze, self.btn_ghost, self.btn_aimlag]:
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #141216;
                    color: #c5a059;
                    border: 1px solid #554422;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: rgba(255,215,0,0.1);
                    border-color: {BRAND_COLOR};
                }}
            """)
            mode_lay.addWidget(btn)

        self.btn_tele.clicked.connect(self.toggle_tele_gui)
        self.btn_freeze.clicked.connect(self.toggle_freeze_gui)
        self.btn_ghost.clicked.connect(self.toggle_ghost_gui)
        self.btn_aimlag.clicked.connect(self.toggle_aimlag_gui)

        p0_layout.addLayout(mode_lay)
        p0_layout.addStretch()
        self.stacked.addWidget(p0)

        # Tab 1: HOTKEYS
        p1 = QWidget()
        p1_layout = QVBoxLayout(p1)
        p1_layout.setContentsMargins(20, 20, 20, 20)
        p1_layout.setSpacing(15)

        p1_title = QLabel("⌨️ HOTKEYS")
        p1_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p1_title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        p1_layout.addWidget(p1_title)

        hk_grid = QGridLayout()
        hk_grid.setSpacing(10)

        hk_items = [
            ("TELE", "hotkey_tele"),
            ("FREEZE", "hotkey_freeze"),
            ("GHOST", "hotkey_ghost"),
            ("MENU", "hotkey_menu")
        ]

        for i, (name, attr) in enumerate(hk_items):
            lbl = QLabel(f"{name}: ...")
            lbl.setStyleSheet(f"""
                QLabel {{
                    background: #141216;
                    color: {BRAND_COLOR};
                    border: 1px dashed #c5a059;
                    border-radius: 6px;
                    padding: 12px;
                    font-weight: bold;
                }}
                QLabel:hover {{
                    border-color: {BRAND_COLOR};
                    background: #221d14;
                }}
            """)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            lbl.installEventFilter(self)
            setattr(self, attr, lbl)
            hk_grid.addWidget(lbl, i // 2, i % 2)

        p1_layout.addLayout(hk_grid)
        p1_layout.addStretch()
        self.stacked.addWidget(p1)

        # Tab 2: FILTERS
        p2 = QWidget()
        p2_layout = QVBoxLayout(p2)
        p2_layout.setContentsMargins(20, 20, 20, 20)

        p2_title = QLabel("⚙️ FILTERS")
        p2_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p2_title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        p2_layout.addWidget(p2_title)

        for label, var in [("Freeze Filter:", "freeze_filter"), ("Tele Filter:", "tele_filter")]:
            row = QHBoxLayout()
            row.addWidget(QLabel(label))
            combo = QComboBox()
            combo.addItems(["Gốc", "V1"])
            combo.setStyleSheet(f"""
                QComboBox {{
                    background: #141216; color: {BRAND_COLOR};
                    border: 1px solid #c5a059; border-radius: 6px;
                    padding: 6px;
                }}
            """)
            combo.currentIndexChanged.connect(lambda idx, v=var: self.change_filter(v, idx))
            row.addWidget(combo)
            p2_layout.addLayout(row)

        p2_layout.addStretch()
        self.stacked.addWidget(p2)

        # Tab 3: AUDIO
        p3 = QWidget()
        p3_layout = QVBoxLayout(p3)
        p3_layout.setContentsMargins(20, 20, 20, 20)

        p3_title = QLabel("🎵 AUDIO")
        p3_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p3_title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        p3_layout.addWidget(p3_title)

        self.btn_sound = QPushButton("🔊 SOUND: ON")
        self.btn_sound.setFixedHeight(40)
        self.btn_sound.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sound.setStyleSheet(f"""
            QPushButton {{
                background: #141216;
                color: {BRAND_COLOR};
                border: 1px solid #c5a059;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #221d14;
                border-color: {BRAND_COLOR};
            }}
        """)
        self.btn_sound.clicked.connect(self.toggle_sound)
        p3_layout.addWidget(self.btn_sound)

        self.btn_overlay = QPushButton("🖥️ OVERLAY: ON")
        self.btn_overlay.setFixedHeight(40)
        self.btn_overlay.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_overlay.setStyleSheet(f"""
            QPushButton {{
                background: #141216;
                color: {BRAND_COLOR};
                border: 1px solid #c5a059;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #221d14;
                border-color: {BRAND_COLOR};
            }}
        """)
        self.btn_overlay.clicked.connect(self.toggle_overlay)
        p3_layout.addWidget(self.btn_overlay)

        p3_layout.addStretch()
        self.stacked.addWidget(p3)

        # Tab 4: ABOUT
        p4 = QWidget()
        p4_layout = QVBoxLayout(p4)
        p4_layout.setContentsMargins(20, 20, 20, 20)

        p4_title = QLabel("📖 ABOUT")
        p4_title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        p4_title.setStyleSheet(f"color: {BRAND_COLOR}; border: none;")
        p4_layout.addWidget(p4_title)

        about_text = QLabel("""
        <b>⚡ PHEDEV FAKELAG SYSTEM ⚡</b><br><br>
        <b>Chế độ:</b><br>
        • ⚡ TELE — Dịch chuyển vị trí<br>
        • 🧊 FREEZE — Đóng băng đối thủ<br>
        • 👻 GHOST — Tàng hình<br>
        • 🎯 AIMLAG — Lag khi ngắm bắn<br><br>
        <b>Hotkeys:</b><br>
        • Bấm vào label để đổi phím tắt<br>
        • F10 để thoát<br><br>
        <b>© 2026 Phedev Team</b>
        """)
        about_text.setOpenExternalLinks(True)
        about_text.setWordWrap(True)
        about_text.setStyleSheet("color: #e6c687; font-size: 11px; border: none; line-height: 1.6;")
        p4_layout.addWidget(about_text)

        p4_layout.addStretch()
        self.stacked.addWidget(p4)

        body_layout.addWidget(self.stacked)
        main_layout.addWidget(body)

        # ===== FOOTER =====
        footer = QFrame()
        footer.setFixedHeight(36)
        footer.setStyleSheet(f"""
            QFrame {{
                background: #121015;
                border: 1px solid {BRAND_COLOR};
                border-radius: 8px;
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(10, 0, 15, 0)

        status = QLabel("⚡ PHEDEV SYSTEM")
        status.setStyleSheet(f"color: {BRAND_COLOR}; font-size: 10px; font-weight: bold; border: none;")
        footer_layout.addWidget(status)

        footer_layout.addStretch()

        self.status_label = QLabel("Tele: OFF | Freeze: OFF | Ghost: OFF")
        self.status_label.setStyleSheet("color: #c5a059; font-size: 10px; font-weight: bold; border: none;")
        footer_layout.addWidget(self.status_label)

        main_layout.addWidget(footer)

        # ===== SIGNALS =====
        signals.update_overlay.connect(self.update_status)
        signals.hotkey_pressed.connect(self.handle_hotkey)
        signals.toggle_menu.connect(self.toggle_menu)

        # ===== TRAY =====
        self.tray = QSystemTrayIcon(QIcon(resource_path('Logo.ico')), self)
        self.tray.setToolTip('PHEDEV FAKELAG')
        tray_menu = QMenu()
        tray_menu.addAction('Hiện/Ẩn').triggered.connect(self.toggle_menu)
        tray_menu.addAction('Thoát').triggered.connect(self.close_app)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(lambda r: self.toggle_menu() if r == QSystemTrayIcon.ActivationReason.Trigger else None)
        self.tray.show()

        # ===== TIMER =====
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.finish_hotkey)

        # Load config
        load_config()
        self.update_hotkey_labels()
        self.switch_tab(0)

    def switch_tab(self, idx):
        self.stacked.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            if i == idx:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                    stop:0 {BRAND_COLOR}, stop:1 {BRAND_COLOR_DARK});
                        color: black;
                        font-weight: bold;
                        border: 1px solid #ffe066;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 12px;
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #c5a059;
                        font-weight: bold;
                        border: 1px solid transparent;
                        border-radius: 6px;
                        text-align: left;
                        padding-left: 12px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 215, 0, 0.12);
                        color: #ffd700;
                        border-color: #c5a059;
                    }
                """)

    def toggle_menu(self):
        if self.animating:
            return
        self.animating = True

        if self.menu_open:
            self.anim = QPropertyAnimation(self, b"windowOpacity")
            self.anim.setDuration(200)
            self.anim.setStartValue(1)
            self.anim.setEndValue(0)
            self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim.finished.connect(lambda: self.hide() or setattr(self, 'menu_open', False) or self.btn_toggle.setText("☰ MENU OFF") or setattr(self, 'animating', False))
            self.anim.start()
        else:
            self.setWindowOpacity(0)
            self.show()
            self.raise_()
            self.anim = QPropertyAnimation(self, b"windowOpacity")
            self.anim.setDuration(200)
            self.anim.setStartValue(0)
            self.anim.setEndValue(1)
            self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.anim.finished.connect(lambda: setattr(self, 'menu_open', True) or self.btn_toggle.setText("☰ MENU ON") or setattr(self, 'animating', False))
            self.anim.start()

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            if watched == self.hotkey_tele:
                self.set_hotkey('tele')
                return True
            elif watched == self.hotkey_freeze:
                self.set_hotkey('freeze')
                return True
            elif watched == self.hotkey_ghost:
                self.set_hotkey('ghost')
                return True
            elif watched == self.hotkey_menu:
                self.set_hotkey('menu')
                return True
        return super().eventFilter(watched, event)

    def set_hotkey(self, hk_type):
        self.setting_hotkey_type = hk_type
        labels = {
            'tele': self.hotkey_tele,
            'freeze': self.hotkey_freeze,
            'ghost': self.hotkey_ghost,
            'menu': self.hotkey_menu
        }
        if hk_type in labels:
            labels[hk_type].setText(f"{hk_type.upper()}: [Bấm phím...]")
        self.timer.start(5000)
        self.keyboard_hook = keyboard.on_press(self.on_key)

    def on_key(self, event):
        if self.setting_hotkey_type:
            signals.hotkey_pressed.emit(self.setting_hotkey_type, event.name)

    def handle_hotkey(self, hk_type, key):
        if not hk_type:
            return
        hk = HotkeyConfig(key=key, is_valid=True)
        if hk_type == 'tele':
            app_config.tele_hotkey = hk
        elif hk_type == 'freeze':
            app_config.freeze_hotkey = hk
        elif hk_type == 'ghost':
            app_config.ghost_hotkey = hk
        elif hk_type == 'menu':
            app_config.menu_hotkey = hk

        self.timer.stop()
        try:
            keyboard.unhook(self.keyboard_hook)
        except:
            pass
        self.setting_hotkey_type = None
        save_config()
        self.update_hotkey_labels()

    def finish_hotkey(self):
        if self.setting_hotkey_type:
            try:
                keyboard.unhook(self.keyboard_hook)
            except:
                pass
            self.setting_hotkey_type = None
            self.update_hotkey_labels()

    def update_hotkey_labels(self):
        keys = {
            'tele': app_config.tele_hotkey.key.upper() if app_config.tele_hotkey.key else '...',
            'freeze': app_config.freeze_hotkey.key.upper() if app_config.freeze_hotkey.key else '...',
            'ghost': app_config.ghost_hotkey.key.upper() if app_config.ghost_hotkey.key else '...',
            'menu': app_config.menu_hotkey.key.upper() if app_config.menu_hotkey.key else '...'
        }
        self.hotkey_tele.setText(f"TELE: {keys['tele']}")
        self.hotkey_freeze.setText(f"FREEZE: {keys['freeze']}")
        self.hotkey_ghost.setText(f"GHOST: {keys['ghost']}")
        self.hotkey_menu.setText(f"MENU: {keys['menu']}")

    def change_filter(self, var, idx):
        val = 'v1' if idx == 1 else 'goc'
        if var == 'freeze_filter':
            app_config.freeze_filter = val
        else:
            app_config.tele_filter = val
        save_config()
        update_filters()

    def toggle_sound(self):
        global sound_enabled
        sound_enabled = not sound_enabled
        self.btn_sound.setText(f"{'🔊' if sound_enabled else '🔇'} SOUND: {'ON' if sound_enabled else 'OFF'}")

    def toggle_overlay(self):
        global overlay_enabled
        overlay_enabled = not overlay_enabled
        self.btn_overlay.setText(f"🖥️ OVERLAY: {'ON' if overlay_enabled else 'OFF'}")
        if overlay_instance:
            overlay_instance.setVisible(overlay_enabled)

    def toggle_tele_gui(self):
        toggle_tele()
        self.update_btn_style(self.btn_tele, tele_mode)

    def toggle_freeze_gui(self):
        toggle_freeze()
        self.update_btn_style(self.btn_freeze, freeze_mode)

    def toggle_ghost_gui(self):
        toggle_ghost()
        self.update_btn_style(self.btn_ghost, ghost_mode)

    def toggle_aimlag_gui(self):
        global aimlag_enabled
        aimlag_enabled = not aimlag_enabled
        self.update_btn_style(self.btn_aimlag, aimlag_enabled)

    def update_btn_style(self, btn, state):
        if state:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                                stop:0 #11998e, stop:1 #38ef7d);
                    color: black;
                    font-weight: bold;
                    border: 2px solid #38ef7d;
                    border-radius: 6px;
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #141216;
                    color: #c5a059;
                    font-weight: bold;
                    border: 1px solid #554422;
                    border-radius: 6px;
                }}
                QPushButton:hover {{
                    background: rgba(255,215,0,0.1);
                    border-color: {BRAND_COLOR};
                }}
            """)

    def update_status(self, tele, freeze, ghost):
        self.status_label.setText(f"Tele: {'ON' if tele else 'OFF'} | Freeze: {'ON' if freeze else 'OFF'} | Ghost: {'ON' if ghost else 'OFF'}")
        self.update_btn_style(self.btn_tele, tele)
        self.update_btn_style(self.btn_freeze, freeze)
        self.update_btn_style(self.btn_ghost, ghost)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self._dragging:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = False

    def showEvent(self, event):
        super().showEvent(event)
        set_native_window_icon(self.winId())

    def closeEvent(self, event):
        self.close_app()
        event.accept()

    def close_app(self):
        stop_all()

# ==================== OVERLAY ====================
class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry((screen.width() - 280) // 2, 10, 280, 36)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(6)

        self.tele_lbl = QLabel("TELE: OFF")
        self.freeze_lbl = QLabel("FREEZE: OFF")
        self.ghost_lbl = QLabel("GHOST: OFF")

        for lbl in [self.tele_lbl, self.freeze_lbl, self.ghost_lbl]:
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("""
                border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: bold;
                color: #a0a5b5; background: rgba(30,32,38,220); border: 1px solid #4a505e;
            """)
            self.layout.addWidget(lbl)

        signals.update_overlay.connect(self.update_status)

    def update_status(self, tele, freeze, ghost):
        ac = '#38ef7d'
        active_style = f"border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: bold; color: {ac}; background: rgba(20,25,22,220); border: 1px solid {ac};"
        default_style = "border-radius: 4px; padding: 4px 8px; font-size: 10px; font-weight: bold; color: #a0a5b5; background: rgba(30,32,38,220); border: 1px solid #4a505e;"

        self.tele_lbl.setText(f"TELE: {'ON' if tele else 'OFF'}")
        self.freeze_lbl.setText(f"FREEZE: {'ON' if freeze else 'OFF'}")
        self.ghost_lbl.setText(f"GHOST: {'ON' if ghost else 'OFF'}")

        self.tele_lbl.setStyleSheet(active_style if tele else default_style)
        self.freeze_lbl.setStyleSheet(active_style if freeze else default_style)
        self.ghost_lbl.setStyleSheet(active_style if ghost else default_style)

# ==================== HOTKEY LISTENER ====================
class HotkeyListener(QThread):
    def __init__(self):
        super().__init__()
        self._tele = False
        self._freeze = False
        self._ghost = False
        self._menu = False

    def is_emulator_active(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return False
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            return proc.name().lower() in ('hd-player.exe', 'bluestacks.exe', 'ldplayer.exe')
        except:
            return False

    def run(self):
        while running:
            # Menu
            if app_config.menu_hotkey.is_valid:
                try:
                    if keyboard.is_pressed(app_config.menu_hotkey.key) and not self._menu:
                        signals.toggle_menu.emit()
                        self._menu = True
                    elif not keyboard.is_pressed(app_config.menu_hotkey.key):
                        self._menu = False
                except:
                    pass

            if not self.is_emulator_active():
                self.msleep(10)
                continue

            # Tele
            if app_config.tele_hotkey.is_valid:
                try:
                    if keyboard.is_pressed(app_config.tele_hotkey.key) and not self._tele:
                        toggle_tele()
                        self._tele = True
                    elif not keyboard.is_pressed(app_config.tele_hotkey.key):
                        self._tele = False
                except:
                    pass

            # Freeze
            if app_config.freeze_hotkey.is_valid:
                try:
                    if keyboard.is_pressed(app_config.freeze_hotkey.key) and not self._freeze:
                        toggle_freeze()
                        self._freeze = True
                    elif not keyboard.is_pressed(app_config.freeze_hotkey.key):
                        self._freeze = False
                except:
                    pass

            # Ghost
            if app_config.ghost_hotkey.is_valid:
                try:
                    if keyboard.is_pressed(app_config.ghost_hotkey.key) and not self._ghost:
                        toggle_ghost()
                        self._ghost = True
                    elif not keyboard.is_pressed(app_config.ghost_hotkey.key):
                        self._ghost = False
                except:
                    pass

            # Aimlag
            if aimlag_enabled:
                left = (win32api.GetAsyncKeyState(1) & 0x8000) != 0
                if left and not freeze_mode:
                    with lock:
                        freeze_mode = True
                        R_I = True
                        signals.update_overlay.emit(tele_mode, freeze_mode, ghost_mode)
                elif not left and freeze_mode and aimlag_enabled:
                    with lock:
                        freeze_mode = False
                        R_I = False
                        p = list(packet_freeze)
                        packet_freeze.clear()
                        if p:
                            threading.Thread(target=send_packets, args=(p, FILTER_I), daemon=True).start()
                        signals.update_overlay.emit(tele_mode, freeze_mode, ghost_mode)

            self.msleep(10)

# ==================== PACKET FUNCTIONS ====================
def send_packets(packets, filter_str):
    try:
        with pydivert.WinDivert(filter_str, layer=pydivert.Layer.NETWORK) as s:
            for pkt in packets:
                s.send(pydivert.Packet(pkt.raw, pkt.interface, pkt.direction))
    except:
        pass

def toggle_tele():
    global tele_mode, R_O
    with lock:
        tele_mode = not tele_mode
        R_O = tele_mode
        if not tele_mode:
            p = list(packet_tele)
            packet_tele.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_O), daemon=True).start()
    audio.play_on() if tele_mode else audio.play_off()
    signals.update_overlay.emit(tele_mode, freeze_mode, ghost_mode)

def toggle_freeze():
    global freeze_mode, R_I
    with lock:
        freeze_mode = not freeze_mode
        R_I = freeze_mode
        if not freeze_mode:
            p = list(packet_freeze)
            packet_freeze.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_I), daemon=True).start()
    audio.play_on() if freeze_mode else audio.play_off()
    signals.update_overlay.emit(tele_mode, freeze_mode, ghost_mode)

def toggle_ghost():
    global ghost_mode, R_F
    with lock:
        ghost_mode = not ghost_mode
        R_F = ghost_mode
        if not ghost_mode:
            p = list(packet_ghost)
            packet_ghost.clear()
            if p:
                threading.Thread(target=send_packets, args=(p, FILTER_F), daemon=True).start()
    audio.play_on() if ghost_mode else audio.play_off()
    signals.update_overlay.emit(tele_mode, freeze_mode, ghost_mode)

def update_filters():
    global FILTER_O, FILTER_I, FILTER_F
    FILTER_O = '(udp.DstPort >= 10010 and udp.DstPort <= 10020) and udp.PayloadLength >= 43' if app_config.tele_filter == 'v1' else '(udp.DstPort >= 10010 and udp.DstPort <= 10020) and udp.PayloadLength >= 40'
    FILTER_I = 'inbound and udp.SrcPort >= 10000 and udp.SrcPort <= 10099 and udp.PayloadLength >= 20' if app_config.freeze_filter == 'v1' else 'inbound and udp.SrcPort >= 10000 and udp.SrcPort <= 10099 and ip and ip.Protocol == 17 and ip.Length >= 50 and ip.Length <= 1491'
    FILTER_F = 'udp and udp.DstPort >= 10000 and udp.DstPort <= 10099 and ip.Length and udp.PayloadLength >= 54 and udp.PayloadLength <= 63'

def stop_all():
    global running, R_O, R_I, R_F
    running = False
    R_O = R_I = R_F = False
    try:
        keyboard.unhook_all()
    except:
        pass
    try:
        app.quit()
    except:
        pass
    os._exit(0)

def divert(filter_ref, flag_ref, packet_list, cond_ref):
    h = None
    while running:
        if not flag_ref():
            if h:
                try:
                    h.close()
                except:
                    pass
                h = None
            time.sleep(0.01)
            continue

        if h is None:
            try:
                f = filter_ref() if callable(filter_ref) else filter_ref
                h = pydivert.WinDivert(f)
                h.open()
            except:
                time.sleep(0.1)
                continue

        try:
            for pkt in h:
                if not running or not flag_ref():
                    break
                with lock:
                    if cond_ref():
                        packet_list.append(pkt)
                    else:
                        h.send(pkt)
        except:
            if h:
                try:
                    h.close()
                except:
                    pass
                h = None

# ==================== MAIN ====================
if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        load_config()
        update_filters()

        main_window_instance = MainWindow()
        main_window_instance.show()

        overlay_instance = OverlayWindow()
        overlay_instance.show()

        # Divert threads
        threading.Thread(target=divert, args=(lambda: FILTER_O, lambda: R_O, packet_tele, lambda: tele_mode), daemon=True).start()
        threading.Thread(target=divert, args=(lambda: FILTER_I, lambda: R_I, packet_freeze, lambda: freeze_mode), daemon=True).start()
        threading.Thread(target=divert, args=(lambda: FILTER_F, lambda: R_F, packet_ghost, lambda: ghost_mode), daemon=True).start()

        # Hotkey listener
        hotkey_listener_thread = HotkeyListener()
        hotkey_listener_thread.start()

        keyboard.add_hotkey('f10', stop_all, suppress=True)

        sys.exit(app.exec())
    except Exception as e:
        log_error(str(e))
        sys.exit(1)