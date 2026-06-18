# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/constant_speed_ice_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import (
    BasePropulsorWidget,
    ENGINE_FIELDS,
    PROPELLER_FIELDS,
)


class ConstantSpeedICEWidget(BasePropulsorWidget):
    # Constant-speed ICE propulsors share the engine + propeller editor fields.
    propulsor_type = "Constant Speed Internal Combustion Engine"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Constant_Speed_Internal_Combustion_Engine
    subcomponent_classes = {
        "engine": RCAIDE.Library.Components.Powertrain.Converters.Engine,
        "propeller": RCAIDE.Library.Components.Powertrain.Converters.Propeller,
    }
    type_fields = ENGINE_FIELDS + PROPELLER_FIELDS
