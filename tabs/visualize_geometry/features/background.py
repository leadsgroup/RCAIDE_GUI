# =================================
# BACKGROUND MENU (with checkmarks)
# =================================
# UI widgets used to build the small background mode menu

from PyQt6.QtWidgets import QPushButton, QMenu, QColorDialog
from PyQt6.QtGui import QAction, QColor
from tabs.visualize_geometry.visualize_geometry import VisualizeGeometryWidget

class BackgroundManager:
    """Manage background mode and menu checkmarks (dark / light / custom)."""
    def __init__(self, widget):
        # keep a reference to the widget so we can access renderer & window
        self.widget = widget
        self.current_mode = "dark"  # default

    @property
    def renderer(self):
        # return the renderer if it exists, else None
        return getattr(self.widget, "renderer", None)

    @property
    def window(self):
        # return the render window so we can call Render()
        try:
            return self.widget.vtkWidget.GetRenderWindow()
        except Exception:
            return None

    def _set_mode(self, mode: str):
        """Set renderer background and update menu checkmarks."""
        r = self.renderer
        w = self.window
        if r is None or w is None:
            return

        if mode == "dark":
            r.GradientBackgroundOn()
            r.SetBackground(0.05, 0.08, 0.15)
            r.SetBackground2(0.12, 0.18, 0.28)

        elif mode == "light":
            r.GradientBackgroundOn()
            r.SetBackground(0.85, 0.90, 0.98)
            r.SetBackground2(1.0, 1.0, 1.0)

        elif mode == "custom":
            # Custom color is handled by set_custom_color() which calls _set_mode("custom")
            pass

        # update menu checkmarks if actions exist
        actions = getattr(self.widget, "_bg_actions", None) or {}
        for m, act in actions.items():
            act.setCheckable(True)
            act.setChecked(m == mode)

        # remember mode and force a redraw
        self.current_mode = mode
        w.Render()

    def set_dark_mode(self):
        # switch to dark mode
        self._set_mode("dark")

    def set_light_mode(self):
        # switch to light mode
        self._set_mode("light")

    def set_custom_color(self):
        # set a single custom background color chosen by the user
        r = self.renderer
        w = self.window
        if r is None or w is None:
            return

        # ask user for a color (default is dark)
        color = QColorDialog.getColor(QColor(20, 20, 20), self.widget, "Choose Background Color")
        if not color.isValid():
            return

        # turn off gradient and apply the chosen color
        r.GradientBackgroundOff()
        r.SetBackground(color.redF(), color.greenF(), color.blueF())

        # mark "custom" in the menu and redraw
        actions = getattr(self.widget, "_bg_actions", None) or {}
        for m, act in actions.items():
            act.setCheckable(True)
            act.setChecked(m == "custom")

        self.current_mode = "custom"
        w.Render()

def _add_background_menu(self):
    """Add Background menu once to the toolbar."""
    # require toolbar
    if not hasattr(self, "toolbar") or self.toolbar is None:
        return

    # Prevent duplicates
    if getattr(self, "_background_menu_added", False):
        return
    self._background_menu_added = True

    # create or reuse a small helper that talks to the renderer
    if not hasattr(self, "bg_manager") or self.bg_manager is None:
        self.bg_manager = BackgroundManager(self)

    # add a simple button to the toolbar
    btn = QPushButton("🌄 Background")
    self.toolbar.addSeparator()
    self.toolbar.addWidget(btn)

    # create a menu to hold actions
    menu = QMenu(btn)

    # actions for each mode
    act_dark = QAction("Dark Mode", menu)   # dark gradient
    act_light = QAction("Light Mode", menu) # light gradient
    act_custom = QAction("Custom Color…", menu) # pick solid color

    # wire actions to the manager
    act_dark.triggered.connect(self.bg_manager.set_dark_mode)
    act_light.triggered.connect(self.bg_manager.set_light_mode)
    act_custom.triggered.connect(self.bg_manager.set_custom_color)

    # keep actions on the widget so we can update checkmarks later
    # stored under `self._bg_actions` for easy access from the manager
    self._bg_actions = {"dark": act_dark, "light": act_light, "custom": act_custom}

    # make each action checkable and add it to the menu
    for act in self._bg_actions.values():
        act.setCheckable(True)
        menu.addAction(act)

    # attach the menu to the toolbar button
    btn.setMenu(menu)

    # set default mode now so the UI matches renderer
    self.bg_manager.set_dark_mode()

# Activate Patch
def _patch_update_toolbar_for_background_menu():
    """Wrap update_toolbar once so the background menu is added."""
    # don't apply more than once
    if getattr(VisualizeGeometryWidget, "_bg_update_toolbar_patched", False):
        return

    old_update_toolbar = VisualizeGeometryWidget.update_toolbar

    def wrapped_update_toolbar(self, *args, **kwargs):
        # keep original toolbar behavior
        old_update_toolbar(self, *args, **kwargs)
        # then ensure the background menu is attached (won't duplicate)
        _add_background_menu(self)  # idempotent

    VisualizeGeometryWidget.update_toolbar = wrapped_update_toolbar
    VisualizeGeometryWidget._bg_update_toolbar_patched = True

_patch_update_toolbar_for_background_menu()
# patch applied above so the background menu is ready when toolbars are built