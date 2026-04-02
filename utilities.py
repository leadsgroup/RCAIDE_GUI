import math
import numpy as np
from PyQt6.QtWidgets import QFrame, QLayout, QMessageBox, QScrollArea, QVBoxLayout, QWidget


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
            widget.deleteLater()
        else:
            sublayout = item.layout()
            if sublayout is not None:
                clear_layout(sublayout)


def convert_name(name: str):
    return name.replace(" ", "_").lower()


class _UnitsMeta(type):
    def __getattr__(cls, name: str) -> float:
        try:
            return cls._conversions[name]
        except KeyError as exc:
            raise AttributeError(f"Unit '{name}' is not defined.") from exc

    def __getitem__(cls, name: str) -> float:
        try:
            return cls._conversions[name]
        except KeyError as exc:
            raise KeyError(f"Unit '{name}' is not defined.") from exc


class Units(metaclass=_UnitsMeta):
    class Length:
        METER = ("m", lambda x: x)
        CENTIMETER = ("cm", lambda x: x * 0.01)
        MILLIMETER = ("mm", lambda x: x * 0.001)
        INCH = ("in", lambda x: x * 0.0254)
        FOOT = ("ft", lambda x: x * 0.3048)
        NAUTICAL_MILE = ("nmi", lambda x: x * 1852.0)
        KILOMETER = ("km", lambda x: x * 1000.0)
        DECIMETER = ("dm", lambda x: x * 0.1)
        YARD = ("yd", lambda x: x * 0.9144)
        MILE = ("mi", lambda x: x * 1609.344)

        unit_list = [
            METER,
            CENTIMETER,
            MILLIMETER,
            INCH,
            FOOT,
            NAUTICAL_MILE,
            KILOMETER,
            DECIMETER,
            YARD,
            MILE,
        ]

    class Area:
        SQUARE_METER = ("m^2", lambda x: x)
        SQUARE_CENTIMETER = ("cm^2", lambda x: x * 1.0e-4)
        SQUARE_MILLIMETER = ("mm^2", lambda x: x * 1.0e-6)
        SQUARE_INCH = ("in^2", lambda x: x * 0.00064516)
        SQUARE_FOOT = ("ft^2", lambda x: x * 0.09290304)
        SQUARE_KILOMETER = ("km^2", lambda x: x * 1.0e6)
        SQUARE_YARD = ("yd^2", lambda x: x * 0.83612736)
        SQUARE_MILE = ("mi^2", lambda x: x * 2.589988e6)

        unit_list = [
            SQUARE_METER,
            SQUARE_CENTIMETER,
            SQUARE_MILLIMETER,
            SQUARE_INCH,
            SQUARE_FOOT,
            SQUARE_KILOMETER,
            SQUARE_YARD,
            SQUARE_MILE,
        ]

    class Volume:
        CUBIC_METER = ("m^3", lambda x: x)
        CUBIC_CENTIMETER = ("cm^3", lambda x: x * 1.0e-6)
        CUBIC_MILLIMETER = ("mm^3", lambda x: x * 1.0e-9)
        CUBIC_INCH = ("in^3", lambda x: x * (0.0254 ** 3))
        CUBIC_FOOT = ("ft^3", lambda x: x * (0.3048 ** 3))
        LITER = ("L", lambda x: x * 1.0e-3)
        MILLILITER = ("mL", lambda x: x * 1.0e-6)
        GALLON = ("gal", lambda x: x * 3.785411784e-3)
        QUART = ("qt", lambda x: x * 0.946352946e-3)
        PINT = ("pt", lambda x: x * 0.473176473e-3)

        unit_list = [
            CUBIC_METER,
            CUBIC_CENTIMETER,
            CUBIC_MILLIMETER,
            CUBIC_INCH,
            CUBIC_FOOT,
            LITER,
            MILLILITER,
            GALLON,
            QUART,
            PINT,
        ]

    class Temperature:
        KELVIN = ("K", lambda x: x)
        CELSIUS = ("degC", lambda x: x + 273.15)
        FAHRENHEIT = ("degF", lambda x: (x - 32.0) * 5.0 / 9.0 + 273.15)
        RANKINE = ("degR", lambda x: x * 5.0 / 9.0)

        unit_list = [KELVIN, CELSIUS, FAHRENHEIT, RANKINE]

    class Mass:
        KILOGRAM = ("kg", lambda x: x)
        GRAM = ("g", lambda x: x * 0.001)
        MILLIGRAM = ("mg", lambda x: x * 1.0e-6)
        OUNCE = ("oz", lambda x: x * 0.028349523125)
        POUND = ("lb", lambda x: x * 0.45359237)
        METRIC_TON = ("t", lambda x: x * 1000.0)
        SLUG = ("slug", lambda x: x * 14.5939029372)

        unit_list = [KILOGRAM, GRAM, MILLIGRAM, OUNCE, POUND, METRIC_TON, SLUG]

    class Time:
        SECOND = ("s", lambda x: x)
        MINUTE = ("min", lambda x: x * 60.0)
        HOUR = ("h", lambda x: x * 3600.0)
        DAY = ("d", lambda x: x * 86400.0)
        MILLISECOND = ("ms", lambda x: x * 0.001)
        MICROSECOND = ("us", lambda x: x * 1.0e-6)
        WEEK = ("wk", lambda x: x * 604800.0)
        MONTH = ("mo", lambda x: x * 2629800.0)
        YEAR = ("yr", lambda x: x * 31557600.0)

        unit_list = [SECOND, MINUTE, HOUR, DAY, MILLISECOND, MICROSECOND, WEEK, MONTH, YEAR]

    class Velocity:
        METER_PER_SECOND = ("m/s", lambda x: x)
        KILOMETER_PER_HOUR = ("km/h", lambda x: x / 3.6)
        MILE_PER_HOUR = ("mph", lambda x: x * 0.44704)
        KNOT = ("kn", lambda x: x * 0.514444)
        FOOT_PER_SECOND = ("ft/s", lambda x: x * 0.3048)
        FOOT_PER_MINUTE = ("ft/min", lambda x: x * 0.3048 / 60.0)
        KILOMETER_PER_SECOND = ("km/s", lambda x: x * 1000.0)

        unit_list = [
            METER_PER_SECOND,
            KILOMETER_PER_HOUR,
            MILE_PER_HOUR,
            KNOT,
            FOOT_PER_SECOND,
            FOOT_PER_MINUTE,
            KILOMETER_PER_SECOND,
        ]

    class Acceleration:
        METER_PER_SECOND_SQUARED = ("m/s^2", lambda x: x)
        KNOTS_PER_SECOND = ("kn/s", lambda x: x * 0.514444)
        FOOT_PER_SECOND_SQUARED = ("ft/s^2", lambda x: x * 0.3048)
        STANDARD_GRAVITY = ("g0", lambda x: x * 9.80665)

        unit_list = [METER_PER_SECOND_SQUARED, KNOTS_PER_SECOND, FOOT_PER_SECOND_SQUARED, STANDARD_GRAVITY]

    class Force:
        NEWTON = ("N", lambda x: x)
        KILONEWTON = ("kN", lambda x: x * 1000.0)
        MEGANEWTON = ("MN", lambda x: x * 1000000.0)
        POUND_FORCE = ("lbf", lambda x: x * 4.448221615)

        unit_list = [NEWTON, KILONEWTON, MEGANEWTON, POUND_FORCE]

    class Energy:
        JOULE = ("J", lambda x: x)
        KILOJOULE = ("kJ", lambda x: x * 1000.0)
        WATT_HOUR = ("Wh", lambda x: x * 3600.0)
        KILOWATT_HOUR = ("kWh", lambda x: x * 3600000.0)
        CALORIE = ("cal", lambda x: x * 4.184)
        KILOCALORIE = ("kcal", lambda x: x * 4184.0)
        BTU = ("BTU", lambda x: x * 1055.06)

        unit_list = [JOULE, KILOJOULE, WATT_HOUR, KILOWATT_HOUR, CALORIE, KILOCALORIE, BTU]

    class Power:
        WATT = ("W", lambda x: x)
        KILOWATT = ("kW", lambda x: x * 1000.0)
        HORSEPOWER = ("hp", lambda x: x * 745.7)
        BTU_PER_HOUR = ("BTU/h", lambda x: x * 0.29307107)

        unit_list = [WATT, KILOWATT, HORSEPOWER, BTU_PER_HOUR]

    class Current:
        AMPERE = ("A", lambda x: x)
        MILLIAMPERE = ("mA", lambda x: x * 0.001)
        MICROAMPERE = ("uA", lambda x: x * 1.0e-6)

        unit_list = [AMPERE, MILLIAMPERE, MICROAMPERE]

    class Pressure:
        PASCAL = ("Pa", lambda x: x)
        KILOPASCAL = ("kPa", lambda x: x * 1000.0)
        MEGAPASCAL = ("MPa", lambda x: x * 1000000.0)
        BAR = ("bar", lambda x: x * 100000.0)
        MILLIBAR = ("mbar", lambda x: x * 100.0)
        ATMOSPHERE = ("atm", lambda x: x * 101325.0)
        POUND_PER_SQUARE_INCH = ("psi", lambda x: x * 6894.757293)
        POUND_PER_SQUARE_FOOT = ("psf", lambda x: x * 47.8802589)

        unit_list = [
            PASCAL,
            KILOPASCAL,
            MEGAPASCAL,
            BAR,
            MILLIBAR,
            ATMOSPHERE,
            POUND_PER_SQUARE_INCH,
            POUND_PER_SQUARE_FOOT,
        ]

    class Unitless:
        NONE = ("", lambda x: x)
        PERCENT = ("%", lambda x: x / 100.0)
        unit_list = [NONE, PERCENT]

    class Count:
        UNIT = ("Unit", lambda x: x)
        unit_list = [UNIT]

    class Angle:
        DEGREE = ("deg", lambda x: np.deg2rad(x))
        RADIAN = ("rad", lambda x: x)
        unit_list = [DEGREE, RADIAN]

    class Intertia:
        KILOGRAM_PER_SQUARE_METER = ("kg/m^2", lambda x: x)
        POUND_PER_SQUARE_FOOT = ("slug/ft^2", lambda x: x * 1.35581795)
        unit_list = [KILOGRAM_PER_SQUARE_METER, POUND_PER_SQUARE_FOOT]

    class Density:
        KILOGRAM_PER_CUBIC_METER = ("kg/m^3", lambda x: x)
        SLUG_PER_CUBIC_FOOT = ("slug/ft^3", lambda x: x * 515.378818)
        POUND_PER_CUBIC_FOOT = ("lb/ft^3", lambda x: x * 16.0185)
        GRAM_PER_CUBIC_CENTIMETER = ("g/cm^3", lambda x: x * 1000.0)

        unit_list = [
            KILOGRAM_PER_CUBIC_METER,
            SLUG_PER_CUBIC_FOOT,
            POUND_PER_CUBIC_FOOT,
            GRAM_PER_CUBIC_CENTIMETER,
        ]

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

    _conversions = {
        # ------------------------------------------------
        # UNITLESS (dimensionless quantities)
        # ------------------------------------------------
        "unitless": 1.0,

        # ------------------------------------------------
        # MASS -> kilograms (kg)
        # ------------------------------------------------
        "kg": 1.0,
        "g": 1e-3,
        "mg": 1e-6,
        "oz": 0.028349523125,
        "lb": 0.45359237,
        "t": 1000.0,
        "slug": 14.5939029372,

        # ------------------------------------------------
        # FORCE -> newtons (N)
        # ------------------------------------------------
        "N": 1.0,
        "kN": 1000.0,
        "MN": 1000000.0,
        "lbf": 4.448221615,

        # ------------------------------------------------
        # LENGTH -> meters (m)
        # ------------------------------------------------
        "m": 1.0,
        "cm": 0.01,
        "mm": 0.001,
        "in": 0.0254,
        "ft": 0.3048,
        "nmi": 1852.0,
        "km": 1000.0,
        "dm": 0.1,
        "yd": 0.9144,
        "mi": 1609.344,

        # ------------------------------------------------
        # AREA -> square meters (m^2)
        # ------------------------------------------------
        "m^2": 1.0,
        "cm^2": 1.0e-4,
        "mm^2": 1.0e-6,
        "in^2": 0.00064516,
        "ft^2": 0.09290304,
        "km^2": 1.0e6,
        "yd^2": 0.83612736,
        "mi^2": 2.589988e6,

        # ------------------------------------------------
        # VOLUME -> cubic meters (m^3)
        # ------------------------------------------------
        "m^3": 1.0,
        "cm^3": 1.0e-6,
        "mm^3": 1.0e-9,
        "in^3": 0.0254 ** 3,
        "ft^3": 0.3048 ** 3,
        "L": 1e-3,
        "mL": 1e-6,
        "gal": 3.785411784e-3,
        "qt": 0.946352946e-3,
        "pt": 0.473176473e-3,

        # ------------------------------------------------
        # TIME -> seconds (s)
        # ------------------------------------------------
        "s": 1.0,
        "ms": 1e-3,
        "us": 1e-6,
        "min": 60.0,
        "h": 3600.0,
        "d": 86400.0,
        "wk": 604800.0,
        "mo": 2629800.0,
        "yr": 31557600.0,

        # ------------------------------------------------
        # SPEED -> meters/second (m/s)
        # ------------------------------------------------
        "m/s": 1.0,
        "km/h": 0.277778,
        "mph": 0.44704,
        "kn": 0.514444,
        "ft/s": 0.3048,
        "ft/min": 0.3048 / 60.0,
        "km/s": 1000.0,

        # Rotational speed -> rad/s
        "rpm": 2.0 * math.pi / 60.0,

        # ------------------------------------------------
        # POWER -> watts (W)
        # ------------------------------------------------
        "W": 1.0,
        "kW": 1000.0,
        "hp": 745.7,
        "BTU/h": 0.29307107,

        # ------------------------------------------------
        # PRESSURE -> pascals (Pa)
        # ------------------------------------------------
        "Pa": 1.0,
        "kPa": 1e3,
        "MPa": 1e6,
        "bar": 1e5,
        "mbar": 1e2,
        "atm": 101325.0,
        "psi": 6894.757293,
        "psf": 47.8802589,

        # ------------------------------------------------
        # ANGLE -> radians (rad)
        # ------------------------------------------------
        "rad": 1.0,
        "deg": math.pi / 180.0,

        # ------------------------------------------------
        # FUEL CONSUMPTION -> kg/(W/s)
        # ------------------------------------------------
        "lb/hp/h": (0.45359237 / 745.7) / 3600.0,

        # ------------------------------------------------
        # ENERGY -> joules (J)
        # ------------------------------------------------
        "J": 1.0,
        "kJ": 1000.0,
        "Wh": 3600.0,
        "kWh": 3.6e6,
        "cal": 4.184,
        "kcal": 4184.0,
        "BTU": 1055.06,

        # ------------------------------------------------
        # ANGULAR ACCELERATION -> radians/second^2 (rad/s^2)
        # ------------------------------------------------
        "rad/s^2": 1.0,
        "deg/s^2": math.pi / 180.0,

        # ------------------------------------------------
        # ACCELERATION -> meters/second^2 (m/s^2)
        # ------------------------------------------------
        "m/s^2": 1.0,
        "kn/s": 0.514444,
        "ft/s^2": 0.3048,
        "g0": 9.80665,

        # ------------------------------------------------
        # DENSITY -> kilograms/meter^3 (kg/m^3)
        # ------------------------------------------------
        "kg/m^3": 1.0,
        "slug/ft^3": 515.378818,
        "lb/ft^3": 16.0185,
        "g/cm^3": 1000.0,

        # ------------------------------------------------
        # TEMPERATURE -> kelvin (K)
        # ------------------------------------------------
        "K": 1.0,

        # ------------------------------------------------
        # ELECTRICAL -> ampere (A)
        # ------------------------------------------------
        "A": 1.0,
        "mA": 1.0e-3,
        "uA": 1.0e-6,
    }
