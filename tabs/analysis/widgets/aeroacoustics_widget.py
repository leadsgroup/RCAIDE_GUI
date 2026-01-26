from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QComboBox

from utilities import create_line_bar, Units, set_data
from widgets import DataEntryWidget
from tabs.analysis.widgets import AnalysisDataWidget

import RCAIDE

import json


class AeroacousticsWidget(AnalysisDataWidget):
    def __init__(self):
        super(AeroacousticsWidget, self).__init__()
        self.main_layout = QVBoxLayout()

        self.main_layout.addWidget(QLabel("<b>Acoustics</b>"))
        self.main_layout.addWidget(create_line_bar())

        self.analysis_selector = QComboBox()
        self.analysis_selector.addItems(self.analyses)
        self.analysis_selector.currentIndexChanged.connect(
            self.on_analysis_change)
        self.main_layout.addWidget(self.analysis_selector)

        self.data_entry_widget = DataEntryWidget(self.data_units_labels[0])
        self.main_layout.addWidget(self.data_entry_widget)

        with open("app_data/defaults/aeroacoustics_analysis.json", "r") as defaults:
            self.defaults = json.load(defaults)

        self.data_entry_widget.load_data(self.defaults[0])
        self.main_layout.addWidget(create_line_bar())
        self.setLayout(self.main_layout)

    def on_analysis_change(self, index): 
        assert self.main_layout is not None

        self.main_layout.removeWidget(self.data_entry_widget)
        self.data_entry_widget = DataEntryWidget(self.data_units_labels[index])
        self.data_entry_widget.load_data(self.defaults[index])
        # self.main_layout.addWidget(self.data_entry_widget)
        self.main_layout.insertWidget(
            self.main_layout.count() - 1, self.data_entry_widget)

    def create_analysis(self, vehicle):
        analysis_num = self.analysis_selector.currentIndex()
        if analysis_num == 0:
            aeroacoustics = RCAIDE.Framework.Analyses.Aeroacoustics.Semi_Empirical()
        else:
            aeroacoustics = RCAIDE.Framework.Analyses.Aeroacoustics.Physics_Based()

        settings  = aeroacoustics.settings
        values_si = self.data_entry_widget.get_values_si()

        for data_unit_label in self.data_units_labels[analysis_num]:
            if len(data_unit_label) < 3:
                continue

            rcaide_label = data_unit_label[-1]
            user_label = data_unit_label[0]
            set_data(settings, rcaide_label, values_si[user_label])

        phi_upper_bound = values_si["Noise Hemisphere Phi Upper Bound"][0]
        phi_lower_bound = values_si["Noise Hemisphere Phi Lower Bound"][0]

        settings.noise_hemisphere_phi_angle_bounds = [
            phi_lower_bound, phi_upper_bound]

        theta_upper_bound = values_si["Noise Hemisphere Theta Upper Bound"][0]
        theta_lower_bound = values_si["Noise Hemisphere Theta Lower Bound"][0]

        settings.noise_hemisphere_theta_angle_bounds = [
            theta_lower_bound, theta_upper_bound]
 
        return aeroacoustics
    
    def get_values(self):
        data = self.data_entry_widget.get_values()
        data["analysis_num"] = self.analysis_selector.currentIndex()
        return data
    
    def load_values(self, values):
        super().load_values(values)
        self.analysis_selector.setCurrentIndex(values["analysis_num"])
        self.on_analysis_change(values["analysis_num"])
        self.data_entry_widget.load_data(values)

    data_units_labels = [
        [
            ("Print Noise Output", Units.Boolean, "print_noise_output"),
            ("Mean Sea Level Altitude", Units.Boolean, "mean_sea_level_altitude"),
            ("Aircraft Departure Location", Units.Position,
             "aircraft_departure_location"),
            ("Aircraft Destination Location", Units.Position,
             "aircraft_destination_location"),
            ("Microphone X Resolution", Units.Count, "microphone_x_resolution"),
            ("Microphone Y Resolution", Units.Count, "microphone_y_resolution"),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length, "microphone_min_x"),
            ("Microphone Max X", Units.Length, "microphone_max_x"),
            ("Microphone Min Y", Units.Length, "microphone_min_y"),
            ("Microphone Max Y", Units.Length, "microphone_max_y"),
            ("Noise Hemisphere", Units.Boolean, "noise_hemisphere"),
            ("Noise Hemisphere Radius", Units.Length, "noise_hemisphere_radius"),
            ("Noise Hemisphere Microphone Resolution", Units.Count,
             "noise_hemisphere_microphone_resolution"),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),
        ],
        [
            ("Flyover", Units.Boolean, "flyover"),
            ("Approach", Units.Boolean, "approach"),
            ("Sideline", Units.Boolean, "sideline"),
            ("Sideline X Position", Units.Boolean, "sideline_x_position"),
            ("Print Noise Output", Units.Boolean, "print_noise_output"),
            ("Mean Sea Level Altitude", Units.Boolean, "mean_sea_level_altitude"),
            ("Aircraft Departure Location", Units.Position,
             "aircraft_departure_location"),
            ("Aircraft Destination Location", Units.Position,
             "aircraft_destination_location"),
            ("Microphone X Resolution", Units.Count, "microphone_x_resolution"),
            ("Microphone Y Resolution", Units.Count, "microphone_y_resolution"),
            # TODO ("Microphone X Stencil", Units.Length),
            # TODO ("Microphone Y Stencil", Units.Length),
            ("Microphone Min X", Units.Length, "microphone_min_x"),
            ("Microphone Max X", Units.Length, "microphone_max_x"),
            ("Microphone Min Y", Units.Length, "microphone_min_y"),
            ("Microphone Max Y", Units.Length, "microphone_max_y"),
            ("Noise Hemisphere", Units.Boolean, "noise_hemisphere"),
            ("Noise Hemisphere Radius", Units.Length, "noise_hemisphere_radius"),
            ("Noise Hemisphere Microphone Resolution", Units.Count,
             "noise_hemisphere_microphone_resolution"),
            ("Noise Hemisphere Phi Upper Bound", Units.Angle),
            ("Noise Hemisphere Phi Lower Bound", Units.Angle),
            ("Noise Hemisphere Theta Upper Bound", Units.Angle),
            ("Noise Hemisphere Theta Lower Bound", Units.Angle),
        ]
    ]
    analyses = ["Semi Empirical", "Physics-Based"]
