import numpy as np
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


class Units:
    class Length:
        METER = ("m", lambda x: x)
        CENTIMETER = ("cm", lambda x: x * 0.01)
        MILLIMETER = ("mm", lambda x: x * 0.001)
        INCH = ("in", lambda x: x * 0.0254)
        FOOT = ("ft", lambda x: x * 0.3048)

        unit_list = [METER, CENTIMETER, MILLIMETER, INCH, FOOT]

    class Area:
        SQUARE_METER = ("m²", lambda x: x)
        SQUARE_CENTIMETER = ("cm²", lambda x: x * 0.0001)
        SQUARE_MILLIMETER = ("mm²", lambda x: x * 0.000001)
        SQUARE_INCH = ("in²", lambda x: x * 0.00064516)
        SQUARE_FOOT = ("ft²", lambda x: x * 0.092903)

        unit_list = [SQUARE_METER, SQUARE_CENTIMETER, SQUARE_MILLIMETER, SQUARE_INCH, SQUARE_FOOT]

    class Volume:
        CUBIC_METER = ("m³", lambda x: x)
        CUBIC_CENTIMETER = ("cm³", lambda x: x * 0.000001)
        CUBIC_MILLIMETER = ("mm³", lambda x: x * 0.000000001)
        CUBIC_INCH = ("in³", lambda x: x * 0.0000163871)
        CUBIC_FOOT = ("ft³", lambda x: x * 0.0283168)

        unit_list = [CUBIC_METER, CUBIC_CENTIMETER, CUBIC_MILLIMETER, CUBIC_INCH, CUBIC_FOOT]

    class Temperature:
        KELVIN = ("K", lambda x: x)
        CELSIUS = ("°C", lambda x: x - 273.15)
        FAHRENHEIT = ("°F", lambda x: (x - 32) * 9 / 5 + 273.15)
        RANKINE = ("°R", lambda x: x * 1.8)

        unit_list = [KELVIN, CELSIUS, FAHRENHEIT, RANKINE]

    class Mass:
        KILOGRAM = ("kg", lambda x: x)
        GRAM = ("g", lambda x: x * 0.001)
        MILLIGRAM = ("mg", lambda x: x * 0.000001)
        OUNCE = ("oz", lambda x: x * 0.0283495)
        POUND = ("lb", lambda x: x * 0.453592)

        unit_list = [KILOGRAM, GRAM, MILLIGRAM, OUNCE, POUND]

    class Time:
        MILLISECOND = ("ms", lambda x: x * 0.001)
        MICROSECOND = ("µs", lambda x: x * 0.000001)
        SECOND = ("s", lambda x: x)
        MINUTE = ("min", lambda x: x * 60)
        HOUR = ("h", lambda x: x * 3600)
        DAY = ("d", lambda x: x * 86400)

        unit_list = [SECOND, MINUTE, HOUR, DAY, MILLISECOND, MICROSECOND]

    class Velocity:
        METER_PER_SECOND = ("m/s", lambda x: x)
        KILOMETER_PER_HOUR = ("km/h", lambda x: x / 3.6)
        MILE_PER_HOUR = ("mph", lambda x: x * 0.44704)
        KNOT = ("kn", lambda x: x * 0.514444)

        unit_list = [METER_PER_SECOND, KILOMETER_PER_HOUR, MILE_PER_HOUR, KNOT]

    class Acceleration:
        METER_PER_SECOND_SQUARED = ("m/s²", lambda x: x)
        # KILOMETER_PER_HOUR_SQUARED = ("km/h²", lambda x: x / 3.6)
        # MILE_PER_HOUR_SQUARED = ("mph²", lambda x: x * 0.44704)
        KNOTS_PER_SECOND = ("kn/s", lambda x: x * 0.514444)

        unit_list = [METER_PER_SECOND_SQUARED, KNOTS_PER_SECOND]
    
    class Force:
        NEWTON = ("N", lambda x: x)
        KILONEWTON = ("kN", lambda x: x * 1000)
        MEGANEWTON = ("MN", lambda x: x * 1000000)
        
        unit_list = [NEWTON, KILONEWTON, MEGANEWTON]

    class Energy:
        JOULE = ("J", lambda x: x)
        KILOJOULE = ("kJ", lambda x: x * 1000)
        WATT_HOUR = ("Wh", lambda x: x * 3600)
        KILOWATT_HOUR = ("kWh", lambda x: x * 3600000)
        CALORIE = ("cal", lambda x: x * 4184)
        KILOCALORIE = ("kcal", lambda x: x * 4184000)

        unit_list = [JOULE, KILOJOULE, WATT_HOUR, KILOWATT_HOUR, CALORIE, KILOCALORIE]

    class Current:
        AMPERE = ("A", lambda x: x)
        MILLIAMPERE = ("mA", lambda x: x * 0.001)
        MICROAMPERE = ("µA", lambda x: x * 0.000001)

        unit_list = [AMPERE, MILLIAMPERE, MICROAMPERE]
        
    class Pressure:
        PASCAL = ("Pa", lambda x: x)
        KILOPASCAL = ("kPa", lambda x: x * 1000)
        MEGAPASCAL = ("MPa", lambda x: x * 1000000)
        BAR = ("bar", lambda x: x * 100000)
        ATMOSPHERE = ("atm", lambda x: x * 101325)
        POUND_PER_SQUARE_INCH = ("psi", lambda x: x * 6894.76)

        unit_list = [PASCAL, KILOPASCAL, MEGAPASCAL, BAR, ATMOSPHERE, POUND_PER_SQUARE_INCH]

    class Unitless:
        NONE = ("", lambda x: x)
        PERCENT = ("%", lambda x: x / 100)
        unit_list = [NONE, PERCENT]

    class Count:
        UNIT = ("Unit", lambda x: x)
        unit_list = [UNIT]

    class Angle:
        RADIAN = ("rad", lambda x: x)
        DEGREE = ("°", lambda x: np.deg2rad(x))
        unit_list = [RADIAN, DEGREE]

    class Boolean:
        pass
