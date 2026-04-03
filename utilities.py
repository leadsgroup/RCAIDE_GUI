import numpy as np
import math
from PyQt6.QtWidgets import QLayout, QMessageBox, QFrame, QScrollArea, QVBoxLayout, QWidget


def show_popup(message, parent):
    """Display a pop-up message for 2 seconds."""
    popup = QMessageBox(parent)
    popup.setWindowTitle("Info")
    popup.setText(message)
    # This line seemed to make it impossible to close the popup
    # popup.setStandardButtons(QMessageBox.StandardButton.NoButton)
    popup.setStyleSheet("QLabel{min-width: 300px;}")
    popup.show()


def create_line_bar():
    """Create a line bar to separate the widgets."""
    line_bar = QFrame()
    line_bar.setFrameShape(QFrame.Shape.HLine)
    line_bar.setFrameShadow(QFrame.Shadow.Sunken)

    return line_bar


def create_scroll_area(widget: QWidget, set_layout=True):
    widget.scroll_area = QScrollArea()
    widget.scroll_area.setWidgetResizable(True)
    scroll_content = QWidget()
    widget.scroll_area.setWidget(scroll_content)
    widget.main_layout = QVBoxLayout(scroll_content)
    layout_scroll = QVBoxLayout()
    layout_scroll.addWidget(widget.scroll_area)
    layout_scroll.setContentsMargins(0, 0, 0, 0)
    if set_layout:
        widget.setLayout(layout_scroll)

    return layout_scroll


def set_data(obj: dict, key: str, data):
    key_list = key.split(".")
    key = key_list[0]
    key_list = key_list[1:]

    if len(key_list) > 0:
        set_data(obj[key], ".".join(key_list), data)
        return

    obj[key] = data


def clear_layout(layout: QLayout):
    """Clear all widgets from the layout."""
    while layout.count():
        item = layout.takeAt(0)

        assert item is not None
        widget = item.widget()
        if widget is not None:
            # Remove widget
            widget.deleteLater()
        else:
            sublayout = item.layout()
            if sublayout is not None:
                # Recursively clear sublayout
                clear_layout(sublayout)

def convert_name(name: str):
    return name.replace(" ", "_").lower()

