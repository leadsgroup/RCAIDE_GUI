from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget,QTreeWidgetItem,QFrame, QMainWindow, QApplication, QMainWindow, QTabWidget, QFileDialog, QMenu

def add_line(shape = "HLine", shadow = "Sunken", color = "gray", height = "20"):
    line = QFrame()
    shape_dict = {
        'NoFrame': QFrame.Shape.NoFrame,
        'Box': QFrame.Shape.Box,
        'Panel': QFrame.Shape.Panel,
        'StyledPanel': QFrame.Shape.StyledPanel,
        'HLine': QFrame.Shape.HLine,
        'VLine': QFrame.Shape.VLine
    }
    shadow_dict = {
        'Plain': QFrame.Shadow.Plain,
        'Raised': QFrame.Shadow.Raised,
        'Sunken': QFrame.Shadow.Sunken
    }
    if shape not in shape_dict:
        raise TypeError("Have problem in shape format, shape should be 'NoFrame , Box , Panel , StyledPanel , HLine, VLine'" )
    #shape:NoFrame , Box , Panel , StyledPanel , HLine, VLine
    line.setFrameShape(shape_dict[shape])  
    if shadow not in shadow_dict:
        raise TypeError("Have problem in shadow format, shadow should be 'Plain , Raised and Sunken'" )
    #shadow:Plain , Raised and Sunken
    line.setFrameShadow(shadow_dict[shadow]) 
    try:
        line.setStyleSheet(f"background-color: {color}; height: {height}px;")
    except:
        raise TypeError("Color format:1.Specific color like:red, blue, lightblue. 2.Hex Code like: #FF5733. 3. RGB like: rgb(255, 87, 51)." )
    return line

def add_title(text, font_weight="bold", color = "black", font_size="20", Alignment="AlignLeft"):
    title = QLabel(text)
    Alignment_dict={
        "AlignLeft":Qt.AlignmentFlag.AlignLeft,
        "AlignRight": Qt.AlignmentFlag.AlignRight,
        "AlignHCenter":Qt.AlignmentFlag.AlignHCenter,
        "AlignJustify":Qt.AlignmentFlag.AlignJustify,
        "AlignTop":Qt.AlignmentFlag.AlignTop,
        "AlignBottom":Qt.AlignmentFlag.AlignBottom,
        "AlignVCenter":Qt.AlignmentFlag.AlignCenter,
        "AlignBaseline":Qt.AlignmentFlag.AlignVCenter
    }
    if Alignment not in Alignment_dict:
        raise TypeError("Have problem in Alignment format, Alignment should be 'AlignLeft, AlignRight, AlignHCenter, AlignJustify, AlignTop, AlignBottom, AlignVCenter, AlignBaseline'" )
    else:     
        title.setAlignment(Alignment_dict[Alignment])
    try:
        title.setStyleSheet(f"font-size: {font_size}px; font-weight: {font_weight}; color: {color};")
    except:
        raise TypeError("font-size format:integer, font-weight format:'bold',Makes the text bold, Color format:1.Specific color like:red, blue, lightblue. 2.Hex Code like: #FF5733. 3. RGB like: rgb(255, 87, 51)." )    
    return title

def add_subtitle(text, font_weight="bold", color = "black", font_size="15", Alignment="AlignLeft"):
    subtitle = QLabel(text)
    Alignment_dict={
        "AlignLeft":Qt.AlignmentFlag.AlignLeft,
        "AlignRight": Qt.AlignmentFlag.AlignRight,
        "AlignHCenter":Qt.AlignmentFlag.AlignHCenter,
        "AlignJustify":Qt.AlignmentFlag.AlignJustify,
        "AlignTop":Qt.AlignmentFlag.AlignTop,
        "AlignBottom":Qt.AlignmentFlag.AlignBottom,
        "AlignVCenter":Qt.AlignmentFlag.AlignCenter,
        "AlignBaseline":Qt.AlignmentFlag.AlignVCenter
    }
    if Alignment not in Alignment_dict:
        raise TypeError("Have problem in Alignment format, Alignment should be 'AlignLeft, AlignRight, AlignHCenter, AlignJustify, AlignTop, AlignBottom, AlignVCenter, AlignBaseline'" )
    else:     
        subtitle.setAlignment(Alignment_dict[Alignment])
    try:
        subtitle.setStyleSheet(f"font-size: {font_size}px; font-weight: {font_weight}; color: {color};")
    except:
        raise TypeError("font-size format:integer, font-weight format:'bold',Makes the text bold, Color format:1.Specific color like:red, blue, lightblue. 2.Hex Code like: #FF5733. 3. RGB like: rgb(255, 87, 51)." )    
    return subtitle


#This is a function help build header.It has three inputs. The first input is from QMainWindow(), usually it is "self".
#The second input is the name for this window. The third input is menu_list. like["File","Documentation"].
def add_header(window, window_name, menu_list = None):
    window.setWindowTitle(window_name)
    menubar = window.menuBar()
    if menubar is None:
        return 
    if menu_list:
        for i in menu_list:
            menubar.addMenu(i)
    return 

#After use this function,programmer can find exact menu. 
def find_menu_variable(window, target_menu):
    menubar = window.menuBar()
    if menubar is None:
        print("No menu bar found.")
        return
    menus = [child for child in menubar.children() if isinstance(child, QMenu)]
    for menu in menus:
        if menu.title() == target_menu:
            return menu

if __name__ == '__main__':
    app = QApplication([])
    window = QMainWindow()
    add_header(window, "My Application", menu_list=["File", "Edit", "View"])
    file_mune = find_menu_variable(window,"File")
    file_mune.addAction("Quit")
    window.show()
    app.exec()


