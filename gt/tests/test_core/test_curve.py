from unittest.mock import patch
from io import StringIO
import unittest
import logging
import json
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tests import maya_test_tools
from gt.core import curve as core_curve
from gt.core import transform as core_transform

cmds = maya_test_tools.cmds


def import_curve_test_file():
    """
    Import test curve file from inside the .../data folder/<name>.abc
    """
    maya_test_tools.import_data_file("curves_nurbs_bezier.ma")


class TestCurveCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def assertAlmostEqualSigFig(self, arg1, arg2, tolerance=2):
        """
        Asserts that two numbers are almost equal up to a given number of significant figures.

        Args:
            self (object): The current test case or class object.
            arg1 (float): The first number for comparison.
            arg2 (float): The second number for comparison.
            tolerance (int, optional): The number of significant figures to consider for comparison. Default is 2.

        Returns:
            None

        Raises:
            AssertionError: If the significands of arg1 and arg2 differ by more than the specified tolerance.

        Example:
            obj = TestClass()
            obj.assertAlmostEqualSigFig(3.145, 3.14159, tolerance=3)
            # No assertion error will be raised as the first 3 significant figures are equal (3.14)
        """
        if tolerance > 1:
            tolerance = tolerance - 1

        str_formatter = "{0:." + str(tolerance) + "e}"
        significand_1 = float(str_formatter.format(arg1).split("e")[0])
        significand_2 = float(str_formatter.format(arg2).split("e")[0])

        exponent_1 = int(str_formatter.format(arg1).split("e")[1])
        exponent_2 = int(str_formatter.format(arg2).split("e")[1])

        self.assertEqual(significand_1, significand_2)
        self.assertEqual(exponent_1, exponent_2)

    def test_combine_curves_list_two(self):
        import_curve_test_file()
        combined_crv = core_curve.combine_curves_list(["curve_01", "curve_02"])
        result = cmds.listRelatives(combined_crv, shapes=True)
        expected = ["curve_Shape1", "curve_Shape2"]
        self.assertEqual(expected, result)

    def test_combine_curves_list_multiple(self):
        import_curve_test_file()
        combined_crv = core_curve.combine_curves_list(["curve_01", "curve_02", "bezier_01", "bezier_02"])
        result = cmds.listRelatives(combined_crv, shapes=True)
        expected = ["curve_Shape1", "curve_Shape2", "bezier_Shape1", "bezier_Shape2"]
        self.assertEqual(expected, result)

    def test_combine_curves_list_bezier_to_nurbs(self):
        import_curve_test_file()
        combined_crv = core_curve.combine_curves_list(["bezier_01", "bezier_02"], convert_bezier_to_nurbs=True)
        shapes = cmds.listRelatives(combined_crv, shapes=True)
        result = maya_test_tools.list_obj_types(shapes)
        expected = {"bezier_Shape1": "nurbsCurve", "bezier_Shape2": "nurbsCurve"}
        self.assertEqual(expected, result)

    def test_combine_curves_list_no_bezier_to_nurbs(self):
        import_curve_test_file()
        combined_crv = core_curve.combine_curves_list(["bezier_01", "bezier_02"], convert_bezier_to_nurbs=False)
        shapes = cmds.listRelatives(combined_crv, shapes=True)
        result = maya_test_tools.list_obj_types(shapes)
        expected = {"bezier_Shape1": "bezierCurve", "bezier_Shape2": "bezierCurve"}
        self.assertEqual(expected, result)

    def test_separate_curve_shapes_into_transforms(self):
        import_curve_test_file()
        result = core_curve.separate_curve_shapes_into_transforms("combined_curve_01")
        expected = ["combined_curve_1", "combined_curve_2"]
        self.assertEqual(expected, result)

    def test_combine_separate_curve_shapes_into_transforms(self):
        import_curve_test_file()
        combined_crv = core_curve.combine_curves_list(["curve_01", "bezier_02"], convert_bezier_to_nurbs=False)
        result = core_curve.separate_curve_shapes_into_transforms(combined_crv)
        expected = ["curve_1", "bezier_2"]
        self.assertEqual(expected, result)

    @patch("sys.stdout", new_callable=StringIO)
    def test_selected_curves_combine(self, mocked_stout):
        import_curve_test_file()
        cmds.select(["curve_01", "curve_02"])
        result = core_curve.selected_curves_combine(show_bezier_conversion_dialog=False)
        expected = "curve_01"
        self.assertEqual(expected, result)
        children = cmds.listRelatives(result, children=True)
        expected = ["curve_Shape1", "curve_Shape2"]
        self.assertEqual(expected, children)

    @patch("sys.stdout", new_callable=StringIO)
    def test_selected_curves_separate(self, mocked_stout):
        import_curve_test_file()
        cmds.select("combined_curve_01")
        result = core_curve.selected_curves_separate()
        expected = ["combined_curve_1", "combined_curve_2"]
        self.assertEqual(expected, result)

    def test_curve_shape_read_existing(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(read_existing_shape="curve_Shape1")

        result = curve_shape.get_data_as_dict()
        expected = {
            "degree": 3,
            "is_bezier": False,
            "knot": None,
            "name": "curve_Shape1",
            "periodic": 0,
            "points": [[0.0, 0.0, 5.0], [-5.0, 0.0, 5.0], [-5.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        }
        self.assertEqual(expected, result)

    def test_curve_shape_set_name(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(read_existing_shape="bezier_Shape1")
        curve_shape.set_name(new_name="new_name")
        result = curve_shape.get_data_as_dict().get("name")
        expected = "new_name"
        self.assertEqual(expected, result)

    def test_curve_shape_init(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        result = curve_shape.get_data_as_dict()
        expected = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": None,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        self.assertEqual(expected, result)

    def test_curve_shape_to_string(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        result = str(curve_shape)
        expected = (
            'CurveShape:\n\t"name": my_curve\n\t"points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]'
            '\n\t"degree": 1\n\t"knot": None\n\t"periodic": None\n\t"is_bezier": False'
        )
        self.assertEqual(expected, result)

    def test_curve_shape_valid(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        result = curve_shape.is_curve_shape_valid()
        self.assertTrue(result)

    def test_curve_shape_invalid(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(name="my_curve", points=None, degree=1, is_bezier=False)
        logging.disable(logging.WARNING)
        result = curve_shape.is_curve_shape_valid()
        logging.disable(logging.NOTSET)
        self.assertFalse(result)

    def test_curve_shape_create(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        result = curve_shape.build()
        expected = "my_curve_transform"
        self.assertEqual(expected, result)

    def test_curve_shape_get_parameters(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        result = curve_shape.get_parameters()
        expected = {"degree": 1, "name": "my_curve_transform", "point": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        self.assertEqual(expected, result)

    def test_curve_shape_create_recursive(self):
        import_curve_test_file()
        curve_shape = core_curve.CurveShape(
            name="my_curve", points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]], degree=1, is_bezier=False
        )
        created_crv = curve_shape.build()
        shapes = cmds.listRelatives(created_crv, shapes=True)
        new_curve_shape = core_curve.CurveShape(read_existing_shape=shapes[0])
        result = new_curve_shape.get_data_as_dict()
        expected = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        self.assertEqual(expected, result)

    def test_curve_shape_set_data_from_dict_init(self):
        import_curve_test_file()
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        result = curve_shape.points
        expected = curve_shape_data.get("points")
        self.assertEqual(expected, result)

    def test_curve_shape_set_data_from_dict(self):
        import_curve_test_file()
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape()
        curve_shape.set_data_from_dict(data_dict=curve_shape_data)
        result = curve_shape.points
        expected = curve_shape_data.get("points")
        self.assertEqual(expected, result)

    def test_curve_shape_replace(self):
        import_curve_test_file()
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve_shape.replace_target_curve(target_curve="curve_01")
        new_curve_shape = core_curve.CurveShape(read_existing_shape="my_curve")
        result = new_curve_shape.get_data_as_dict()
        expected = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        self.assertEqual(expected, result)

    def test_curve_init(self):
        import_curve_test_file()
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        result = curve.get_data_as_dict()
        expected = {
            "name": "my_curve",
            "shapes": [
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "my_curve",
                    "periodic": None,
                    "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                }
            ],
            "transform": None,
        }
        self.assertEqual(expected, result)

    def test_curve_read_from_existing(self):
        import_curve_test_file()
        curve = core_curve.Curve(read_existing_curve="curve_01")
        result = curve.get_data_as_dict()
        expected = {
            "name": "curve_01",
            "shapes": [
                {
                    "degree": 3,
                    "is_bezier": False,
                    "knot": None,
                    "name": "curve_Shape1",
                    "periodic": 0,
                    "points": [[0.0, 0.0, 5.0], [-5.0, 0.0, 5.0], [-5.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
                }
            ],
            "transform": None,
        }
        self.assertEqual(expected, result)

    def test_curve_read_from_dict(self):
        data_path = maya_test_tools.get_data_dir_path()
        two_lines_crv = os.path.join(data_path, "two_lines.crv")
        with open(two_lines_crv, "r") as file:
            data_dict = json.load(file)
        curve = core_curve.Curve(data_from_dict=data_dict)
        result = curve.get_data_as_dict()
        expected = {
            "name": "two_lines",
            "shapes": [
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "curveShape1",
                    "periodic": None,
                    "points": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                },
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "curveShape2",
                    "periodic": None,
                    "points": [[0.0, 0.0, -1.0], [1.0, 0.0, -1.0]],
                },
            ],
            "transform": None,
        }
        self.assertEqual(expected, result)

    def test_curve_read_from_file(self):
        data_path = maya_test_tools.get_data_dir_path()
        two_lines_crv = os.path.join(data_path, "two_lines.crv")
        curve = core_curve.Curve(data_from_file=two_lines_crv)
        result = curve.get_data_as_dict()
        expected = {
            "name": "two_lines",
            "shapes": [
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "curveShape1",
                    "periodic": None,
                    "points": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                },
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "curveShape2",
                    "periodic": None,
                    "points": [[0.0, 0.0, -1.0], [1.0, 0.0, -1.0]],
                },
            ],
            "transform": None,
        }
        self.assertEqual(expected, result)

    def test_curve_is_valid_valid(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        result = curve.is_curve_valid()
        self.assertTrue(result)

    def test_curve_is_valid_invalid(self):
        curve = core_curve.Curve(name="my_curve")
        logging.disable(logging.WARNING)
        result = curve.is_curve_valid()
        logging.disable(logging.NOTSET)
        self.assertFalse(result)

    def test_curve_build(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        result = curve.build()
        expected = "|my_curve"
        self.assertEqual(expected, result)

    def test_curve_transform(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        from gt.core.transform import Vector3, Transform

        pos = Vector3(1, 2, 3)
        rot = Vector3(4, 5, 6)
        sca = Vector3(7, 8, 9)
        trans = Transform(pos, rot, sca)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape], transform=trans)
        curve_name = curve.build()
        result = cmds.getAttr(f"{curve_name}.tx")
        expected = 1
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.ty")
        expected = 2
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.tz")
        expected = 3
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.rx")
        expected = 4
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.ry")
        expected = 5
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.rz")
        expected = 6
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.sx")
        expected = 7
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.sy")
        expected = 8
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f"{curve_name}.sz")
        expected = 9
        self.assertAlmostEqualSigFig(expected, result)

    def test_curve_set_name(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        curve.set_name("mocked_curve")
        result = curve.build()
        expected = "mocked_curve"
        self.assertEqual(expected, result)

    def test_curve_write_curve_to_file(self):
        data_dir = maya_test_tools.generate_test_temp_dir()
        temp_file = os.path.join(data_dir, "output.json")
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        curve.write_curve_to_file(temp_file)
        with open(temp_file, "r") as file:
            result = json.load(file)
        expected = {
            "name": "my_curve",
            "shapes": [
                {
                    "degree": 1,
                    "is_bezier": False,
                    "knot": None,
                    "name": "my_curve",
                    "periodic": None,
                    "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                }
            ],
            "transform": None,
        }
        self.assertEqual(expected, result)

    def test_curve_set_metadata(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        metadata_dict = {"mocked_key": "mocked_value"}
        curve.set_metadata_dict(new_metadata=metadata_dict)
        result = curve.metadata
        expected = metadata_dict
        self.assertEqual(expected, result)

    def test_curve_get_metadata(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        metadata_dict = {"mocked_key": "mocked_value"}
        curve.set_metadata_dict(new_metadata=metadata_dict)
        result = curve.get_metadata()
        expected = metadata_dict
        self.assertEqual(expected, result)

    def test_curve_add_metadata(self):
        curve_shape_data = {
            "degree": 1,
            "is_bezier": False,
            "knot": None,
            "name": "my_curve",
            "periodic": 0,
            "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
        }
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        curve.add_to_metadata(key="mocked_key_one", value="mocked_value_one")
        result = curve.get_metadata()
        expected = {"mocked_key_one": "mocked_value_one"}
        self.assertEqual(expected, result)
        curve.add_to_metadata(key="mocked_key_two", value="mocked_value_two")
        result = curve.get_metadata()
        expected = {"mocked_key_one": "mocked_value_one", "mocked_key_two": "mocked_value_two"}
        curve.add_to_metadata(key="mocked_key_two", value="mocked_value_two")
        self.assertEqual(expected, result)

    def test_get_curve_path(self):
        path = core_curve.get_curve_file_path("circle")
        result = os.path.exists(path)
        self.assertTrue(result)
        result = os.path.basename(path)
        expected = "circle.crv"
        self.assertEqual(expected, result)

    def test_get_curve_preview_image_path(self):
        path = core_curve.get_curve_preview_image_path("circle")
        result = os.path.exists(path)
        self.assertTrue(result)
        result = os.path.basename(path)
        expected = "circle.jpg"
        self.assertEqual(expected, result)

    def test_curves_existence(self):
        curve_attributes = vars(core_curve.Curves)
        curve_keys = [attr for attr in curve_attributes if not (attr.startswith("__") and attr.endswith("__"))]
        for curve_key in curve_keys:
            curve_obj = getattr(core_curve.Curves, curve_key)
            if not curve_obj:
                raise Exception(f"Missing curve: {curve_obj}")
            if not curve_obj.shapes:
                raise Exception(f"Missing shapes for a curve: {curve_obj}")

    @patch("sys.stdout", new_callable=StringIO)
    def test_add_thumbnail_metadata_attr_to_selection(self, mock_stdout):
        import_curve_test_file()
        curves_to_test = ["curve_01", "curve_02"]
        cmds.select(curves_to_test)
        core_curve.add_thumbnail_metadata_attr_to_selection()
        for crv in curves_to_test:
            axis = cmds.objExists(f"{crv}.{core_curve.PROJECTION_AXIS_KEY}")
            scale = cmds.objExists(f"{crv}.{core_curve.PROJECTION_SCALE_KEY}")
            fit = cmds.objExists(f"{crv}.{core_curve.PROJECTION_FIT_KEY}")
            self.assertTrue(axis)
            self.assertTrue(scale)
            self.assertTrue(fit)

    @patch("sys.stdout", new_callable=StringIO)
    def test_write_curve_files_from_selection(self, mock_stdout):
        import_curve_test_file()
        temp_folder = maya_test_tools.generate_test_temp_dir()
        curves_to_test = ["curve_01", "curve_02"]
        cmds.select(curves_to_test)
        core_curve.add_thumbnail_metadata_attr_to_selection()
        cmds.setAttr(f"curve_01.{core_curve.PROJECTION_AXIS_KEY}", 0)
        core_curve.write_curve_files_from_selection(target_dir=temp_folder)
        expected = ["curve_01.crv", "curve_02.crv"]
        result = sorted(os.listdir(temp_folder))  # Sorted because MacOS might change the order
        self.assertEqual(expected, result)
        curve_file = os.path.join(temp_folder, "curve_01.crv")
        with open(curve_file, "r") as file:
            data_dict = json.load(file)
        result = data_dict.get("metadata").get(core_curve.PROJECTION_AXIS_KEY)
        expected = "persp"
        self.assertEqual(expected, result)

    @patch("maya.cmds.viewFit")
    @patch("maya.cmds.lookThru")
    @patch("sys.stdout", new_callable=StringIO)
    def test_generate_curve_thumbnail(self, mock_stdout, mock_look_thru, mock_view_fit):
        temp_folder = maya_test_tools.generate_test_temp_dir()
        curve_data_path = os.path.join(maya_test_tools.get_data_dir_path(), "two_lines.crv")
        curve = core_curve.Curve(data_from_file=curve_data_path)
        core_curve.generate_package_curve_thumbnail(target_dir=temp_folder, curve=curve)
        expected = ["two_lines.jpg"]
        result = os.listdir(temp_folder)
        self.assertEqual(expected, result)

    @patch("gt.utils.system.open_file_dir")
    @patch("maya.cmds.viewFit")
    @patch("maya.cmds.lookThru")
    @patch("sys.stdout", new_callable=StringIO)
    def test_generate_curves_thumbnails(self, mock_stdout, mock_look_thru, mock_view_fit, mock_open_file_dir):
        curve_data_path = os.path.join(maya_test_tools.get_data_dir_path(), "two_lines.crv")
        curve = core_curve.Curve(data_from_file=curve_data_path)

        class MockedCurves:  # Mocked curves class
            two_lines = curve

        with patch("gt.core.curve.Curves", new=MockedCurves):
            temp_folder = maya_test_tools.generate_test_temp_dir()
            core_curve.generate_package_curves_thumbnails(target_dir=temp_folder)
            expected = ["two_lines.jpg"]
            result = os.listdir(temp_folder)
            self.assertEqual(expected, result)

    def test_curve_get_name(self):
        curve_shape_data = {"name": "my_curve", "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        result = curve.get_name()
        expected = "my_curve"
        self.assertEqual(expected, result)

    def test_curve_get_name_formatted(self):
        curve_shape_data = {"name": "my_curve", "points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        curve_shape = core_curve.CurveShape(read_curve_shape_data=curve_shape_data)
        curve = core_curve.Curve(name="my_curve", shapes=[curve_shape])
        result = curve.get_name(formatted=True)
        expected = "My Curve"
        self.assertEqual(expected, result)

    def test_get_curve(self):
        curve = core_curve.get_curve(file_name="_scalable_one_side_arrow")
        self.assertIsInstance(curve, core_curve.Curve)

    def test_get_curve_custom_dir(self):
        curve = core_curve.get_curve(file_name="two_lines", curve_dir=maya_test_tools.get_data_dir_path())
        self.assertIsInstance(curve, core_curve.Curve)

    def test_get_curve_missing_file(self):
        curve = core_curve.get_curve(file_name="mocked_missing_file", curve_dir=maya_test_tools.get_data_dir_path())
        self.assertFalse(curve)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_code_for_crv_files(self, mocked_stdout):
        data_dir = maya_test_tools.get_data_dir_path()
        result = core_curve.print_code_for_crv_files(target_dir=data_dir, use_output_window=False)
        expected = 'two_lines = get_curve(file_name="two_lines")'
        self.assertEqual(expected, result)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_code_for_crv_files_ignore_private_files(self, mocked_stdout):
        temp_dir = maya_test_tools.generate_test_temp_dir()
        private_curve = os.path.join(temp_dir, "_private.crv")
        public_curve = os.path.join(temp_dir, "public.crv")
        for file_path in [private_curve, public_curve]:
            with open(file_path, "w"):
                pass
        result = core_curve.print_code_for_crv_files(target_dir=temp_dir, ignore_private=True, use_output_window=False)
        expected = 'public = get_curve(file_name="public")'
        self.assertEqual(expected, result)

    @patch("sys.stdout", new_callable=StringIO)
    def test_print_code_for_crv_files_include_private_files(self, mocked_stdout):
        temp_dir = maya_test_tools.generate_test_temp_dir()
        private_curve = os.path.join(temp_dir, "_private.crv")
        public_curve = os.path.join(temp_dir, "public.crv")
        for file_path in [private_curve, public_curve]:
            with open(file_path, "w"):
                pass
        result = core_curve.print_code_for_crv_files(target_dir=temp_dir, ignore_private=False, use_output_window=False)
        expected = 'public = get_curve(file_name="public")\n_private = get_curve(file_name="_private")'
        self.assertEqual(expected, result)

    def test_create_text(self):
        result = core_curve.create_text("curve", font="Arial")
        expected = "curve_crv"
        self.assertEqual(expected, result)

    def test_create_text_shapes(self):
        curve = core_curve.create_text("curve", font="Arial")
        result = cmds.listRelatives(curve, shapes=True)
        expected = [
            "curve_crv_01Shape",
            "curve_crv_02Shape",
            "curve_crv_03Shape",
            "curve_crv_04Shape",
            "curve_crv_05Shape",
            "curve_crv_06Shape",
        ]
        self.assertEqual(expected, result)

    def test_create_text_shape_types(self):
        curve = core_curve.create_text("curve")
        shapes = cmds.listRelatives(curve, shapes=True)
        type_dict = maya_test_tools.list_obj_types(shapes)
        expected = "nurbsCurve"
        for obj, obj_type in type_dict.items():
            self.assertEqual(expected, obj_type)

    def test_add_shape_scale_cluster(self):
        cube = cmds.circle(ch=False)[0]
        control_attr = "mockedAttr"
        cmds.addAttr(cube, longName=control_attr, at="double", k=True, minValue=0)
        result = core_curve.add_shape_scale_cluster(cube, f"{cube}.{control_attr}")
        expected = "nurbsCircle1_LocScaleHandle"
        self.assertEqual(expected, result)

    def test_curve_set_transform(self):
        curve = core_curve.get_curve("circle")
        expected = None
        result = curve.transform
        self.assertEqual(expected, result)
        transform = core_transform.Transform()
        transform.set_position(0, 10, 0)
        curve.set_transform(transform)
        self.assertEqual(transform, curve.transform)
        maya_curve = curve.build()
        ty_value = cmds.getAttr(f"{maya_curve}.ty")
        expected = 10
        self.assertEqual(expected, ty_value)

    def test_curve_get_transform(self):
        curve = core_curve.get_curve("circle")
        expected = None
        result = curve.transform
        self.assertEqual(expected, result)
        transform = core_transform.Transform()
        transform.set_position(0, 10, 0)
        curve.transform = transform
        result = curve.get_transform()
        self.assertEqual(transform, result)

    def test_curve_set_position(self):
        curve = core_curve.get_curve("circle")
        expected = None
        result = curve.transform
        self.assertEqual(expected, result)
        transform = core_transform.Transform()
        transform.set_position(0, 10, 0)
        curve.set_position(0, 10, 0)
        self.assertEqual(transform, curve.transform)
        maya_curve = curve.build()
        ty_value = cmds.getAttr(f"{maya_curve}.ty")
        expected = 10
        self.assertEqual(expected, ty_value)

    def test_curve_set_rotation(self):
        curve = core_curve.get_curve("circle")
        expected = None
        result = curve.transform
        self.assertEqual(expected, result)
        transform = core_transform.Transform()
        transform.set_rotation(0, 10, 0)
        curve.set_rotation(0, 10, 0)
        self.assertEqual(transform, curve.transform)
        maya_curve = curve.build()
        ty_value = cmds.getAttr(f"{maya_curve}.ry")
        expected = 10
        self.assertEqual(expected, ty_value)

    def test_curve_set_scale(self):
        curve = core_curve.get_curve("circle")
        expected = None
        result = curve.transform
        self.assertEqual(expected, result)
        transform = core_transform.Transform()
        transform.set_scale(0, 10, 0)
        curve.set_scale(0, 10, 0)
        self.assertEqual(transform, curve.transform)
        maya_curve = curve.build()
        ty_value = cmds.getAttr(f"{maya_curve}.sy")
        expected = 10
        self.assertEqual(expected, ty_value)

    def test_filter_curve_shapes(self):
        cube = maya_test_tools.create_poly_cube()
        circle_one = cmds.circle()[0]
        circle_two = cmds.circle()[0]
        items = [circle_one, circle_two, cube]
        expected = ["|nurbsCircle1|nurbsCircleShape1", "|nurbsCircle2|nurbsCircleShape2"]
        result = core_curve.filter_curve_shapes(obj_list=items, get_transforms=False)  # False is default
        self.assertEqual(expected, result)

    def test_filter_curve_shapes_transforms(self):
        cube = maya_test_tools.create_poly_cube()
        circle_one = cmds.circle()[0]
        circle_two = cmds.circle()[0]
        items = [circle_one, circle_two, cube]
        expected = ["nurbsCircle2", "nurbsCircle1"]
        result = core_curve.filter_curve_shapes(obj_list=items, get_transforms=True)
        self.assertEqual(sorted(expected), sorted(result))  # macOS changes the order, that's why it's sorted.

    def test_get_python_shape_code(self):
        cube = maya_test_tools.create_poly_cube()
        circle_one = cmds.circle()[0]
        circle_two = cmds.circle()[0]
        items = [circle_one, circle_two, cube]
        expected = (
            "# Shape state for \"nurbsCircleShape1\":\nfor cv in [('nurbsCircle1.cv[0]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle1.cv[1]', (0.0, 0.0, 0.0)), ('nurbsCircle1.cv[2]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle1.cv[3]', (0.0, 0.0, 0.0)), ('nurbsCircle1.cv[4]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle1.cv[5]', (0.0, 0.0, 0.0)), ('nurbsCircle1.cv[6]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle1.cv[7]', (0.0, 0.0, 0.0))]:\n    cmds.xform(cv[0], os=True, t=cv[1])"
            "\n\n# Shape state for \"nurbsCircleShape2\":\nfor cv in [('nurbsCircle2.cv[0]', (0.0, 0.0, 0.0)),"
            " ('nurbsCircle2.cv[1]', (0.0, 0.0, 0.0)), ('nurbsCircle2.cv[2]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle2.cv[3]', (0.0, 0.0, 0.0)), ('nurbsCircle2.cv[4]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle2.cv[5]', (0.0, 0.0, 0.0)), ('nurbsCircle2.cv[6]', (0.0, 0.0, 0.0)), "
            "('nurbsCircle2.cv[7]', (0.0, 0.0, 0.0))]:"
            "\n    cmds.xform(cv[0], os=True, t=cv[1])"
        )
        result = core_curve.get_python_shape_code(crv_list=items)
        self.assertEqual(expected, result)

    def test_get_python_curve_code(self):
        cube = maya_test_tools.create_poly_cube()
        circle_one = cmds.circle()[0]
        circle_two = cmds.circle()[0]
        items = [circle_one, circle_two, cube]
        expected = (
            '# Curve data for "nurbsCircleShape1":\ncmds.curve(point=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], '
            "[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "
            "[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], degree=3, periodic=2, "
            "knot=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0], "
            "name='nurbsCircleShape1_transform')\n\n# Curve data for \"nurbsCircleShape2\":\ncmds.curve("
            "point=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "
            "[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], "
            "[0.0, 0.0, 0.0]], degree=3, periodic=2, knot=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, "
            "7.0, 8.0, 9.0, 10.0], name='nurbsCircleShape2_transform')"
        )
        result = core_curve.get_python_curve_code(crv_list=items)
        self.assertEqual(expected, result)

    def test_set_curve_width(self):
        circle_one = cmds.circle()[0]
        result = core_curve.set_curve_width(obj_list=circle_one, line_width=5)
        expected_shapes = ["|nurbsCircle1|nurbsCircleShape1"]
        self.assertEqual(expected_shapes, result)
        value = cmds.getAttr(f"{expected_shapes[0]}.lineWidth")
        expected_width = 5
        self.assertEqual(expected_width, value)

    def test_set_curve_width_list(self):
        circle_one = cmds.circle()[0]
        circle_two = cmds.circle()[0]
        crv_transforms = [circle_one, circle_two]
        result = core_curve.set_curve_width(obj_list=crv_transforms, line_width=5)
        expected_shapes = ["|nurbsCircle1|nurbsCircleShape1", "|nurbsCircle2|nurbsCircleShape2"]
        self.assertEqual(expected_shapes, result)
        for shape in expected_shapes:
            value = cmds.getAttr(f"{shape}.lineWidth")
            expected_width = 5
            self.assertEqual(expected_width, value)

    def test_create_connection_line(self):
        cube_one = maya_test_tools.create_poly_cube(name="myCubeA")
        cube_two = maya_test_tools.create_poly_cube(name="myCubeB")
        result = core_curve.create_connection_line(object_a=cube_one, object_b=cube_two)
        expected = ("myCubeA_to_myCubeB", "myCubeA_cluster", "myCubeB_cluster")
        self.assertEqual(expected, result)

    def test_get_positions_from_curve_periodic(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )
        result = core_curve.get_positions_from_curve(curve=crv, count=2, periodic=True, space="uv", normalized=True)
        expected = [0.0, 0.5]
        self.assertEqual(expected, result)

    def test_get_positions_from_curve_open(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )
        result = core_curve.get_positions_from_curve(curve=crv, count=2, periodic=False, space="uv", normalized=True)
        expected = [0.0, 1.0]
        self.assertEqual(expected, result)

    def test_get_positions_from_curve_not_normalized(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )
        result = core_curve.get_positions_from_curve(curve=crv, count=2, periodic=False, space="uv", normalized=False)
        expected = [0.0, 3.0]
        self.assertEqual(expected, result)

    def test_get_positions_from_curve_world_space(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )
        result = core_curve.get_positions_from_curve(curve=crv, count=2, periodic=False, space="world", normalized=True)
        expected = [[0.0, 0.0, 1.0], [0.0, 0.0, -2.0]]
        self.assertEqual(expected, result)

    def test_rescale_curve(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )

        num_cvs = cmds.getAttr(f"{crv}.spans")
        num_cvs += cmds.getAttr(f"{crv}.degree")
        cv_positions = []
        for i in range(num_cvs):
            cv_position = cmds.pointPosition(f"{crv}.cv[{i}]", world=True)
            cv_positions.append(cv_position)

        expected = [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.667],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 0.0, -1.667],
            [0.0, 0.0, -2.0],
        ]
        self.assertEqual(expected, cv_positions)

        core_curve.rescale_curve(curve_transform=crv, scale=2)

        cv_positions = []
        for i in range(num_cvs):
            cv_position = cmds.pointPosition(f"{crv}.cv[{i}]", world=True)
            cv_positions.append(cv_position)

        expected = [
            [0.0, 0.0, 2.0],
            [0.0, 0.0, 1.334],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, -2.0],
            [0.0, 0.0, -3.334],
            [0.0, 0.0, -4.0],
        ]
        self.assertEqual(expected, cv_positions)

    def test_rescale_curve_tuple(self):
        crv = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_curve",
        )

        num_cvs = cmds.getAttr(f"{crv}.spans")
        num_cvs += cmds.getAttr(f"{crv}.degree")
        cv_positions = []
        for i in range(num_cvs):
            cv_position = cmds.pointPosition(f"{crv}.cv[{i}]", world=True)
            cv_positions.append(cv_position)

        expected = [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.667],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 0.0, -1.667],
            [0.0, 0.0, -2.0],
        ]
        self.assertEqual(expected, cv_positions)

        core_curve.rescale_curve(curve_transform=crv, scale=(2, 1, 1))

        cv_positions = []
        for i in range(num_cvs):
            cv_position = cmds.pointPosition(f"{crv}.cv[{i}]", world=True)
            cv_positions.append(cv_position)

        expected = [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 0.667],
            [0.0, 0.0, 0.0],
            [0.0, 0.0, -1.0],
            [0.0, 0.0, -1.667],
            [0.0, 0.0, -2.0],
        ]
        self.assertEqual(expected, cv_positions)