# Full Unit System for all unit conversions in the app
class Units:

    # Length Units
    class Length:
        METER = ("m", lambda x: x)
        CENTIMETER = ("cm", lambda x: x * 0.01)
        MILLIMETER = ("mm", lambda x: x * 0.001)
        INCH = ("in", lambda x: x * 0.0254)
        FOOT = ("ft", lambda x: x * 0.3048)
        MILE = ("mi", lambda x: x * 1609.344)
        NAUTICAL_MILE = ("nmi", lambda x: x * 1852.0)
        KILOMETER = ("km", lambda x: x * 1000)
        DECIMETER = ("dm", lambda x: x * 0.1)
        YARD = ("yd", lambda x: x * 0.9144)
        unit_list = [METER, CENTIMETER, MILLIMETER, INCH, FOOT, NAUTICAL_MILE, 
                     KILOMETER, DECIMETER, YARD, MILE]
        
    # Area Units
    class Area:
        SQUARE_METER = ("m\u00b2", lambda x: x)
        SQUARE_CENTIMETER = ("cm\u00b2", lambda x: x * 0.0001)
        SQUARE_MILLIMETER = ("mm\u00b2", lambda x: x * 0.000001)
        SQUARE_INCH = ("in\u00b2", lambda x: x * 0.00064516)
        SQUARE_FOOT = ("ft\u00b2", lambda x: x * 0.092903)
        SQUARE_KILOMETER = ("km\u00b2", lambda x: x * 1e6)
        SQUARE_YARD = ("yd\u00b2", lambda x: x * 0.83612736)
        SQUARE_MILE = ("mi\u00b2", lambda x: x * 2.589988e6)

        unit_list = [SQUARE_METER, SQUARE_CENTIMETER, 
                     SQUARE_MILLIMETER, SQUARE_INCH, SQUARE_FOOT, SQUARE_KILOMETER, SQUARE_YARD, SQUARE_MILE]
        
    # Volume Units
    class Volume:
        CUBIC_METER = ("m\u00b3", lambda x: x)
        CUBIC_CENTIMETER = ("cm\u00b3", lambda x: x * 0.000001)
        CUBIC_MILLIMETER = ("mm\u00b3", lambda x: x * 0.000000001)
        CUBIC_INCH = ("in\u00b3", lambda x: x * 0.0000163871)
        CUBIC_FOOT = ("ft\u00b3", lambda x: x * 0.0283168)
        LITER = ("L", lambda x: x * 1e-3)
        MILLILITER = ("mL", lambda x: x * 1e-6)
        GALLON = ("gal", lambda x: x * 3.785411784e-3)
        QUART = ("qt", lambda x: x * 0.946352946e-3)
        PINT = ("pt", lambda x: x * 0.473176473e-3)

        unit_list = [CUBIC_METER, CUBIC_CENTIMETER,
                     CUBIC_MILLIMETER, CUBIC_INCH, CUBIC_FOOT, LITER, MILLILITER, GALLON, QUART, PINT]
        
    # Temperature Units
    class Temperature:
        KELVIN = ("K", lambda x: x)
        CELSIUS = ("\u00B0C", lambda x: x - 273.15)
        FAHRENHEIT = ("\u00B0F", lambda x: (x - 32.0) * 9.0 / 5.0 + 273.15)
        RANKINE = ("\u00B0R", lambda x: x * 1.8)

        unit_list = [KELVIN, CELSIUS, FAHRENHEIT, RANKINE]

    # Mass Units
    class Mass:
        KILOGRAM = ("kg", lambda x: x)
        GRAM = ("g", lambda x: x * 0.001)
        MILLIGRAM = ("mg", lambda x: x * 0.000001)
        OUNCE = ("oz", lambda x: x * 0.0283495)
        POUND = ("lb", lambda x: x * 0.453592)
        METRIC_TON = ("t", lambda x: x * 1000.0)
        SLUG = ("slug", lambda x: x * 14.5939)

        unit_list = [KILOGRAM, GRAM, MILLIGRAM, OUNCE, POUND, METRIC_TON, SLUG]
    
    # Time Units
    class Time:
        MILLISECOND = ("ms", lambda x: x * 0.001)
        MICROSECOND = ("µs", lambda x: x * 0.000001)
        SECOND = ("s", lambda x: x)
        MINUTE = ("min", lambda x: x * 60.0)
        HOUR = ("h", lambda x: x * 3600.0)
        DAY = ("d", lambda x: x * 86400.0)
        WEEK = ("wk", lambda x: x * 604800.0)
        MONTH = ("mo", lambda x: x * 2629800.0)
        YEAR = ("yr", lambda x: x * 31557600.0)

        unit_list = [SECOND, MINUTE, HOUR, DAY, MILLISECOND, MICROSECOND, WEEK, MONTH, YEAR]

    # Velocity Units
    class Velocity:
        METER_PER_SECOND = ("m/s", lambda x: x)
        KILOMETER_PER_HOUR = ("km/h", lambda x: x / 3.6)
        MILE_PER_HOUR = ("mph", lambda x: x * 0.44704)
        KNOT = ("kts", lambda x: x * 0.514444)
        FOOT_PER_SECOND = ("ft/s", lambda x: x * 0.3048)
        FOOT_PER_MINUTE = ("ft/min", lambda x: x * 0.3048 / 60.0)
        KILOMETER_PER_SECOND = ("km/s", lambda x: x * 1000.0)

        unit_list = [METER_PER_SECOND, KNOT, FOOT_PER_SECOND, FOOT_PER_MINUTE, KILOMETER_PER_SECOND]

    # Acceleration Units
    class Acceleration:
        METER_PER_SECOND_SQUARED = ("m/s\u00b2", lambda x: x)
        KNOTS_PER_SECOND = ("kts/s", lambda x: x * 0.514444)
        STANDARD_GRAVITY = ("g", lambda x: x * 9.80665)
        FOOT_PER_SECOND_SQUARED = ("ft/s\u00b2", lambda x: x * 0.3048)

        unit_list = [METER_PER_SECOND_SQUARED, KNOTS_PER_SECOND, STANDARD_GRAVITY, FOOT_PER_SECOND_SQUARED]

    # Force Units
    class Force:
        NEWTON = ("N", lambda x: x)
        KILONEWTON = ("kN", lambda x: x * 1000.0)
        MEGANEWTON = ("MN", lambda x: x * 1000000.0)
        POUND_FORCE = ("lbf", lambda x: x * 4.448221615)

        unit_list = [NEWTON, KILONEWTON, MEGANEWTON, POUND_FORCE]

    # Energy Units
    class Energy:
        JOULE = ("J", lambda x: x)
        KILOJOULE = ("kJ", lambda x: x * 1000.0)
        WATT_HOUR = ("Wh", lambda x: x * 3600.0)
        KILOWATT_HOUR = ("kWh", lambda x: x * 3600000.0)
        BTU = ("BTU", lambda x: x * 1055.06)
        CALORIE = ("cal", lambda x: x * 4.184)
        KILOCALORIE = ("kcal", lambda x: x * 4184)

        unit_list = [JOULE, KILOJOULE, WATT_HOUR,
                     KILOWATT_HOUR, CALORIE, KILOCALORIE, BTU]

    # Current Units
    class Current:
        AMPERE = ("A", lambda x: x)
        MILLIAMPERE = ("mA", lambda x: x * 0.001)
        MICROAMPERE = ("µA", lambda x: x * 0.000001)

        unit_list = [AMPERE, MILLIAMPERE, MICROAMPERE]

    # Pressure Units
    class Pressure:
        PASCAL = ("Pa", lambda x: x)
        KILOPASCAL = ("kPa", lambda x: x * 1000.0)
        MEGAPASCAL = ("MPa", lambda x: x * 1000000.0)
        BAR = ("bar", lambda x: x * 100000.0)
        ATMOSPHERE = ("atm", lambda x: x * 101325.0)
        POUND_PER_SQUARE_INCH = ("psi", lambda x: x * 6894.757293)
        MILLIBAR = ("mbar", lambda x: x * 100.0)
        POUND_PER_SQUARE_FOOT = ("psf", lambda x: x * 47.8802589)

        unit_list = [PASCAL, KILOPASCAL, MEGAPASCAL,
                     BAR, ATMOSPHERE, POUND_PER_SQUARE_INCH, MILLIBAR, POUND_PER_SQUARE_FOOT]

    # Unitless Units
    class Unitless:
        NONE = ("", lambda x: x)
        PERCENT = ("%", lambda x: x / 100.0)

        unit_list = [NONE, PERCENT]

    class Count:
        UNIT = ("Unit", lambda x: x)
        unit_list = [UNIT]

    class Angle:
        RADIAN = ("rad", lambda x: x)
        DEGREE = ("deg", lambda x: np.deg2rad(x))

        unit_list = [DEGREE, RADIAN]

    # Intertia Units
    class Intertia:
        KILOGRAM_PER_SQUARE_METER = ("kg/m\u00b2", lambda x: x)
        POUND_PER_SQUARE_FOOT = ("slug/ft\u00b2", lambda x: x * 1.35581795)

        unit_list = [KILOGRAM_PER_SQUARE_METER, POUND_PER_SQUARE_FOOT]       

    class Position:
        pass

    class Boolean:
        pass

    class Heading:
        pass

    class File:
        pass

    class String:
        pass