from PyQt6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QWidgetItem


class PowertrainConnectorWidget(QWidget):
    def __init__(self):
        super(PowertrainConnectorWidget, self).__init__()

        self.main_layout = QHBoxLayout()
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(QWidget(), "Distributors")
        self.tab_widget.addTab(QWidget(), "Converters")
        self.tab_widget.addTab(QWidget(), "Sources")

        self.main_layout.addWidget(self.tab_widget)
        self.selector_layouts = []
        self.names = []

        self.setLayout(self.main_layout)

    def clear(self):
        pass

    def update_selector(self, data):
        distributor_names = [x["distributor name"] for x in data["distributor data"]]
        propulsor_names = [x["Propulsor Tag"] for x in data["propulsor data"]]
        converter_names = [x["Converter Name"] for x in data["converter data"]]
        source_names = [x["Source Name"] for x in data["source data"]]

        self.names = [distributor_names, propulsor_names, converter_names, source_names]

        self.tab_widget.clear()

        self.selector_layouts = []
        temp = []
        layout = QVBoxLayout()
        for distributor in distributor_names:
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(distributor))
            for propulsor in propulsor_names:
                sub_layout.addWidget(QCheckBox(propulsor))

            temp.append(sub_layout)
            layout.addLayout(sub_layout)

        self.selector_layouts.append(temp)
        widget = QWidget()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Distributors")

        temp = []
        layout = QVBoxLayout()
        for converter in converter_names:
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(converter))
            for propulsor in propulsor_names:
                sub_layout.addWidget(QCheckBox(propulsor))

            temp.append(sub_layout)
            layout.addLayout(sub_layout)

        self.selector_layouts.append(temp)
        widget = QWidget()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Converters")

        temp = []
        layout = QVBoxLayout()
        for distributor in distributor_names:
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(distributor))
            for source in source_names:
                sub_layout.addWidget(QCheckBox(source))

            temp.append(sub_layout)
            layout.addLayout(sub_layout)

        self.selector_layouts.append(temp)
        widget = QWidget()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Sources")
    
    def get_connections(self, data):
        distributor_names = [x["distributor name"] for x in data["distributor data"]]
        propulsor_names = [x["Propulsor Tag"] for x in data["propulsor data"]]
        converter_names = [x["Converter Name"] for x in data["converter data"]]
        source_names = [x["Source Name"] for x in data["source data"]]

        current_names = [distributor_names, propulsor_names, converter_names, source_names]
        if self.names != current_names:
            self.update_selector(data)

        connections = []
        for tab in self.selector_layouts:
            tab_connections = []
            for layout in tab:
                temp = []
                assert isinstance(layout, QHBoxLayout)
                for i in range(1, layout.count()):
                    item = layout.itemAt(i).widget()
                    assert item is not None and isinstance(item, QCheckBox)
                    temp.append(item.isChecked())

                tab_connections.append(temp)

            connections.append(tab_connections)
        return connections
