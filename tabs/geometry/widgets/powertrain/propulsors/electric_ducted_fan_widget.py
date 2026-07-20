# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/electric_ducted_fan_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import (
    BasePropulsorWidget,
    DUCTED_FAN_FIELDS,
    ESC_FIELDS,
    MOTOR_FIELDS,
)


class ElectricDuctedFanWidget(BasePropulsorWidget):
    # Electric ducted fans combine motor, ducted fan, and ESC subcomponents.
    propulsor_type = "Electric Ducted Fan"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Electric_Ducted_Fan
    subcomponent_classes = {
        "motor": RCAIDE.Library.Components.Powertrain.Converters.DC_Motor,
        "ducted_fan": RCAIDE.Library.Components.Powertrain.Converters.Ducted_Fan,
        "electronic_speed_controller": RCAIDE.Library.Components.Powertrain.Modulators.Electronic_Speed_Controller,
    }
    type_fields = MOTOR_FIELDS + DUCTED_FAN_FIELDS + ESC_FIELDS
