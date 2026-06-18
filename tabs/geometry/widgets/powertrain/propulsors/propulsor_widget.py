# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/propulsor_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import BasePropulsorWidget


class PropulsorWidget(BasePropulsorWidget):
    # Plain base propulsor exposes only fields common to all RCAIDE propulsors.
    propulsor_type = "Propulsor"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Propulsor
    subcomponent_classes = {}
    type_fields = []
