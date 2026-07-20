# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/base_distributor_widget.py

# Created: Jun 2026, M. Clarke

from tabs.geometry.widgets import GeometryDataWidget


class BaseDistributorWidget(GeometryDataWidget):
    """Base class for all powertrain distributor widgets.

    Subclasses handle name entry and type-specific properties.
    Connectivity (assigned propulsors and sources) is managed by
    ConnectionMatrixFrame.  Subclasses store loaded connectivity in
    ``_loaded_propulsors`` / ``_loaded_sources`` so that PowertrainWidget
    can seed the matrix after a file load.
    """

    distributor_type = ""

    def __init__(self, index, on_delete):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        # Populated by load_data_values; read by PowertrainWidget._collect_distributor_info
        self._loaded_propulsors: list[str] = []
        self._loaded_sources:    list[str] = []

    def delete_button_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)
