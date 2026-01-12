# ===========================
# SCREENSHOT EXPORT SECTION
# ===========================
# Adds "📷 Export View" to the toolbar and saves the current VTK view to PNG/JPG.

import datetime
import vtk
from PyQt6.QtWidgets import QPushButton, QFileDialog, QMessageBox
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

def add_screenshot_button(self):
    # --- need toolbar + vtkWidget ---
    if not getattr(self, "toolbar", None) or not getattr(self, "vtkWidget", None):
        return

    # --- prevents adding the button twice ---
    if getattr(self, "screenshot_button", None) is not None:
        return

    # --- add button to toolbar ---
    btn = QPushButton("📷 Export View")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)
    self.screenshot_button = btn

    def save_screenshot():
        # --- choose filename (default timestamp) ---
        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        default_name = f"screenshot_{ts}.png"

        path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Screenshot As",
            default_name,
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)",
        )
        if not path:
            return

        # --- add extension if missing ---
        lower = path.lower()
        if not (lower.endswith(".png") or lower.endswith(".jpg") or lower.endswith(".jpeg")):
            path += ".jpg" if "JPEG" in selected_filter else ".png"

        # --- grab current render window image ---
        rw = self.vtkWidget.GetRenderWindow()
        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(rw)
        w2i.ReadFrontBufferOff()
        w2i.SetInputBufferTypeToRGBA()
        w2i.Update()

        # --- pick writer based on extension ---
        if path.lower().endswith((".jpg", ".jpeg")):
            writer = vtk.vtkJPEGWriter()
        else:
            writer = vtk.vtkPNGWriter()

        # --- write file ---
        writer.SetFileName(path)
        writer.SetInputConnection(w2i.GetOutputPort())

        try:
            writer.Write()
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not save screenshot:\n{e}")
            return

        QMessageBox.information(self, "Export Successful", f"Saved:\n{path}")

    # --- connect click ---
    btn.clicked.connect(save_screenshot)

# Activate Patch
def _patch_update_toolbar_for_screenshot():
    # --- patch update_toolbar to add screenshot button ---
    if getattr(VisualizeGeometryWidget, "_screenshot_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        old_update_toolbar(self, *args, **kwargs)
        add_screenshot_button(self)

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._screenshot_update_toolbar_patched = True

_patch_update_toolbar_for_screenshot()