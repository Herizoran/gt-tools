import gt.utils.system as utils_system
import gt.core.session as core_session
import gt.ui.qt_import as ui_qt
import logging
import sys
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class MayaWindowMeta(type):
    """
    Maya Window Metaclass. Used to make a QT Windows in Maya with extra functionalities such as docking and overwrites.
    It also handles the Singleton and Mac focus behaviour of the window (when in Maya)

    This metaclass modifies the base class of a QT object class to enable the dock ability in Maya.
    It dynamically adjusts the class inheritance to include "MayaQWidgetDockableMixin" based on the context
    (interactive Maya session or not).
    """

    def __new__(mcs, name, bases, attrs, base_inheritance=None, dockable=True):
        """
        Create a new class with modified inheritance for the dock ability in Maya.

        This method is responsible for creating a new class with modified base inheritance, which enables the dock
        ability in Maya. It checks whether the script is running in an interactive Maya session or not, and adjusts
        the base class accordingly. If running interactively, the "MayaQWidgetDockableMixin" is included in the
        inheritance; otherwise, only the specified base classes are used.

        Args:
            mcs (type): The metaclass instance (MayaDockableMeta).
            name (str): The name of the new class to be created.
            bases (tuple): The base classes of the new class.
            attrs (dict): The attributes and methods of the new class.
            base_inheritance (type, tuple, optional): The base class or classes to be included in inheritance.
                                                      Default is None, which becomes "QDialog".
                                                      If something is provided then that will be used instead.
            dockable (bool, optional): If active, then it will make the window dockable in Maya.
                                       If inactive, it will only attempt to delete existing windows before opening one.
                                       (In this case "MayaQWidgetDockableMixin" is not added as a base class)
        Returns:
            type: The newly created class with adjusted inheritance for Maya dock function.

        Example:
            class ToolView(metaclass=MayaWindowMeta, base_inheritance=QDialog):
            or
            class ToolView(metaclass=MayaWindowMeta):
        """
        if not core_session.is_script_in_interactive_maya():
            dockable = False
        if not base_inheritance:
            base_inheritance = (ui_qt.QtWidgets.QDialog,)
            if utils_system.is_system_macos():
                base_inheritance = (ui_qt.QtWidgets.QDialog,)
        if not isinstance(base_inheritance, tuple):
            base_inheritance = (base_inheritance,)
        if dockable:
            from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

            bases = (MayaQWidgetDockableMixin,) + base_inheritance
        else:
            bases = base_inheritance
        new_class = type(name, bases, attrs)

        # Overwrites
        base_class_vars = vars(new_class)
        if "__init__" in base_class_vars:
            original_init = base_class_vars["__init__"]

            def custom_init(self, *args, **kwargs):
                """
                Init injection (custom version of the init)
                It attempts to first close existing QT view of the same class type before opening a new one.
                It also overwrites the "show" function when using the dockable version of this metaclass.
                """
                try:
                    found_elements = get_maya_main_window_qt_elements(type(self))
                    close_ui_elements(found_elements)
                except Exception as e:
                    logger.debug(f'Unable to close previous QT elements. Issue: "{str(e)}".')

                # Overwrite Show
                _class_dir = dir(self)
                if "show" in _class_dir and dockable:
                    original_show = self.show

                    def custom_show(*args_show, **kwargs_show):
                        """
                        This is a custom function to override the original "show".
                        It calls the original "show" method with the addition of the "dockable" argument set to True.
                        Args:
                            *args_show: Additional positional arguments for the "show" method.
                            **kwargs_show: Additional keyword arguments for the "show" method.
                        """
                        if not hasattr(self, "_original_geometry"):
                            width = self.geometry().width()
                            height = self.geometry().height()
                            pos_x = self.pos().x()
                            pos_y = self.pos().y()
                            self._original_geometry = [pos_x, pos_y, width, height]
                        original_show(*args_show, **kwargs_show, dockable=True)
                        try:
                            window_parent = self.parent().parent().parent().parent().parent()
                            ui_qt.QtWidgets.QWidget.setWindowIcon(window_parent, self.windowIcon())
                            if hasattr(self, "_original_geometry"):
                                x, y, width, height = self._original_geometry
                                window_parent.move(x, y)
                                window_parent.resize(width, height)
                        except (AttributeError, ValueError):
                            pass

                    self.show = custom_show
                # Call Original Init
                original_init(self, *args, **kwargs)
                # Stay On Top macOS Tool Modality
                try:
                    if utils_system.is_system_macos() and not dockable:
                        self.setWindowFlag(ui_qt.QtLib.WindowFlag.Tool, True)
                except Exception as e:
                    logger.debug(f'Unable to set MacOS Tool Modality. Issue: "{str(e)}".')

            new_class.__init__ = custom_init
        return new_class


