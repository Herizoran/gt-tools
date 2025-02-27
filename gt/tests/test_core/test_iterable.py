import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.core import iterable as core_iterable
from gt.tests import maya_test_tools
cmds = maya_test_tools.cmds


class TestIterableCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def setUp(self):
        maya_test_tools.force_new_scene()
        self.mocked_dict = {'apple': 3, 'banana': 5, 'cherry': 7, 'date': 9}
        self.mocked_list = ["1", "2", "3", "a", "b", "c"]

    def test_get_list_difference(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = (['2', '3', 'b', 'c'], [])
        result = core_iterable.get_list_difference(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_intersection(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = ['1', 'a']
        result = core_iterable.get_list_intersection(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = ['2', '3', 'b', 'c']
        result = core_iterable.get_list_missing_elements(expected_list=list_a, result_list=list_b)
        self.assertEqual(expected, result)

    def test_make_flat_list(self):
        list_a = ["1"]
        list_b = ["2", ["3"]]
        list_c = [[["4"]], ["5"]]
        list_d = []
        list_e = [[[[[["6"]]]]]]
        expected = ["1", "2", "3", "4", "5", "6"]
        result = core_iterable.make_flat_list(list_a, list_b, list_c, list_d, list_e)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements_two(self):
        list_a = ["1", "2", "a", "b"]
        list_b = ["1", "a"]
        expected = ['2', 'b']
        result = core_iterable.get_list_missing_elements(expected_list=list_a, result_list=list_b)
        self.assertEqual(expected, result)

    def test_next_item(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'banana')
        self.assertEqual(next_item, ('cherry', 7))

    def test_no_next_item(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'date')
        self.assertIsNone(next_item)

    def test_cycle_enabled(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'date', cycle=True)
        self.assertEqual(next_item, ('apple', 3))

    def test_cycle_disabled(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'date', cycle=False)
        self.assertIsNone(next_item)

    def test_next_item_last_key(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'cherry')
        self.assertEqual(next_item, ('date', 9))

    def test_cycle_enabled_last_key(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'cherry', cycle=True)
        self.assertEqual(next_item, ('date', 9))

    def test_cycle_disabled_last_key(self):
        next_item = core_iterable.get_next_dict_item(self.mocked_dict, 'date', cycle=False)
        self.assertIsNone(next_item)

    def test_remove_duplicates(self):
        self.assertEqual(core_iterable.remove_list_duplicates([1, 2, 2, 3, 4, 4, 5]), [1, 2, 3, 4, 5])
        self.assertEqual(core_iterable.remove_list_duplicates([1, 1, 1, 1, 1]), [1])
        self.assertEqual(core_iterable.remove_list_duplicates([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])
        self.assertEqual(core_iterable.remove_list_duplicates([]), [])

    def test_remove_duplicates_ordered(self):
        self.assertEqual(core_iterable.remove_list_duplicates_ordered([1, 2, 2, 3, 4, 4, 5]), [1, 2, 3, 4, 5])
        self.assertEqual(core_iterable.remove_list_duplicates_ordered([1, 1, 1, 1, 1]), [1])
        self.assertEqual(core_iterable.remove_list_duplicates_ordered([5, 4, 3, 2, 1]), [5, 4, 3, 2, 1])
        self.assertEqual(core_iterable.remove_list_duplicates_ordered([]), [])

    def test_compare_identical_dict_values_types_identical_keys(self):
        dict1 = {'a': 1, 'b': 2, 'c': 3}
        dict2 = {'c': 3, 'a': 1, 'b': 2}
        expected = True
        result = core_iterable.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_different_keys(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'c': 3, 'd': 4}
        expected = False
        result = core_iterable.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_empty_dicts(self):
        dict1 = {}
        dict2 = {}
        expected = True
        result = core_iterable.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_one_empty_dict(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {}
        expected = False
        result1 = core_iterable.compare_identical_dict_keys(dict1, dict2)
        result2 = core_iterable.compare_identical_dict_keys(dict2, dict1)
        self.assertEqual(expected, result1)
        self.assertEqual(expected, result2)

    def test_compare_identical_dict_values_types_identical_dicts(self):
        dict1 = {'a': 1, 'b': 'hello', 'c': [1, 2, 3]}
        dict2 = {'a': 2, 'b': 'world', 'c': [4, 5, 6]}
        expected = True
        result = core_iterable.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_with_none(self):
        dict1 = {'a': 1, 'b': 'hello', 'c': [1, 2, 3]}
        dict2 = {'a': 2, 'b': 'world', 'c': None}
        expected = True
        result = core_iterable.compare_identical_dict_values_types(dict1, dict2,
                                                                   allow_none=True)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_different_types(self):
        dict1 = {'a': 1, 'b': 'hello'}
        dict2 = {'a': 'string', 'b': 123}
        expected = False
        result = core_iterable.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_compare_identical_dict_values_types_missing_key(self):
        dict1 = {'a': 1, 'b': 'hello'}
        dict2 = {'a': 1, 'c': 'world'}
        expected = False
        result = core_iterable.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_round_numbers_in_list_integers(self):
        input_list = [1, 2, 3]
        expected_result = [1, 2, 3]
        result = core_iterable.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_floats(self):
        input_list = [1.2345, 2.6789, 3.0]
        expected_result = [1, 3, 3]
        result = core_iterable.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_to_2_digits(self):
        input_list = [1.2345, 2.6789, 3.0]
        expected_result = [1.23, 2.68, 3.0]
        result = core_iterable.round_numbers_in_list(input_list, num_digits=2)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_ignore_non_numeric_values(self):
        input_list = [1, 'two', 3.5, 'four']
        expected_result = [1, 'two', 4, 'four']
        result = core_iterable.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_get_highest_int_from_str_list(self):
        expected = 987
        result = core_iterable.get_highest_int_from_str_list(["proxy123", "proxy456", "proxy987"])
        self.assertEqual(expected, result)

        expected = 3
        result = core_iterable.get_highest_int_from_str_list(["no_match1", "no_match2", "no_match3"])
        self.assertEqual(expected, result)

        # Test when the list is empty
        expected = 0
        result = core_iterable.get_highest_int_from_str_list([])
        self.assertEqual(expected, result)

        # Test when the list does not contain numbers
        expected = 0
        result = core_iterable.get_highest_int_from_str_list(["hello", "world", ""])
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_default_formatting(self):
        input_dict = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
        expected = "{\n 'a': 1, 'b': {'c': 2, 'd': {'e': 3}}\n}"
        result = core_iterable.dict_as_formatted_str(input_dict)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_custom_formatting(self):
        input_dict = {'x': [1, 2, 3], 'y': {'z': 'hello'}}
        expected = "{\n  'x': [1, 2, 3],\n  'y': {'z': 'hello'}\n}"
        result = core_iterable.dict_as_formatted_str(input_dict,
                                                     indent=2,
                                                     width=30,
                                                     format_braces=True)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_sort_dicts(self):
        input_dict = {'b': 2, 'a': 1, 'c': {'z': 26, 'y': 25}}
        expected = "{\n 'a': 1,\n 'b': 2,\n 'c': {'y': 25, 'z': 26}\n}"
        result = core_iterable.dict_as_formatted_str(input_dict,
                                                     width=30)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_custom_depth(self):
        input_dict = {'a': {'b': {'c': {'d': 42}}}}
        expected = "{\n 'a': {'b': {...}}\n}"
        result = core_iterable.dict_as_formatted_str(input_dict,
                                                     depth=2)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_no_format_braces(self):
        input_dict = {'a': 1, 'b': {'c': 2}}
        expected = "{'a': 1, 'b': {'c': 2}}"
        result = core_iterable.dict_as_formatted_str(input_dict,
                                                     format_braces=False)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_no_format_braces_on_key_per_line(self):
        input_dict = {'a': 1, 'b': {'c': 2}}
        expected = "{'a': 1,\n 'b': {'c': 2}}"
        result = core_iterable.dict_as_formatted_str(input_dict,
                                                     format_braces=False,
                                                     one_key_per_line=True)
        self.assertEqual(expected, result)

    def test_sort_dict_by_keys_integer_keys(self):
        input_dict = {3: 'three', 1: 'one', 2: 'two'}
        expected_result = {1: 'one', 2: 'two', 3: 'three'}
        result = core_iterable.sort_dict_by_keys(input_dict)
        self.assertEqual(expected_result, result)

    def test_sort_dict_by_keys_empty_dict(self):
        input_dict = {}
        expected_result = {}
        result = core_iterable.sort_dict_by_keys(input_dict)
        self.assertEqual(expected_result, result)

    def test_sort_dict_by_keys_mixed_keys(self):
        # Test case with mixed keys (integer and string)
        input_dict = {'b': 'banana', 'a': 'apple', 2: 'two', 1: 'one'}
        expected_result = {1: 'one', 2: 'two', 'a': 'apple', 'b': 'banana'}
        result = core_iterable.sort_dict_by_keys(input_dict)
        self.assertEqual(expected_result, result)

    def test_sanitize_maya_list(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        non_existent_obj = 'non_existent_object'

        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere, non_existent_obj],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)

        expected = [f'|{cube}', f'|{sphere}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_filter_unique(self):
        cube_one = maya_test_tools.create_poly_cube(name='cube_one')  # Added two times below
        cube_two = maya_test_tools.create_poly_cube(name='cube_two')
        cube_three = maya_test_tools.create_poly_cube(name='cube_three')  # Added two times below
        non_existent_obj = 'non_existent_object'

        input_list = [cube_one, cube_one,
                      non_existent_obj, cube_two,
                      cube_three, cube_three]

        result = core_iterable.sanitize_maya_list(input_list=input_list,
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{cube_one}', f'|{cube_two}', f'|{cube_three}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_filter_string(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        non_existent_obj = 'non_existent_object'

        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere, non_existent_obj],
                                                  filter_unique=True,
                                                  filter_string='cube',
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{sphere}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_hierarchy(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        cmds.parent(sphere, cube)
        non_existent_obj = 'non_existent_object'

        result = core_iterable.sanitize_maya_list(input_list=[cube, non_existent_obj],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=True,
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{cube}', f'|{cube}|{sphere}',
                    f'|{cube}|{cube}Shape', f'|{cube}|{sphere}|{sphere}Shape']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_filter_type(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        result = core_iterable.sanitize_maya_list(input_list=[cube, f'|{cube}|Shape'],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type='transform',
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=True,  # Shapes won't show due to type filter
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{cube}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_filter_regex(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=r'^cu',
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{cube}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_filter_func(self):
        # Define a custom filter function
        def custom_filter(item):
            return 'sphere' in item

        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=custom_filter,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)

        expected = [f'|{sphere}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_convert_to_nodes(self):
        from gt.core.node import Node
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=True,
                                                  short_names=False)
        for obj in result:
            if not isinstance(obj, Node):
                raise Exception(f'Incorrect type returned. Expected "Node", but got "{str(type(obj))}".')

    def test_sanitize_maya_list_sort_list(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        cylinder = maya_test_tools.create_poly_cylinder(name="cylinder")
        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere, cylinder],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=True,
                                                  short_names=False)
        expected = [f'|{cube}', f'|{sphere}', f'|{cylinder}']
        result_as_str = list(map(str, result))
        self.assertEqual(expected, result_as_str)

    def test_sanitize_maya_list_sort_list_reverse(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        cylinder = maya_test_tools.create_poly_cylinder(name="cylinder")
        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere, cylinder],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=True,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=False)
        expected = [f'|{cylinder}', f'|{sphere}', f'|{cube}']
        self.assertEqual(expected, result)

    def test_sanitize_maya_list_short_names(self):
        cube = maya_test_tools.create_poly_cube(name='cube')
        sphere = maya_test_tools.create_poly_sphere(name='sphere')
        non_existent_obj = 'non_existent_object'

        result = core_iterable.sanitize_maya_list(input_list=[cube, sphere, non_existent_obj],
                                                  filter_unique=True,
                                                  filter_string=None,
                                                  filter_func=None,
                                                  filter_type=None,
                                                  filter_regex=None,
                                                  sort_list=True,
                                                  reverse_list=False,
                                                  hierarchy=False,
                                                  convert_to_nodes=False,
                                                  short_names=True)

        expected = [f'{cube}', f'{sphere}']
        self.assertEqual(expected, result)

    def test_filter_list_by_type_strings(self):
        input_list = ["world", 2, 3.5, None, "hello", 42]
        desired_data_type = str
        result = core_iterable.filter_list_by_type(input_list, desired_data_type)
        expected = ["world", "hello"]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_integers(self):
        input_list = ["world", 2, 3.5, None, "hello", 42]
        desired_data_type = int
        result = core_iterable.filter_list_by_type(input_list, desired_data_type)
        expected = [2, 42]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_floats(self):
        input_list = ["world", 2, 3.5, None, "hello", 42]
        desired_data_type = float
        result = core_iterable.filter_list_by_type(input_list, desired_data_type)
        expected = [3.5]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_none(self):
        input_list = ["world", 2, 3.5, None, "hello", 42]
        desired_data_type = type(None)
        result = core_iterable.filter_list_by_type(input_list, desired_data_type)
        expected = [None]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_none_with_num_items(self):
        input_list = ["world", 2, 3.5, None, "hello", 42]
        desired_data_type = type(None)
        result = core_iterable.filter_list_by_type(input_list, desired_data_type, num_items=4)
        expected = []
        self.assertEqual(expected, result)

    def test_filter_list_by_type_lists_with_num_items(self):
        input_list = ["world", [1, 2, 3], "hello", [4, 5]]
        desired_data_type = list
        result = core_iterable.filter_list_by_type(input_list, desired_data_type, num_items=3)
        expected = [[1, 2, 3]]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_tuples_with_num_items(self):
        input_list = ["world", (1, 2, 3), "hello", (4, 5)]
        desired_data_type = tuple
        result = core_iterable.filter_list_by_type(input_list, desired_data_type, num_items=3)
        expected = [(1, 2, 3)]
        self.assertEqual(expected, result)

    def test_filter_list_by_type_dicts_with_num_items(self):
        input_list = ["world", {"a": 1, "b": 2}, "hello", {"x": 10, "y": 20, "z": 30}]
        desired_data_type = dict
        result = core_iterable.filter_list_by_type(input_list, desired_data_type, num_items=2)
        expected = [{"a": 1, "b": 2}]
        self.assertEqual(expected, result)

    def test_multiply_collection_by_number_list_multiplication(self):
        original_list = [1, 2, 3, 4]
        multiplier = 0.5
        expected = [0.5, 1, 1.5, 2]
        result = core_iterable.multiply_collection_by_number(original_list, multiplier)
        self.assertEqual(expected, result)

    def test_multiply_collection_by_number_tuple_multiplication(self):
        original_tuple = (1, 2, 3, 4)
        multiplier = 2
        expected = (2, 4, 6, 8)
        result = core_iterable.multiply_collection_by_number(original_tuple, multiplier)
        self.assertEqual(expected, result)

    def test_multiply_collection_by_number_nested_list_multiplication(self):
        original_list = [1, [2, 3], 4]
        multiplier = 0.5
        expected = [0.5, [1, 1.5], 2]
        result = core_iterable.multiply_collection_by_number(original_list, multiplier)
        self.assertEqual(expected, result)

    def test_multiply_collection_by_number_nested_tuple_multiplication(self):
        original_tuple = (1, (2, 3), 4)
        multiplier = 2
        expected = (2, (4, 6), 8)
        result = core_iterable.multiply_collection_by_number(original_tuple, multiplier)
        self.assertEqual(expected, result)

    def test_multiply_collection_by_number_invalid_input_type(self):
        with self.assertRaises(TypeError):
            core_iterable.multiply_collection_by_number(collection=123, number=0.5)

    def test_multiply_collection_by_number_non_numeric_elements(self):
        original_list = [1, 'a', 3, 'b']
        multiplier = 2
        expected = [2, 'a', 6, 'b']
        result = core_iterable.multiply_collection_by_number(original_list, multiplier)
        self.assertEqual(expected, result)
