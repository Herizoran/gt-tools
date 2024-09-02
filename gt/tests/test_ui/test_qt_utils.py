import gt.ui.qt_import as ui_qt
from unittest.mock import patch, MagicMock, Mock
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
import gt.ui.qt_utils as ui_qt_utils
from gt.ui import qt_utils


class TestQtUtilities(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = ui_qt.QtWidgets.QApplication.instance()
        if not app:
            cls.app = ui_qt.QtWidgets.QApplication(sys.argv)

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    def test_base_inheritance_default(self):
        """
        Test that MayaWindowMeta sets 'base_inheritance' to QDialog by default.
        """
        new_class = ui_qt_utils.MayaWindowMeta("TestBaseInheritanceDefault", (object,), {})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, ui_qt.QtWidgets.QDialog))

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    @patch("gt.utils.system.is_system_macos", MagicMock(return_value=False))
    def test_base_inheritance_non_macos(self):
        new_class = ui_qt_utils.MayaWindowMeta(name="TestBaseInheritanceNonMacOS", bases=(object,), attrs={})
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, ui_qt.QtWidgets.QDialog))

    @patch("gt.core.session.is_script_in_interactive_maya", MagicMock(return_value=True))
    def test_base_inheritance_widget(self):
        import gt.ui.qt_import as ui_qt

        new_class = ui_qt_utils.MayaWindowMeta(
            name="TestBaseInheritance", bases=(object,), attrs={}, base_inheritance=(ui_qt.QtWidgets.QWidget,)
        )
        from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

        self.assertEqual(new_class.__bases__, (MayaQWidgetDockableMixin, ui_qt.QtWidgets.QWidget))

    @patch("gt.utils.system.import_from_path")
    @patch("gt.ui.qt_utils.get_maya_main_window")
    def test_with_valid_class_type(self, mock_get_maya_main_window, mock_import_from_path):
        mock_maya_window = MagicMock()
        mock_maya_window.findChildren.return_value = ["child_one", "child_two"]
        mock_import_from_path.return_value = Mock()
        mock_get_maya_main_window.return_value = mock_maya_window

        # Call the function
        result = qt_utils.get_maya_main_window_qt_elements(Mock())

        # Expected result
        expected = ["child_one", "child_two"]

        # Assert the result
        self.assertEqual(result, expected)

    def test_close_ui_elements_success(self):
        # Create mock UI elements
        ui_element1 = Mock()
        ui_element2 = Mock()

        # Call the function with the mock elements
        obj_list = [ui_element1, ui_element2]
        qt_utils.close_ui_elements(obj_list)

        # Assert that close() and deleteLater() methods were called for each UI element
        ui_element1.close.assert_called_once()
        ui_element1.deleteLater.assert_called_once()
        ui_element2.close.assert_called_once()
        ui_element2.deleteLater.assert_called_once()

    @patch.object(QtGui.QCursor, "pos", return_value=ui_qt.QtCore.QPoint(100, 200))
    def test_get_cursor_position_no_offset(self, mock_cursor):
        expected = ui_qt.QtCore.QPoint(100, 200)
        result = qt_utils.get_cursor_position()
        self.assertEqual(expected, result)

    @patch.object(QtGui.QCursor, "pos", return_value=ui_qt.QtCore.QPoint(100, 200))
    def test_get_cursor_position_with_offset(self, mock_cursor):
        offset_x = 10
        offset_y = 20
        expected = ui_qt.QtCore.QPoint(110, 220)
        result = qt_utils.get_cursor_position(offset_x, offset_y)
        self.assertEqual(expected, result)

    @patch("gt.ui.qt_utils.get_main_window_screen_number", return_value=0)
    @patch.object(ui_qt.QtWidgets.QApplication, "screens")
    def test_get_screen_center(self, mock_screens, mock_get_main_window_screen_number):
        expected = ui_qt.QtCore.QPoint(100, 200)
        mocked_xy = MagicMock()
        mocked_xy.x.return_value = 100
        mocked_xy.y.return_value = 200
        mocked_center = MagicMock()
        mocked_center.center.return_value = mocked_xy
        mocked_geometry = MagicMock()
        mocked_geometry.geometry.return_value = mocked_center
        mock_screens.return_value = [mocked_geometry]
        result = qt_utils.get_screen_center()
        self.assertEqual(expected, result)

    @patch("gt.ui.qt_import.QtGui.QFont", return_value="mocked_font")
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance", return_value=MagicMock())
    @patch("gt.ui.qt_import.QtGui.QFontDatabase.addApplicationFontFromData", return_value=0)
    @patch("gt.ui.qt_import.QtGui.QFontDatabase.applicationFontFamilies", return_value=["CustomFont"])
    def test_load_custom_font_success(self, mock_font_from_data, mock_app_font_families, mock_app, mock_font):
        custom_font = qt_utils.load_custom_font(
            "custom_font.ttf", point_size=12, weight=ui_qt.QtLib.Font.Bold, italic=True
        )
        expected_font = "mocked_font"
        self.assertEqual(expected_font, custom_font)

    def test_font_available(self):
        # Test if a font that should be available returns True
        font_name = "Arial"
        expected_result = True
        result = qt_utils.is_font_available(font_name)
        self.assertEqual(result, expected_result)

    def test_font_not_available(self):
        # Test if a font that should not be available returns False
        font_name = "NonExistentFont123"
        expected_result = False
        result = qt_utils.is_font_available(font_name)
        self.assertEqual(result, expected_result)

    @patch("gt.ui.qt_utils.is_font_available", return_value=True)
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_with_font_name(self, mock_instance, mock_is_font_available):
        mock_instance.return_value = MagicMock()

        font_name = "Arial"
        font = qt_utils.get_font(font_name)

        expected_font = ui_qt.QtGui.QFont(font_name)

        self.assertEqual(font, expected_font)

    @patch("gt.ui.qt_utils.is_font_available", return_value=False)
    @patch("gt.ui.qt_utils.load_custom_font", return_value=ui_qt.QtGui.QFont("CustomFont"))
    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_with_font_path(self, mock_instance, mock_load_custom_font, mock_is_font_available):
        mock_instance.return_value = MagicMock()
        import gt.ui.resource_library as ui_res_lib

        result = qt_utils.get_font(ui_res_lib.Font.roboto)
        expected_font = ui_qt.QtGui.QFont("CustomFont")
        self.assertEqual(expected_font, result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication.instance")
    def test_get_font_invalid_font(self, mock_instance):
        mock_instance.return_value = MagicMock()

        invalid_font = 123  # Invalid input type
        font = qt_utils.get_font(invalid_font)

        expected_font = ui_qt.QtGui.QFont()  # Default font

        self.assertEqual(font, expected_font)

    def test_get_qt_color_valid_hex_color(self):
        # Test with a valid hex color
        expected = ui_qt.QtGui.QColor("#FF0000")
        result = qt_utils.get_qt_color("#FF0000")
        self.assertEqual(expected, result)

    def test_get_qt_color_valid_color_name(self):
        # Test with a valid color name
        expected = ui_qt.QtGui.QColor("red")
        result = qt_utils.get_qt_color("red")
        self.assertEqual(expected, result)

    def test_get_qt_color_invalid_color_input(self):
        # Test with an invalid color input
        expected = None
        result = qt_utils.get_qt_color("invalid_color")
        self.assertEqual(expected, result)

    def test_get_qt_color_color_object_input(self):
        # Test with a QColor object as input
        input_color = ui_qt.QtGui.QColor("#00FF00")
        expected = input_color
        result = qt_utils.get_qt_color(input_color)
        self.assertEqual(expected, result)

    def test_get_qt_color_none_input(self):
        # Test with None as input
        expected = None
        result = qt_utils.get_qt_color(None)
        self.assertEqual(expected, result)

    def test_get_qt_color_library(self):
        # Test with None as input
        import gt.ui.resource_library as ui_res_lib

        expected = ui_qt.QtGui.QColor(ui_res_lib.Color.RGB.red)
        result = qt_utils.get_qt_color(ui_res_lib.Color.RGB.red)
        self.assertEqual(expected, result)

    @patch("gt.ui.qt_import.QtWidgets.QDesktopWidget")
    def test_resize_to_screen_valid_percentage(self, mock_desktop_widget):
        mock_screen = MagicMock()
        mock_screen.width.return_value = 100
        mock_screen.height.return_value = 200
        mock_geo = MagicMock()
        mock_geo.availableGeometry.return_value = mock_screen
        mock_desktop_widget.return_value = mock_geo
        window = MagicMock()
        qt_utils.resize_to_screen(window, percentage=50)
        expected_width = 50
        expected_height = 100
        self.assertEqual(window.setGeometry.call_args[0][2], expected_width)
        self.assertEqual(window.setGeometry.call_args[0][3], expected_height)

    def test_resize_to_screen_invalid_percentage(self):
        window = Mock()
        with self.assertRaises(ValueError):
            qt_utils.resize_to_screen(window, percentage=110)

    @patch("gt.ui.qt_import.QtWidgets.QApplication")
    def test_get_main_window_screen_number(self, mock_instance):
        mock_screen_number = MagicMock()
        mock_screen_number.screenNumber.return_value = 10
        mock_instance.instance.return_value = MagicMock()
        mock_instance.desktop.return_value = mock_screen_number
        result = qt_utils.get_main_window_screen_number()
        expected = 10
        self.assertEqual(expected, result)

    @patch("gt.ui.qt_import.QtWidgets.QDesktopWidget")
    def test_get_window_screen_number(self, mock_desktop):
        mock_screen_number = MagicMock()
        mock_screen_number.screenNumber.return_value = 10
        mock_desktop.return_value = mock_screen_number
        result = qt_utils.get_window_screen_number(MagicMock())
        expected = 10
        self.assertEqual(expected, result)

    def test_center_window(self):
        mock_window = MagicMock()
        qt_utils.center_window(mock_window)
        mock_window.move.assert_called()

    def test_update_formatted_label_default_format(self):
        mock_label = ui_qt.QtWidgets.QLabel()
        expected_html = "<html><div style='text-align:center;'><font>Text</font></div></html>"
        qt_utils.update_formatted_label(mock_label, "Text")
        result_html = mock_label.text()
        self.assertEqual(expected_html, result_html)

    def test_update_formatted_label_custom_format(self):
        mock_label = ui_qt.QtWidgets.QLabel()
        expected_html = (
            "<html><div style='text-align:left;'><b><font size='16' color='blue' style='background-color:"
            "yellow;'>Text</font></b><b><font size='14' color='red'>Output</font></b></div></html>"
        )
        qt_utils.update_formatted_label(
            mock_label,
            "Text",
            text_size=16,
            text_color="blue",
            text_bg_color="yellow",
            text_is_bold=True,
            output_text="Output",
            output_size=14,
            output_color="red",
            text_output_is_bold=True,
            overall_alignment="left",
        )
        result_html = mock_label.text()
        self.assertEqual(expected_html, result_html)

    def test_load_and_scale_pixmap_scale_by_percentage(self):
        # Test scaling by percentage
        import gt.ui.resource_library as ui_res_lib

        input_path = ui_res_lib.Icon.dev_code

        scale_percentage = 50
        scaled_pixmap = qt_utils.load_and_scale_pixmap(image_path=input_path, scale_percentage=scale_percentage)

        expected_width = 256  # 50% of the original width
        expected_height = 256  # 50% of the original height

        self.assertEqual(scaled_pixmap.width(), expected_width)
        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_load_and_scale_pixmap_scale_by_exact_height(self):
        # Test scaling by exact height
        import gt.ui.resource_library as ui_res_lib

        input_path = ui_res_lib.Icon.dev_code
        exact_height = 200
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_height=exact_height
        )

        expected_height = 200  # Exact height specified

        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_load_and_scale_pixmap_scale_by_exact_width(self):
        # Test scaling by exact width
        import gt.ui.resource_library as ui_res_lib

        input_path = ui_res_lib.Icon.dev_code
        exact_width = 300
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_width=exact_width
        )

        expected_width = 300  # Exact width specified

        self.assertEqual(scaled_pixmap.width(), expected_width)

    def test_load_and_scale_pixmap_scale_with_both_exact_dimensions(self):
        # Test scaling with both exact dimensions specified
        import gt.ui.resource_library as ui_res_lib

        input_path = ui_res_lib.Icon.dev_code
        exact_width = 300
        exact_height = 200
        scaled_pixmap = qt_utils.load_and_scale_pixmap(
            image_path=input_path, scale_percentage=100, exact_height=exact_height, exact_width=exact_width
        )

        expected_width = 300  # Exact width specified
        expected_height = 200  # Exact height specified

        self.assertEqual(scaled_pixmap.width(), expected_width)
        self.assertEqual(scaled_pixmap.height(), expected_height)

    def test_create_color_pixmap_valid_color(self):
        expected_width_height = 24
        result = qt_utils.create_color_pixmap(
            color=ui_qt.QtGui.QColor(255, 0, 0), width=expected_width_height, height=expected_width_height
        )
        self.assertEqual(ui_qt.QtGui.QPixmap, type(result))
        self.assertEqual(expected_width_height, result.height())
        self.assertEqual(expected_width_height, result.width())

    def test_create_color_pixmap_invalid_color(self):
        # Test with an invalid color (not a QColor)
        result = qt_utils.create_color_pixmap("invalid_color")
        self.assertIsNone(result)

    def test_create_color_icon_valid_color(self):
        result = qt_utils.create_color_icon(color=ui_qt.QtGui.QColor(255, 0, 0))
        self.assertEqual(ui_qt.QtGui.QIcon, type(result))

    def test_create_color_icon_invalid_color(self):
        # Test with an invalid color (not a QColor)
        result = qt_utils.create_color_icon("invalid_color")
        self.assertIsNone(result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication")
    def test_get_screen_dpi_scale_valid_screen_number(self, mock_qapp):
        # Create a mock QApplication instance with mock screens
        app = MagicMock()
        screen1 = MagicMock()
        screen2 = MagicMock()
        screen1.logicalDotsPerInch.return_value = 120.0
        screen2.logicalDotsPerInch.return_value = 96.0
        app.screens.return_value = [screen1, screen2]

        # Replace the QApplication instance with the mock
        mock_qapp.instance.return_value = app

        expected_result = 1
        result = qt_utils.get_screen_dpi_scale(screen_number=1)
        self.assertEqual(expected_result, result)
        expected_result = 1.25
        result = qt_utils.get_screen_dpi_scale(screen_number=0)
        self.assertEqual(expected_result, result)

    @patch("gt.ui.qt_import.QtWidgets.QApplication")
    def test_get_screen_dpi_scale_negative_screen_number(self, mock_app):
        # Create a mock QApplication instance with mock screens
        app = MagicMock()
        screen1 = MagicMock()
        screen2 = MagicMock()
        screen1.logicalDotsPerInch.return_value = 120.0
        screen2.logicalDotsPerInch.return_value = 96.0
        app.screens.return_value = [screen1, screen2]

        # Replace the QApplication instance with the mock
        mock_app.instance.return_value = app

        # Test with a negative screen number (screen_number = -1)
        with self.assertRaises(ValueError):
            qt_utils.get_screen_dpi_scale(-1)
