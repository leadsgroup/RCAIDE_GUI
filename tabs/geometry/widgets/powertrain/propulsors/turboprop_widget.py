# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/turboprop_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import (
    BasePropulsorWidget,
    TURBOPROP_COMPONENT_FIELDS,
)
from utilities import Units


class TurbopropWidget(BasePropulsorWidget):
    # Turboprop uses a turbine core plus gearbox/propeller fields.
    propulsor_type = "Turboprop"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Turboprop
    subcomponent_classes = {
        "compressor": RCAIDE.Library.Components.Powertrain.Converters.Compressor,
        "turbine": RCAIDE.Library.Components.Powertrain.Converters.Turbine,
        "combustor": RCAIDE.Library.Components.Powertrain.Converters.Combustor,
        "propeller": RCAIDE.Library.Components.Powertrain.Converters.Propeller,
    }
    type_fields = [
        ("Turboprop Design", Units.Heading, ""),
        ("Design Altitude", Units.Length, "design_altitude"),
        ("Gearbox Gear Ratio", Units.Unitless, "gearbox.gear_ratio"),
        ("Gearbox Efficiency", Units.Unitless, "gearbox.efficiency"),
        ("Design Mach Number", Units.Unitless, "design_mach_number"),
        ("Design Freestream Velocity", Units.Velocity, "design_freestream_velocity"),
    ] + TURBOPROP_COMPONENT_FIELDS
