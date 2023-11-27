from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton

from color import Color


def get_widget() -> QWidget:
    base_layout = QHBoxLayout()
    main_layout = QVBoxLayout()

    tree_frame = Color("pink")
    main_frame = Color("pink")
    main_extra_frame = Color("pink")

    solve_button = QPushButton("SOLVE")

    main_layout.addWidget(main_frame, 7)
    main_layout.addWidget(solve_button, 2)
    main_layout.addWidget(main_extra_frame, 3)
    base_layout.addWidget(tree_frame, 1)
    base_layout.addLayout(main_layout, 4)

    main_layout.setSpacing(3)
    base_layout.setSpacing(3)

    base_widget = QWidget()
    base_widget.setLayout(base_layout)
    return base_widget
