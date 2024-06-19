from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar, Units
from widgets import DataEntryWidget
from tabs.analysis.widgets import AnalysisWidget

import RCAIDE
import numpy as np


class NoiseWidget(QWidget, AnalysisWidget):
    data_units_labels = [
        [
            ("Flyover", Units.Boolean),
            ("Approach", Units.Boolean),
            ("Sideline", Units.Boolean),
            ("Sideline X Position", Units.Length),
            ("Print Noise Output", Units.Boolean),
            ("Mean Sea Level Altitude", Units.Boolean),
            ("Aircraft Departure Location", Units.Position),
            ("Aircraft Destination Location", Units.Position),
            ("Microphone X Resolution", Units.Count),
            ("Microphone Y Resolution", Units.Count),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length),
            ("Microphone Max X", Units.Length),
            ("Microphone Min Y", Units.Length),
            ("Microphone Max Y", Units.Length),
            ("Noise Hemisphere", Units.Boolean),
            ("Noise Hemisphere Radius", Units.Length),
            ("Noise Hemisphere Microphone Resolution", Units.Count),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),
        ],
        [
            ("Sideline X Position", Units.Length),
            ("Print Noise Output", Units.Boolean),
            ("Mean Sea Level Altitude", Units.Boolean),
            ("Aircraft Departure Location", Units.Position),
            ("Aircraft Destination Location", Units.Position),
            ("Microphone X Resolution", Units.Count),
            ("Microphone Y Resolution", Units.Count),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length),
            ("Microphone Max X", Units.Length),
            ("Microphone Min Y", Units.Length),
            ("Microphone Max Y", Units.Length),
            ("Noise Hemisphere", Units.Boolean),
            ("Noise Hemisphere Radius", Units.Length),
            ("Noise Hemisphere Microphone Resolution", Units.Count),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),]
    ]
    analyses = ["Correlation Buildup", "Frequency Domain Buildup"]

    def __init__(self):
        super(NoiseWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Noise</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(self.analyses)
        self.analysis_selector.currentIndexChanged.connect(self.on_analysis_change)
        self.main_layout.addWidget(self.analysis_selector)
        
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[0])
        self.main_layout.addWidget(self.data_entry_widget)

        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def on_analysis_change(self, index):
        print("Index changed to", index)

        assert self.main_layout is not None

        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[index])
        # self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.insertWidget(
            self.main_layout.count() - 1, self.data_entry_widget)
    
    def create_analysis(self):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            noise = RCAIDE.Framework.Analyses.Noise.Correlation_Buildup()
        else:
            noise = RCAIDE.Framework.Analyses.Noise.Frequency_Domain_Buildup()
        
        settings = noise.settings
        values_si = self.data_entry_widget.get_values_si()
        
        if analysis_num == 0:
            settings.flyover = values_si["Flyover"][0]
            settings.approach = values_si["Approach"][0]
            settings.sideline = values_si["Sideline"][0]
        
        settings.sideline_x_position = values_si["Sideline X Position"][0]
        settings.print_noise_output = values_si["Print Noise Output"][0]
        settings.mean_sea_level_altitude = values_si["Mean Sea Level Altitude"][0]
        settings.aircraft_departure_location = values_si["Aircraft Departure Location"][0]
        settings.aircraft_destination_location = values_si["Aircraft Destination Location"][0]
        settings.microphone_x_resolution = values_si["Microphone X Resolution"][0]
        settings.microphone_y_resolution = values_si["Microphone Y Resolution"][0]
        settings.microphone_min_x = values_si["Microphone Min X"][0]
        settings.microphone_max_x = values_si["Microphone Max X"][0]
        settings.microphone_min_y = values_si["Microphone Min Y"][0]
        settings.microphone_max_y = values_si["Microphone Max Y"][0]
        settings.noise_hemisphere = values_si["Noise Hemisphere"][0]
        settings.noise_hemisphere_radius = values_si["Noise Hemisphere Radius"][0]
        settings.noise_hemisphere_microphone_resolution = values_si["Noise Hemisphere Microphone Resolution"][0]
        
        phi_upper_bound = values_si["Noise Hemisphere Phi Upper Bound"][0]
        phi_lower_bound = values_si["Noise Hemisphere Phi Lower Bound"][0]
        
        settings.noise_hemisphere_phi_angle_bounds = np.array([phi_lower_bound, phi_upper_bound])
        
        theta_upper_bound = values_si["Noise Hemisphere Theta Upper Bound"][0]
        theta_lower_bound = values_si["Noise Hemisphere Theta Lower Bound"][0]
        
        settings.noise_hemisphere_theta_angle_bounds = np.array([theta_lower_bound, theta_upper_bound])
        
        return noise
        