def get_maya_main_window_qt_elements(class_object):
    """
    Get QtWidgets.QWidget elements of a specific class from the main Maya window.

    Args:
        class_object (type or str): The class type or fully qualified string name of the class.

    Returns:
        list: A list of QtWidgets.QWidget elements matching the given class in the Maya window.
    """
    if isinstance(class_object, str):
        from gt.utils.system import import_from_path

        class_object = import_from_path(class_object)
    if not class_object:
        logger.debug(f'The requested class was not found or is "None".')
        return []
    maya_win = get_maya_main_window()
    if not maya_win:
        logger.debug(f"Maya window was not found.")
        return []
    return maya_win.findChildren(class_object)


def close_ui_elements(obj_list):
    """
    Close and delete a list of UI elements.

    Args:
        obj_list (list): A list of UI elements to be closed and deleted.
    """
    for obj in obj_list:
        try:
            obj.close()
            obj.deleteLater()
        except Exception as e:
            logger.debug(f"Unable to close and delete window object. Issue: {str(e)}")
            pass


def get_cursor_position(offset_x=0, offset_y=0):
    """
    The current position of the mouse cursor

    Args:
        offset_x: (int) A value to offset the returned x position by - in pixels
        offset_y: (int) A value to offset the returned y position by - in pixels

    Returns:
        QPoint: the current cursor position, offset by the given x and y offset values>

    """
    cursor_position = ui_qt.QtGui.QCursor().pos()
    return ui_qt.QtCore.QPoint(cursor_position.x() + offset_x, cursor_position.y() + offset_y)


def get_screen_center():
    """
    Gets the center of the screen where the parent is located.

    Returns:
        QPoint: A QPoint object with X and Y coordinates for the center of the screen.
    """
    screen_number = get_main_window_screen_number()
    screen = ui_qt.QtWidgets.QApplication.screens()[screen_number]
    center_x = screen.geometry().center().x()
    center_y = screen.geometry().center().y()
    center = ui_qt.QtCore.QPoint(center_x, center_y)
    return center


def load_custom_font(font_path, point_size=-1, weight=-1, italic=False):
    """
    Loads a custom font using its path.
    NOTE: This function can only be used after loading an instance of QApplication.
    If an instance is not found, the default font is returned instead.
    Args:
        font_path (str): Path to a font file. (Accepted formats: ".ttf", "otf")
        point_size (int, optional): Font size (default -1)
        weight (int, optional): Font weight (default -1)
        italic (bool, optional): Font italic state (default False)
    Returns:
        QFont: A QFont object for the provided custom font or a default one if the operation failed
    """
    custom_font = ui_qt.QtGui.QFont()  # default font
    if ui_qt.QtWidgets.QApplication.instance():
        # Open the font file using QFile
        file = ui_qt.QtCore.QFile(font_path)
        if file.open(ui_qt.QtLib.OpenModeFlag.ReadOnly):
            data = file.readAll()
            file.close()

            # Load the font from the memory data
            font_id = ui_qt.QtGui.QFontDatabase.addApplicationFontFromData(data)
            if font_id != -1:
                font_families = ui_qt.QtGui.QFontDatabase.applicationFontFamilies(font_id)
                if len(font_families) > 0:
                    custom_font = ui_qt.QtGui.QFont(
                        font_families[0], pointSize=point_size, weight=weight, italic=italic
                    )
        else:
            logger.debug(f"Failed to open the font file: {font_path}")
    return custom_font


