# RCAIDE_GUI/tabs/analysis/widgets/atmosphere_widget.py

# Created: May 2023, M. Clarke
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------
import RCAIDE
from tabs.analysis.widgets.analysis_data_widget import ComboBoxAnalysisWidget

# ------------------------------------------------------------------------------
# Atmosphere Widget
# ------------------------------------------------------------------------------
class AtmosphereWidget(ComboBoxAnalysisWidget):
    title   = "Atmosphere"
    options = ["1976 US Standard Atmosphere", "Constant Temperature"]

    def create_analysis(self, _vehicle):
        if self.analysis_selector.currentIndex() == 0:
            return RCAIDE.Framework.Analyses.Atmospheric.US_Standard_1976()
        return RCAIDE.Framework.Analyses.Atmospheric.Constant_Temperature()
