# RCAIDE_GUI/tabs/analysis/widgets/analysis_data_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox
from utilities import create_line_bar

# ------------------------------------------------------------------------------
# Analysis Data Widget  (base)
# ------------------------------------------------------------------------------
class AnalysisDataWidget(QWidget):
    """
    Base class for all analysis panel widgets.

    Subclasses set `title` as a class attribute; the header label and first
    divider are rendered automatically by this __init__.  Subclasses add their
    own content to self.main_layout and call self.setLayout(self.main_layout).
    """
    title = ""

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        if self.title:
            self.main_layout.addWidget(QLabel(f"<b>{self.title}</b>"))
            self.main_layout.addWidget(create_line_bar())

    def create_analysis(self, vehicle: RCAIDE.Vehicle):
        return RCAIDE.Framework.Analyses.Analysis()

    def get_values(self):
        return {}

    def load_values(self, values):
        self.setVisible(values["enabled"])


# ------------------------------------------------------------------------------
# Combo Box Analysis Widget  (intermediate base)
# ------------------------------------------------------------------------------
class ComboBoxAnalysisWidget(AnalysisDataWidget):
    """
    Base for analysis widgets whose only input is a combo-box selector.

    Subclasses define `title` and `options` as class attributes and implement
    `create_analysis`.  get_values / load_values are handled here.
    """
    options = []

    def __init__(self):
        super().__init__()
        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(self.options)
        self.main_layout.addWidget(self.analysis_selector)
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def get_values(self):
        return {"analysis_num": self.analysis_selector.currentIndex()}

    def load_values(self, values):
        super().load_values(values)
        self.analysis_selector.setCurrentIndex(values.get("analysis_num", 0))