def is_font_available(font_name):
    """
    Checks the font QT font database to see if the font is available in the system.
    Args:
        font_name (str): The name of the font to check. For example: "Arial"
    Returns:
        bool: True if the font is available, false if it's not.
    """
    if ui_qt.QtWidgets.QApplication.instance():
        font_db = ui_qt.QtGui.QFontDatabase()
        available_fonts = font_db.families()
        return font_name in available_fonts


def get_font(font):
    """
    Function used to get QFont object from a font path or a font name.
    This will only work if an instance of a QApplication is present.
    Args:
        font (str): This is the font to load. It can be a font name or a font path.
                    If a name is provided, and it's found in the system, then a QFont object containing it is returned.
                    If a path is provided, it attempts to add it to the font database and create a QFont object for it.
    Returns:
        QFont: A QFont object with the provided font or a default QFont object in case the operation failed.
    """
    qt_font = ui_qt.QtGui.QFont()
    if not isinstance(font, str):
        return qt_font
    if is_font_available(font):
        qt_font = ui_qt.QtGui.QFont(font)
    elif os.path.exists(font) and os.path.isfile(font):
        qt_font = load_custom_font(font)
    return qt_font


def get_maya_main_window():
    """
    Finds the instance of maya's main window
    Returns:
        QWidget: The main maya widget
    """
    from maya import OpenMayaUI as OpenMayaUI

    ptr = OpenMayaUI.MQtUtil.mainWindow()
    maya_window = ui_qt.shiboken.wrapInstance(int(ptr), ui_qt.QtWidgets.QWidget)
    return maya_window


def get_qt_color(color):
    if isinstance(color, str):
        if re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", color):  # Hex pattern (e.g. "#FF0000"):
            return ui_qt.QtGui.QColor(color)
        else:
            try:
                return ui_qt.QtGui.QColor(color)
            except Exception as e:
                logger.error(f"Unable to create QColor. Issue: {e}")
    elif isinstance(color, ui_qt.QtGui.QColor):
        return color
    elif color is not None:
        logger.error(f'Unable to create QColor. Unrecognized object type received: "{type(color)}"')


def resize_to_screen(
    window,
    percentage=20,
    width_percentage=None,
    height_percentage=None,
    dpi_scale=False,
    dpi_percentage=20,
    dpi_ignore_below_one=True,
):
    """
    Resizes the window to match a percentage of the screen size.

    Args:
        window (QDialog, any): Window to be resized.
        percentage (int, optional): The percentage of the screen size that the window should inherit.
                                    Must be a value between 0 and 100. Default is 20.
        width_percentage (int, optional): If provided, it will overwrite general set percentage when setting width.
        height_percentage (int, optional): If provided, it will overwrite general set percentage when setting height.
        dpi_scale (bool, optional): When active, it will multiply the size of the window by the DPI scale factor.
                                    It will limit it to the size of the window.
        dpi_percentage (float, int, optional): If using dpi scale, this number determines the percentage of the scale
                                               influences the window.
                                               For example: if "dpi_scale" is 10 and "dpi_percentage" is 50,
                                                            the used value for "dpi_scale" will become 5 (50% of 10)
        dpi_ignore_below_one (bool, optional): When active, it ignores DPI calculations when the scale is 1 (100%)

    Raises:
        ValueError: If the percentage is not within the range [0, 100].
    """
    if not 0 <= percentage <= 100:
        raise ValueError("Percentage should be between 0 and 100")

    if ui_qt.IS_PYSIDE6:
        screen = ui_qt.QtGui.QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        width = screen_geometry.width() * percentage / 100
        height = screen_geometry.height() * percentage / 100
    else:
        screen = ui_qt.QtWidgets.QDesktopWidget()
        screen_geometry = screen.availableGeometry(window)
        width = screen_geometry.width() * percentage / 100
        height = screen_geometry.height() * percentage / 100
    if height_percentage:
        height = screen_geometry.height() * height_percentage / 100
    if width_percentage:
        width = screen_geometry.height() * width_percentage / 100
    if dpi_scale:
        dpi_scale = get_screen_dpi_scale(get_window_screen_number(window=window))
        dpi_scale = dpi_scale * (dpi_percentage / 100)
        if dpi_ignore_below_one and dpi_scale < 1.0:
            dpi_scale = 1.0
        scaled_height = height * dpi_scale
        if scaled_height <= screen_geometry.height():
            height = scaled_height
        else:
            height = screen_geometry.height()
        scaled_width = width * dpi_scale
        if scaled_width <= screen_geometry.width():
            width = scaled_width
        else:
            width = screen_geometry.width()
    window.setGeometry(0, 0, width, height)


