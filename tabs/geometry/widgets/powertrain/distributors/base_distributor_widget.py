# RCAIDE_GUI/tabs/geometry/widgets/powertrain/distributors/base_distributor_widget.py

# Created: Jun 2026, M. Clarke

from tabs.geometry.widgets import GeometryDataWidget
from utilities import CONNECTION_GROUPS, empty_connections
import rcaide_io


class BaseDistributorWidget(GeometryDataWidget):
    """Base class for all powertrain distributor widgets.

    Subclasses handle name entry and type-specific properties.
    Connectivity (assigned propulsors, sources, converters and systems) is
    managed by ConnectionMatrixFrame.  ``load_connections`` stores the loaded
    connectivity in ``loaded_connections`` so that PowertrainWidget can seed
    the matrix after a file load.
    """

    distributor_type = ""

    def __init__(self, index, on_delete):
        super().__init__()
        self.index = index
        self.on_delete = on_delete
        # Populated by load_connections; read by PowertrainWidget._collect_distributor_info
        self.loaded_connections = empty_connections()
        # RCAIDE distributor loaded from a file (stripped JSON dict); None for a new distributor
        self.loaded_component = None

    def load_connections(self, data):
        """Store the loaded RCAIDE distributor and the component names it connects to, one list per connection group."""
        self.loaded_component   = data.get("rcaide_component")
        self.loaded_connections = {key: list(data.get(key, [])) for key, _ in CONNECTION_GROUPS}

    def base_distributor(self, distributor_class):
        """Return the loaded RCAIDE distributor, or a new one with RCAIDE defaults."""
        if self.loaded_component is not None:
            distributor = rcaide_io.component_from_dict(self.loaded_component)
            if type(distributor) is distributor_class:
                return distributor
        return distributor_class()

    def keep_loaded_component(self, data):
        """Carry the loaded RCAIDE distributor along with the form data."""
        if self.loaded_component is not None:
            data["rcaide_component"] = self.loaded_component
        return data

    def delete_button_pressed(self):
        if self.on_delete:
            self.on_delete(self.index)
