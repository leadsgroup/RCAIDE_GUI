from PyQt6.QtWidgets import QMessageBox


def show_popup(message, parent):
    """Display a pop-up message for 2 seconds."""
    popup = QMessageBox(parent)
    popup.setWindowTitle("Info")
    popup.setText(message)
    # This line seemed to make it impossible to close the popup
    # popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
    popup.setStyleSheet("QLabel{min-width: 300px;}")
    popup.show()


class Units():
    pass