def get_main_window_screen_number():
    """
    Determine the screen number where the main Qt instance is located.

    Returns:
        int: Index of the screen where the main window is located.
    """
    app = ui_qt.QtWidgets.QApplication.instance()
    if app is None:
        return -1  # No instance found
    main_window = app.activeWindow() or ui_qt.QtWidgets.QMainWindow()
    if ui_qt.IS_PYSIDE6:
        screen = ui_qt.QtGui.QGuiApplication.screenAt(main_window.geometry().center())
        screen_number = ui_qt.QtGui.QGuiApplication.screens().index(screen)
        return screen_number
    else:
        screen_number = ui_qt.QtWidgets.QApplication.desktop().screenNumber(main_window)
        return screen_number


def get_window_screen_number(window):
    """
    Determines the screen number where the provided Qt windows is located.
    Args:
        window (QWidget): Qt Window used to determine screen number
    Returns:
        int: Screen number where the window is located.
    """
    if ui_qt.IS_PYSIDE6:
        # Get the QGuiApplication instance
        app = ui_qt.QtGui.QGuiApplication.instance()
        if not app:
            raise RuntimeError("QGuiApplication instance is not created.")

        # Get the widget's global position
        widget_global_pos = window.mapToGlobal(window.rect().topLeft())

        screens = app.screens()

        for i, screen in enumerate(screens):
            if screen.geometry().contains(widget_global_pos):
                return i  # Return the screen number (index)
        return -1  # Return -1 if no screen is found
    else:  # Pyside2
        desktop = ui_qt.QtWidgets.QDesktopWidget()
        screen_number = desktop.screenNumber(window)
        return screen_number


def center_window(window):
    """
    Moves the given window to the center of the screen.

    Args:
        window (QDialog, any): The window to be centered on the screen.
    """
    rect = window.frameGeometry()
    center_position = get_screen_center()
    rect.moveCenter(center_position)
    window.move(rect.topLeft())


def update_formatted_label(
    target_label,
    text,
    text_size=None,
    text_color=None,
    text_bg_color=None,
    text_is_bold=False,
    output_text="",
    output_size=None,
    output_color=None,
    output_bg_color=None,
    text_output_is_bold=False,
    overall_alignment="center",
):
    """
    Updates the target QLabel with formatted text containing a text and text output.
    e.g. "Text: TextOutput" or "Status: OK"

    Args:
       target_label (QtWidgets.QLabel): The QLabel to update with the formatted text.
       text (str): The text to be displayed before the output_text.
       text_size (int, optional): The font size of the text.
       text_color (str, optional): The color of the text.
       text_bg_color (str, optional): A color fo the text background.
       text_is_bold (bool, optional): Determines if the text should be bold or not. Default: False.
       output_text (str, optional): The text output to be displayed after the text.
       output_size (int, optional): The font size of the text output.
       output_color (str, optional): The color of the text output.
       output_bg_color (str, optional): The color of the text output background.
       text_output_is_bold (bool, optional): Determines if the text output should be bold or not. Default: False.
       overall_alignment (str, optional): The overall alignment of the formatted text. Default is "center".
                                          Possible values are "left", "center", and "right".
    """
    _html = f"<html><div style='text-align:{overall_alignment};'>"
    if text_is_bold:
        _html += "<b>"
    _html += f"<font"
    # Text
    if text_size:
        _html += f" size='{str(text_size)}'"
    if text_color:
        _html += f" color='{text_color}'"
    if text_bg_color:
        _html += f" style='background-color:{text_bg_color};'"
    _html += f">{text}</font>"
    if text_is_bold:
        _html += "</b>"
    # Output Text
    if output_text:
        if text_output_is_bold:
            _html += "<b>"
        _html += "<font"
        if output_size:
            _html += f" size='{str(output_size)}'"
        if output_color:
            _html += f" color='{output_color}'"
        if output_bg_color:
            _html += f" style='background-color:{output_bg_color};'"
        _html += f">{output_text}</font>"
        if text_output_is_bold:
            _html += "</b>"
    _html += "</div></html>"
    target_label.setText(_html)


