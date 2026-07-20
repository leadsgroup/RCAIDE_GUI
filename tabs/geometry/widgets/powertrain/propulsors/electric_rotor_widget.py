# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/electric_rotor_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import (
    BasePropulsorWidget,
    ESC_FIELDS,
    MOTOR_FIELDS,
    ROTOR_FIELDS,
)


class ElectricRotorWidget(BasePropulsorWidget):
    # Electric rotors combine motor, rotor, and ESC subcomponents.
    propulsor_type = "Electric Rotor"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Electric_Rotor
    subcomponent_classes = {
        "motor": RCAIDE.Library.Components.Powertrain.Converters.DC_Motor,
        "rotor": RCAIDE.Library.Components.Powertrain.Converters.Rotor,
        "electronic_speed_controller": RCAIDE.Library.Components.Powertrain.Modulators.Electronic_Speed_Controller,
    }
    type_fields = MOTOR_FIELDS + ROTOR_FIELDS + ESC_FIELDS
