from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout

from widgets import Color
from tabs import TabWidget


def get_widget() -> QWidget:
    base_layout = QHBoxLayout()
    main_layout = QVBoxLayout()

    tree_frame = Color("red")
    main_frame = Color("red")
    main_extra_frame = Color("red")

    main_layout.addWidget(main_frame, 7)
    main_layout.addWidget(main_extra_frame, 3)
    base_layout.addWidget(tree_frame, 1)
    base_layout.addLayout(main_layout, 4)

    main_layout.setSpacing(3)
    base_layout.setSpacing(3)

    base_widget = TabWidget()
    base_widget.setLayout(base_layout)
    return base_widget