def load_and_scale_pixmap(image_path, scale_percentage=100, exact_height=None, exact_width=None):
    """
    Load an image from the given path, and scale it by the specified percentage,
    then return the scaled QPixmap.

    Args:
        image_path (str): Path to the image file.
        scale_percentage (float): Percentage to scale the image by. (Default is 100%, which is the original resolution)
                                  100 = Same resolution. 50 = half the resolution. 200 = double the resolution.
        exact_height (int, optional): If provided, it will overwrite scale percentage and use this height instead.
        exact_width (int, optional): If provided, it will overwrite scale percentage and use this width instead.

    Returns:
        QPixmap: Scaled QPixmap object with loaded image (Using SmoothTransformation mode)
    """
    pixmap = ui_qt.QtGui.QPixmap(image_path)
    pixmap_height = pixmap.height()
    pixmap_width = pixmap.width()

    scaled_width = int(pixmap_width * (scale_percentage / 100))
    scaled_height = int(pixmap_height * (scale_percentage / 100))

    if exact_height and isinstance(exact_height, int):
        scaled_height = exact_height
    if exact_width and isinstance(exact_width, int):
        scaled_width = exact_width

    scaled_pixmap = pixmap.scaled(scaled_width, scaled_height, mode=ui_qt.QtLib.TransformationMode.SmoothTransformation)
    return scaled_pixmap


