from PyQt6.QtWidgets import QWidget, QTabWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox


class PowertrainConnectorWidget(QWidget):
    def __init__(self):
        super(PowertrainConnectorWidget, self).__init__()

        self.main_layout = QHBoxLayout()
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(QWidget(), "Propulsors")
        self.tab_widget.addTab(QWidget(), "Converters")
        self.tab_widget.addTab(QWidget(), "Sources")

        self.main_layout.addWidget(self.tab_widget)
        self.selector_layouts = []

        self.setLayout(self.main_layout)

    def clear(self):
        pass

    def update_selector(self, data):
        distributor_names = [x["name"] for x in data["distributor data"]]
        propulsor_names = [x["Propulsor Tag"] for x in data["propulsor data"]]
        converter_names = [x["Converter Name"] for x in data["converter data"]]
        source_names = [x["Source Name"] for x in data["source data"]]

        self.tab_widget.clear()

        self.selector_layouts = []
        temp = []
        layout = QVBoxLayout()
        for propulsor in propulsor_names:
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(propulsor))
            for distributor in distributor_names:
                sub_layout.addWidget(QCheckBox(distributor))

            temp.append(sub_layout)
            layout.addLayout(sub_layout)

        self.selector_layouts.append(temp)
        widget = QWidget()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Propulsors")

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
        for source in source_names:
            sub_layout = QHBoxLayout()
            sub_layout.addWidget(QLabel(source))
            for distributor in distributor_names:
                sub_layout.addWidget(QCheckBox(distributor))

            temp.append(sub_layout)
            layout.addLayout(sub_layout)

        self.selector_layouts.append(temp)
        widget = QWidget()
        widget.setLayout(layout)
        self.tab_widget.addTab(widget, "Sources")
