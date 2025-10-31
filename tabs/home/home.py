from PyQt6.QtCore import QSize, Qt, QPropertyAnimation, QEasingCurve, QTimer, QUrl
from PyQt6.QtGui import QPixmap, QDesktopServices
from PyQt6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QPushButton, QSizePolicy,
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QGraphicsOpacityEffect
)
from PyQt6.QtWidgets import QApplication
from utilities import create_line_bar
from tabs import TabWidget
from widgets.image_widget import ImageWidget
from PyQt6.QtCore import qInstallMessageHandler

def suppress_qt_warnings(mode, context, message):
    if "Unknown property" in message:  # hides CSS warnings (Qt Does not support CSS propertieis within Load/Scratch Aircraft (RH column) - Harmless warning, functionality not affected)
        return
    print(message)  

qInstallMessageHandler(suppress_qt_warnings)

BANNER_HEIGHT = 320
VERTICAL_FOCUS = 0.3

class BannerImage(QLabel):
    def __init__(self, path: str, height: int = BANNER_HEIGHT):
        super().__init__()
        self._pix = QPixmap(path)
        self._fixed_h = height
        self.setFixedHeight(height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

    def resizeEvent(self, e):
        if not self._pix.isNull():
            scaled = self._pix.scaled(
                self.width(), self._fixed_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            y_offset = int(max(0, scaled.height() - self._fixed_h) * VERTICAL_FOCUS)
            cropped = scaled.copy(0, y_offset, self.width(), self._fixed_h)
            self.setPixmap(cropped)
        super().resizeEvent(e)

class HomeWidget(TabWidget):
    def __init__(self):
        super(HomeWidget, self).__init__()

        # Logo Screen
        self.splash_label = QLabel()
        self.splash_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.splash_label.setStyleSheet("background-color: #02101d;")
        pixmap = QPixmap("app_data/images/logo.png")
        self.splash_label.setPixmap(
            pixmap.scaled(260, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        )

        self.splash_opacity = QGraphicsOpacityEffect()
        self.splash_label.setGraphicsEffect(self.splash_opacity)

        self.fade_in = QPropertyAnimation(self.splash_opacity, b"opacity")
        self.fade_in.setDuration(1800)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.fade_out = QPropertyAnimation(self.splash_opacity, b"opacity")
        self.fade_out.setDuration(1300)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_out.finished.connect(self._show_homepage_after_splash)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.main_widget = QWidget()
        self.main_widget.setVisible(False)
        self.layout.addWidget(self.splash_label)
        self.layout.addWidget(self.main_widget)

        self._build_main_ui()
        QTimer.singleShot(200, self._start_splash)

    def _start_splash(self):
        self.fade_in.start()
        self.fade_in.finished.connect(lambda: QTimer.singleShot(800, self.fade_out.start))

    def _show_homepage_after_splash(self):
        self.splash_label.hide()
        self.main_widget.setVisible(True)
        home_opacity = QGraphicsOpacityEffect()
        self.main_widget.setGraphicsEffect(home_opacity)
        home_opacity.setOpacity(0.0)

        self.home_fade_in = QPropertyAnimation(home_opacity, b"opacity")
        self.home_fade_in.setDuration(1000)
        self.home_fade_in.setStartValue(0.0)
        self.home_fade_in.setEndValue(1.0)
        self.home_fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.home_fade_in.finished.connect(lambda: self.main_widget.setGraphicsEffect(None))
        self.home_fade_in.start()
        self.play_fade_sequence()
        self.adjust_for_screen(force=True)

    # Main UI
    def _build_main_ui(self):
        base_layout = QVBoxLayout(self.main_widget)
        base_layout.setSpacing(0)
        base_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_layout = QGridLayout()
        website_btn = QPushButton("Website")
        github_btn = QPushButton("GitHub")
        docs_btn = QPushButton("Documentation")
        contribute_btn = QPushButton("Contribute")
        contact_btn = QPushButton("Contact")

        header_layout.addWidget(website_btn, 0, 0)
        header_layout.addWidget(github_btn, 0, 1)
        header_layout.addWidget(docs_btn, 0, 2)
        header_layout.addWidget(contribute_btn, 0, 3)
        header_layout.addWidget(contact_btn, 0, 4)
        header_layout.setContentsMargins(12, 12, 12, 0)
        header_layout.setSpacing(10)

        # Tab URLs
        website_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.rcaide.leadsresearchgroup.com")))
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/leadsgroup")))
        docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.docs.rcaide.leadsresearchgroup.com")))
        contribute_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.rcaide.leadsresearchgroup.com/community")))
        contact_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://www.rcaide.leadsresearchgroup.com/community")))

        # Banner Section
        banner_container = QFrame()
        banner_container.setFixedHeight(BANNER_HEIGHT)
        banner_container.setStyleSheet("border:none; background:transparent;")
        self.banner = BannerImage("app_data/images/background.jpg", height=BANNER_HEIGHT)

        self.rcaide_label = QLabel("RCAIDE")
        self.leads_label = QLabel("by L.E.A.D.S (UIUC)")
        for lbl in (self.rcaide_label, self.leads_label):
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.rcaide_label.setStyleSheet("color:#00BFFF; font-size:46px; font-weight:800; letter-spacing:2px;")
        self.leads_label.setStyleSheet("color:white; font-size:20px; font-weight:500;")

        overlay_layout = QVBoxLayout()
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        overlay_layout.addWidget(self.rcaide_label)
        overlay_layout.addWidget(self.leads_label)

        overlay_widget = QWidget()
        overlay_widget.setLayout(overlay_layout)
        overlay_widget.setStyleSheet("background:transparent;")

        banner_layout = QVBoxLayout(banner_container)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        banner_layout.addWidget(self.banner)
        banner_layout.addWidget(overlay_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        base_layout.addLayout(header_layout)
        base_layout.addWidget(banner_container)
        base_layout.addWidget(create_line_bar())

        # Body Background
        body_bg = QFrame()
        body_bg.setObjectName("bodyBg")
        body_bg.setStyleSheet("""
#bodyBg {
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #0B1D2C, stop:1 #051018);
    border-top: 1px solid #11293C;
}
""")
        body_layout = QHBoxLayout(body_bg)
        body_layout.setContentsMargins(60, 40, 100, 70)
        body_layout.setSpacing(30)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # Left Column: How To Use GUI Flowchart
        self.flowchart_frame = QFrame()
        self.flowchart_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(20, 40, 60, 0.7),
                stop:1 rgba(10, 20, 30, 0.7));
            border-radius: 16px;
            border: 1px solid rgba(0, 170, 255, 0.3);
        """)
        flowchart_layout = QVBoxLayout(self.flowchart_frame)
        flowchart_layout.setContentsMargins(0, 0, 0, 0)
        flowchart_layout.setSpacing(0)
        flowchart_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Load High-Resolution Flowchart Image
        original_pix = QPixmap("app_data/images/flowchart.png")
        if not original_pix.isNull():
            screen = QApplication.primaryScreen()
            dpr = screen.devicePixelRatio() if screen else 1.0
            highres_pix = original_pix.scaled(
                int(620 * dpr),
                int(320 * dpr),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            highres_pix.setDevicePixelRatio(dpr)
        else:
            highres_pix = original_pix

        # Center Flowchart Within Container
        self.flowchart_image = QLabel()
        self.flowchart_image.setPixmap(highres_pix)
        self.flowchart_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.flowchart_image.setFixedSize(620, 320)
        self.flowchart_image.setStyleSheet("border:none; background:transparent;")

        flowchart_layout.addStretch(1)
        flowchart_layout.addWidget(self.flowchart_image, alignment=Qt.AlignmentFlag.AlignCenter)
        flowchart_layout.addStretch(1)
        
        # Right Column: Load Aircraft / Mission Or Start From Scratch
        self.mission_frame = QFrame()
        self.mission_frame.setObjectName("missionPanel")
        self.mission_frame.setStyleSheet("""
#missionPanel {
    background-color: rgba(20, 40, 60, 0.55);
    border: 1px solid rgba(0, 170, 255, 0.35);
    border-radius: 20px;
    box-shadow: 0px 0px 25px rgba(0, 170, 255, 0.15);
    backdrop-filter: blur(14px);
}
QLabel {
    color: #ffffff;
    font-size: 22px;
    font-weight: bold;
}
QComboBox {
    background-color: rgba(255,255,255,0.1);
    color: white;
    font-size: 16px;
    padding: 6px;
    border-radius: 8px;
}
QPushButton {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #0099FF, stop:1 #0066CC);
    color: white;
    font-size: 18px;
    font-weight: 600;
    border-radius: 12px;
    padding: 8px 22px;
    border: 1px solid rgba(0,170,255,0.35);
}
QPushButton:hover {
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #33BBFF, stop:1 #0088FF);
    box-shadow: 0 0 15px rgba(0,170,255,0.3);
}
""")
        mission_layout = QVBoxLayout(self.mission_frame)
        mission_layout.setContentsMargins(45, 45, 45, 45)
        mission_layout.setSpacing(30)
        mission_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title_container = QVBoxLayout()
        title_container.setSpacing(10)
        title_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mission_label = QLabel("Get Started")
        mission_label.setFixedHeight(40)
        mission_label.setStyleSheet("""
            color: #00BFFF;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 1px;
            padding-top: 6px;
            padding-bottom: 6px;
        """)

        underline = QFrame()
        underline.setFixedHeight(5)
        underline.setFixedWidth(180)
        underline.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.25 rgba(0,150,255,0.35),
                    stop:0.5 rgba(0,220,255,0.95),
                    stop:0.75 rgba(0,150,255,0.35),
                    stop:1 transparent);
                border-radius: 2px;
                margin-top: 6px;
            }
        """)

        title_container.addWidget(mission_label, alignment=Qt.AlignmentFlag.AlignCenter)
        title_container.addWidget(underline, alignment=Qt.AlignmentFlag.AlignCenter)
        mission_layout.addLayout(title_container)

        subtitle = QLabel("Quickly set up or define your aircraft mission.")
        subtitle.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 14px; font-weight: 400;")
        mission_layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Buttons
        load_row = QHBoxLayout()
        load_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        load_row.setSpacing(15)

        load_btn = QPushButton("Load Aircraft and Mission")
        load_btn.setMinimumWidth(230)
        load_btn.setFixedHeight(42)

        aircraft_selector = QComboBox()
        aircraft_selector.addItems(["Boeing 737-800", "Airbus A321neo", "ATR-72", "Dash-8 Q400"])
        aircraft_selector.setFixedWidth(180)

        load_row.addWidget(load_btn)
        load_row.addWidget(aircraft_selector)
        mission_layout.addLayout(load_row)

        divider = QFrame()
        divider.setFixedHeight(2)
        divider.setStyleSheet("""
            QFrame {
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.3 rgba(0,180,255,0.25),
                    stop:0.5 rgba(0,255,255,0.8),
                    stop:0.7 rgba(0,180,255,0.25),
                    stop:1 transparent);
                border-radius: 1px;
                margin-top: 18px;
                margin-bottom: 10px;
            }
        """)
        mission_layout.addWidget(divider)

        scratch_btn = QPushButton("Start from Scratch")
        scratch_btn.setMinimumWidth(250)
        scratch_btn.setFixedHeight(42)

        # Move the button slightly up under the divider
        mission_layout.addSpacing(-10)  
        scratch_container = QVBoxLayout()
        scratch_container.setContentsMargins(0, 0, 0, 0)
        scratch_container.addWidget(scratch_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        mission_layout.addLayout(scratch_container)

        # Sizes
        self._normal_flowchart_size = QSize(620, 320)
        self._normal_mission_size = QSize(550, 310)
        self._fullscreen_scale = 1.55

        self.flowchart_frame.setFixedSize(self._normal_flowchart_size)
        self.mission_frame.setFixedSize(self._normal_mission_size)

        body_layout.addWidget(self.flowchart_frame)
        body_layout.addWidget(self.mission_frame)
        base_layout.addWidget(body_bg)

        # Footer
        footer = QFrame()
        footer.setFixedHeight(12)
        footer.setStyleSheet("background-color: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #004080, stop:1 #001A33);")
        base_layout.addWidget(footer)

        self.setup_fade_animations()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_for_screen()

    def adjust_for_screen(self, force=False):
        window = self.window()
        if not window:
            return
        is_fullscreen = window.isFullScreen()
        scale = self._fullscreen_scale if is_fullscreen else 1.0

        flow_w = int(self._normal_flowchart_size.width() * scale)
        flow_h = int(self._normal_flowchart_size.height() * scale)
        mission_w = int(self._normal_mission_size.width() * scale)
        mission_h = int(self._normal_mission_size.height() * scale)

        self.flowchart_frame.setFixedSize(flow_w, flow_h)
        self.mission_frame.setFixedSize(mission_w, mission_h)
        self.updateGeometry()
        self.repaint()

    def setup_fade_animations(self):
        def make_fade(widget, duration=2000):
            effect = QGraphicsOpacityEffect()
            widget.setGraphicsEffect(effect)
            anim = QPropertyAnimation(effect, b"opacity")
            anim.setDuration(duration)
            anim.setStartValue(0)
            anim.setEndValue(1)
            anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
            return effect, anim

        self.banner_effect, self.banner_anim = make_fade(self.banner, 2000)
        self.flowchart_effect, self.flow_anim = make_fade(self.flowchart_frame, 2000)
        self.mission_effect, self.mission_anim = make_fade(self.mission_frame, 2000)
        self.rcaide_effect, self.rcaide_anim = make_fade(self.rcaide_label, 1800)
        self.leads_effect, self.leads_anim = make_fade(self.leads_label, 1800)

    def play_fade_sequence(self):
        def start_group1():
            self.banner_anim.start()
            self.flow_anim.start()
            self.mission_anim.start()
            QTimer.singleShot(1200, start_group2)

        def start_group2():
            self.rcaide_label.setVisible(True)
            self.leads_label.setVisible(True)
            self.rcaide_anim.start()
            self.leads_anim.start()
            self.rcaide_anim.finished.connect(lambda: self.rcaide_label.setGraphicsEffect(None))
            self.leads_anim.finished.connect(lambda: self.leads_label.setGraphicsEffect(None))

        self.rcaide_label.setVisible(False)
        self.leads_label.setVisible(False)
        QTimer.singleShot(100, start_group1)

def get_widget() -> QWidget:
    return HomeWidget()