class QtApplicationContext:
    """
    A context manager for managing a QtWidgets.QApplication.

    Usage:
    with QtContext() as context:
        # Your Qt application code here

    When the context is exited, the Qt application will be properly closed.

    Attributes:
        app (QtWidgets.QApplication): The QApplication instance.
    """

    def __init__(self):
        """Initializes QtApplicationContext"""
        self.app = None
        self.is_script_in_interactive_maya = core_session.is_script_in_interactive_maya()
        self.parent = None

    def is_in_interactive_maya(self):
        """
        Gets if script is running from inside of Maya or not (interactive Maya, not PyMaya)
        Returns:
            bool: True if inside Maya, False if not (also False if running it in mayapy.exe - Not interactive)
        """
        return self.is_script_in_interactive_maya

    def get_parent(self):
        """
        Gets the parent. (Maya window if inside Maya, or None if outside)
        Returns:
            str or None: Parent to be used by a QtWidget or element.
        """
        return self.parent

    def __enter__(self):
        """
        Initialize the QApplication when entering the context.

        Returns:
            QtApplicationContext: The QtContext instance.
        """
        if self.is_script_in_interactive_maya:
            self.parent = get_maya_main_window()
        else:
            logger.debug("Running Qt outside Maya. Initializing QApplication.")
            _app_instance = ui_qt.QtWidgets.QApplication.instance()
            if not _app_instance:
                self.app = ui_qt.QtWidgets.QApplication(sys.argv)
            else:
                self.app = _app_instance
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Clean up and close the QApplication when exiting the context.

        Args:
            exc_type (type): The type of the exception raised, if any.
            exc_value (Exception): The exception object raised, if any.
            traceback (traceback): The traceback object associated with the exception.

        Returns:
            bool: True to suppress the exception, False to propagate it.
        """
        if self.app and not self.is_script_in_interactive_maya:
            sys.exit(self.app.exec_())
        if exc_type is not None:
            logger.warning(f"An exception of type {exc_type} occurred with value: {exc_value}")
        return False


def create_color_pixmap(color, width=24, height=24):
    """
    Creates a QIcon for a given QColor with the specified icon size.

    Args:
        color: The QColor for which to create the icon.
        width (int, optional): The size of the pixmap in pixels (width). Defaults to 24.
        height (int, optional): The size of the pixmap in pixels (height). Defaults to 24.

    Returns:
        The created QPixmap with the specified color, or None if color is invalid.
    """
    if not isinstance(color, ui_qt.QtGui.QColor):
        logger.debug("Invalid color provided. Please provide a valid QColor object.")
        return None

    pixmap = ui_qt.QtGui.QPixmap(width, height)
    pixmap.fill(color)
    return pixmap


def create_color_icon(color, width=24, height=24):
    """
    Creates a QIcon for a given QColor with the specified icon size.

    Args:
        color: The QColor for which to create the icon.
        width (int, optional): The size of the icon in pixels (width). Defaults to 24.
        height (int, optional): The size of the icon in pixels (height). Defaults to 24.

    Returns:
        The created QIcon with the specified color, or None if color is invalid.

    Example:
        # Create a color icon with the default size (24x24) using a red QColor
        red_color = QColor(255, 0, 0)
        red_icon = create_color_icon(red_color)

        # Create a color icon with a custom size (32x32) using a blue QColor
        blue_color = QColor(0, 0, 255)
        blue_icon = create_color_icon(blue_color, icon_size=32)
    """
    if not isinstance(color, ui_qt.QtGui.QColor):
        logger.debug("Invalid color provided. Please provide a valid QColor object.")
        return None

    pixmap = create_color_pixmap(color=color, width=width, height=height)
    icon = ui_qt.QtGui.QIcon(pixmap)
    return icon


def get_screen_dpi_scale(screen_number):
    """
    Calculate the scale factor of the DPI for a given screen number.

    Args:
        screen_number (int): The index of the screen for which to calculate DPI percentage.

    Returns:
        float: The scale factor of DPI for the specified screen.

    Raises:
        ValueError: If the screen number is out of range.
    """
    app = ui_qt.QtWidgets.QApplication.instance()
    screen_list = app.screens()

    if 0 <= screen_number < len(screen_list):
        target_screen = screen_list[screen_number]
        standard_dpi = 96.0
        dpi_scale_factor = target_screen.logicalDotsPerInch() / standard_dpi
        return dpi_scale_factor
    else:
        raise ValueError("Invalid screen number. Please provide a valid screen number.")


def expand_tree_item_recursively(item):
    """
    Recursively expands all child items in a tree view starting from the given item.

    This function sets the expansion state of the provided item to True and then
    recursively expands all its child items, if any.

    Args:
        item (QTreeWidgetItem): The root item from which to start expanding child items.

    Example:
        # Expand all child items in a tree view
        root_item = QTreeWidgetItem()
        expand_tree_item_recursively(root_item)
    """
    if item is not None:
        item.setExpanded(True)
        for i in range(item.childCount()):
            expand_tree_item_recursively(item.child(i))


class QHeaderWithWidgets(ui_qt.QtWidgets.QHeaderView):
    """
    Subclass of QHeaderView with the ability to set custom widgets for individual sections.

    Attributes:
        widget_index_dict (dict): A dictionary to store custom widgets with their corresponding section indices.
    """

    def __init__(self, parent=None):
        """
        Constructor for QHeaderWithWidgets.

        Args:
            parent (QWidget): The parent widget. Defaults to None.
        """
        super().__init__(ui_qt.QtLib.Orientation.Horizontal, parent)
        self.widget_index_dict = {}

    def add_widget(self, index, widget):
        """
        Set a custom widget for a specific section.

        Args:
            index (int): The index of the section.
            widget (QWidget): The custom widget to be set.
        """
        if not isinstance(index, int) or index < 0:
            return
        self.widget_index_dict[index] = widget
        widget.setParent(self)
        widget.setVisible(False)

    def paintSection(self, painter, rect, logical_index):
        """
        Paint the section, and if a custom widget is set for the section, paint and display the widget.

        Args:
            painter (QPainter): The painter object for rendering.
            rect (QRect): The rectangle defining the section's area.
            logical_index (int): The logical index of the section.

        """
        super().paintSection(painter, rect, logical_index)
        if logical_index in self.widget_index_dict:
            widget = self.widget_index_dict.get(logical_index)
            if widget:
                widget.setVisible(True)
                widget.setGeometry(rect)


class ConfirmableQLineEdit(ui_qt.QtWidgets.QLineEdit):
    """
    Custom QLineEdit that prevents the pressing of the Enter key to trigger other undesired behaviours.
    """

    def keyPressEvent(self, event: ui_qt.QtGui.QKeyEvent):
        if event.key() == ui_qt.QtLib.Key.Key_Enter or event.key() == ui_qt.QtLib.Key.Key_Return:
            event.accept()  # Prevent the default behavior of the Enter key
            self.editingFinished.emit()
        else:
            super().keyPressEvent(event)  # Continue with the default behavior for other keys


class QIntSlider(ui_qt.QtWidgets.QSlider):
    """A QSlider subclass that emits integer values.

    This class provides a slider that operates over a range of integer values.
    It emits a signal with an integer value when the slider is moved.

    Attributes:
        intValueChanged (QtCore.Signal): Custom signal that emits an integer value when the slider changes.
    """

    intValueChanged = ui_qt.QtCore.Signal(int)

    def __init__(self, orientation=ui_qt.QtLib.Orientation.Horizontal, parent=None):
        """
        Initializes the QIntSlider.

        Args:
            orientation (Qt.Orientation): The orientation of the slider. Defaults to Qt.Horizontal.
            parent (QtWidgets.QWidget): The parent widget of the slider. Defaults to None.
        """
        super().__init__(orientation, parent)

        # Default range for integers
        self._min_int = 0
        self._max_int = 100
        self.setRange(self._min_int, self._max_int)
        self.linked_spin_box = None

        # Connect the QSlider's valueChanged signal to emit integer values
        self.valueChanged.connect(self.emit_int_value)

    def emit_int_value(self, value):
        """
        Emits the intValueChanged signal with the slider's integer value.

        This method emits the custom signal with the current slider value.

        Args:
            value (int): The integer value of the slider.
        """
        self.intValueChanged.emit(value)

    def set_int_value(self, int_value):
        """
        Sets the slider position based on an integer value.

        Args:
            int_value (int): The integer value to set on the slider.
        """
        self.setValue(int_value)

    def set_int_range(self, min_int, max_int):
        """
        Sets the range of the slider to represent the given integer range.

        Args:
            min_int (int): The minimum integer value of the slider.
            max_int (int): The maximum integer value of the slider.
        """
        self._min_int = min_int
        self._max_int = max_int
        self.setRange(self._min_int, self._max_int)
        self.set_int_value(self._min_int)  # Reset the slider to min value

        # Update the linked spin box range if linked
        if self.linked_spin_box:
            self.linked_spin_box.setRange(self._min_int, self._max_int)

    def int_value(self):
        """
        Returns the current slider value as an integer.

        Returns:
            int: The current slider value.
        """
        return self.value()

    def link_spin_box(self, spin_box):
        """
        Links a QSpinBox to the slider for synchronized updates.

        Args:
            spin_box (QSpinBox): The QSpinBox to link with the slider.
        """
        self.linked_spin_box = spin_box
        # Update the spin box to reflect the current slider value
        spin_box.setValue(self.int_value())
        spin_box.setRange(self._min_int, self._max_int)  # Set initial range
        spin_box.valueChanged.connect(self.set_int_value_from_spin_box)
        self.intValueChanged.connect(self.set_spin_box_int_value)

    def set_int_value_from_spin_box(self, value):
        """
        Updates the slider position based on the integer value from the linked spin box.

        Args:
            value (int): The integer value from the spin box.
        """
        self.set_int_value(value)

    def set_spin_box_int_value(self, value):
        """
        Updates the spin box value based on the slider position.

        Args:
            value (int): The integer value to set in the spin box.
        """
        if self.linked_spin_box:
            self.linked_spin_box.setValue(self.int_value())


class QDoubleSlider(ui_qt.QtWidgets.QSlider):
    """A QSlider subclass that emits double values.

    This class provides a slider that operates over a range of double values with a specified precision.
    It emits a signal with a double value when the slider is moved.

    Attributes:
        doubleValueChanged (QtCore.Signal): Custom signal that emits a double value when the slider changes.
    """

    doubleValueChanged = ui_qt.QtCore.Signal(float)

    def __init__(self, orientation=ui_qt.QtLib.Orientation.Horizontal, parent=None):
        """
        Initializes the QDoubleSlider.

        Args:
            orientation (Qt.Orientation): The orientation of the slider. Defaults to Qt.Horizontal.
            parent (QtWidgets.QWidget): The parent widget of the slider. Defaults to None.
        """
        super().__init__(orientation, parent)

        # Default range to handle doubles with desired precision
        self._scale = 1000.0
        self._min_double = 0.0
        self._max_double = 1.0
        self.setRange(0, int(self._scale * (self._max_double - self._min_double)))
        self.linked_spin_box = None

        # Connect the QSlider's valueChanged signal to emit double values
        self.valueChanged.connect(self.emit_double_value)

    def emit_double_value(self, value):
        """
        Emits the doubleValueChanged signal with the slider's double value.

        This method converts the slider's integer value to a double and emits the custom signal.

        Args:
            value (int): The integer value of the slider.
        """
        double_value = self._min_double + (value / self._scale)
        self.doubleValueChanged.emit(double_value)

    def set_double_value(self, double_value):
        """
        Sets the slider position based on a double value.

        Args:
            double_value (float): The double value to set on the slider.
        """
        int_value = int((double_value - self._min_double) * self._scale)
        self.setValue(int_value)

    def set_double_range(self, min_double, max_double):
        """
        Sets the range of the slider to represent the given double range.

        Args:
            min_double (float): The minimum double value of the slider.
            max_double (float): The maximum double value of the slider.
        """
        self._min_double = min_double
        self._max_double = max_double
        self._scale = 1000.0  # Or another value depending on desired precision
        self.setRange(0, int(self._scale * (self._max_double - self._min_double)))
        self.set_double_value(self._min_double)  # Reset the slider to min value

        # Update the linked spin box range if linked
        if self.linked_spin_box:
            self.linked_spin_box.setRange(self._min_double, self._max_double)

    def double_value(self):
        """
        Returns the current slider value as a double.

        Returns:
            float: The current slider value represented as a double.
        """
        return self._min_double + (self.value() / self._scale)

    def link_spin_box(self, spin_box):
        """
        Links a QDoubleSpinBox to the slider for synchronized updates.

        Args:
            spin_box (QDoubleSpinBox): The QDoubleSpinBox to link with the slider.
        """
        self.linked_spin_box = spin_box
        # Update the spin box to reflect the current slider value
        spin_box.setValue(self.double_value())
        spin_box.setRange(self._min_double, self._max_double)  # Set initial range
        spin_box.valueChanged.connect(self.set_double_value_from_spin_box)
        self.doubleValueChanged.connect(self.set_spin_box_double_value)

    def set_double_value_from_spin_box(self, value):
        """
        Updates the slider position based on the double value from the linked spin box.

        Args:
            value (float): The double value from the spin box.
        """
        self.set_double_value(value)

    def set_spin_box_double_value(self, value):
        """
        Updates the spin box value based on the slider position.

        Args:
            value (float): The double value to set in the spin box.
        """
        if self.linked_spin_box:
            self.linked_spin_box.setValue(self.double_value())


if __name__ == "__main__":
    with QtApplicationContext():
        a_window = ui_qt.QtWidgets.QMainWindow()
        resize_to_screen(a_window, percentage=40)
        center_window(a_window)
        print(get_main_window_screen_number())
        print(get_screen_center())
        a_window.show()
        # close_ui_elements([a_window])  # Working, as it closes
