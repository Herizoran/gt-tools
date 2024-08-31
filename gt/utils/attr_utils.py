"""
Attribute Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.string_utils import remove_suffix, remove_prefix, upper_first_char
from gt.utils.feedback_utils import FeedbackMessage, log_when_true
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_CHANNELS = ['t', 'r', 's']
DEFAULT_DIMENSIONS = ['x', 'y', 'z']
DEFAULT_ATTRS = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v']


# -------------------------------------------- Setters ---------------------------------------------
def set_attr(attribute_path=None, value=None, obj_list=None, attr_list=None, clamp=False, force_unlock=False,
             verbose=False, log_level=logging.INFO, raise_exceptions=False):
    """
    This function sets attributes of specified objects using Maya's `cmds.setAttr` function.
    It provides options to set attributes for a single attribute path, multiple objects and attributes,
    and supports string and numeric values.
    It does not raise errors, but can log them with the provided level determined as an argument.

    Args:
        attribute_path (str, optional): A single-line object attribute path in the format "object.attribute".
        value (any): The value to set for the attribute. If a string, the attribute will be set as a string type.
        obj_list (str ,list, optional): The name of the object or a list of object names. e.g. ["cube1", "cube2"]
        attr_list (str ,list, optional): The name of the attribute or a list of attribute names. e.g. ["tx", "ty"]
        clamp (bool, optional): If True, the value will be clamped to the attribute's minimum and maximum values.
        force_unlock (bool, optional): If active, this function unlock locked attributes before settings their values.
        verbose (bool, optional): If True, log messages will be displayed for each attribute set operation.
        log_level (int, optional): The logging level to use when verbose is True. Default is logging.INFO.
        raise_exceptions (bool, optional): If active, the function will raise an exceptions whenever something fails.

    Examples:
        # Set a single attribute value
        set_attr(attribute_path="myObject.myAttribute", value=10)

        # Set multiple attributes for multiple objects
        set_attr(obj_list=["object1", "object2"], attr_list=["attr1", "attr2"], value=0.5)

        # Set a string attribute value
        set_attr(attribute_path="myObject.myStringAttribute", value="Hello, world!")
    """
    attributes_to_set = set()
    # Add One Line Attribute
    if attribute_path and isinstance(attribute_path, str):
        attributes_to_set.add(attribute_path)

    # Add object and attribute lists
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    if isinstance(attr_list, str):
        attr_list = [attr_list]
    if obj_list and attr_list and isinstance(obj_list, list) and isinstance(attr_list, list):  # Exists and is list
        for attr in attr_list:
            for obj in obj_list:
                attributes_to_set.add(f'{obj}.{attr}')

    # Set Attribute
    for attr_path in attributes_to_set:
        try:
            if force_unlock:
                if cmds.getAttr(attr_path, lock=True):
                    cmds.setAttr(attr_path, lock=False)
            if isinstance(value, str):
                cmds.setAttr(attr_path, value, typ="string", clamp=clamp)
            if isinstance(value, (tuple, list)):
                cmds.setAttr(attr_path, *value, typ="double3", clamp=clamp)
            else:
                cmds.setAttr(attr_path, value, clamp=clamp)
        except Exception as e:
            message = f'Unable to set attribute "{attr_path}". Issue: "{e}".'
            log_when_true(logger, message, do_log=verbose, level=log_level)
            if raise_exceptions:
                raise e


def set_attr_state(attribute_path=None, obj_list=None, attr_list=None, locked=None, hidden=None,
                   verbose=False, log_level=logging.INFO, raise_exceptions=False):
    """
    This function sets locked or hidden states of specified attributes of objects using Maya's `cmds.setAttr` function.
    It provides options to set locked or hidden states for a single attribute path, multiple objects and attributes.
    It does not raise errors, but can log them with the provided level determined as an argument.

    Args:
        attribute_path (str, optional): A single-line object attribute path in the format "object.attribute".
        obj_list (str ,list, optional): The name of the object or a list of object names. e.g. ["cube1", "cube2"]
        attr_list (str ,list, optional): The name of the attribute or a list of attribute names. e.g. ["tx", "ty"]
        locked (bool, optional): If True, sets the attribute's locked state to True.
        hidden (bool, optional): If True, sets the attribute's hidden state to True. (hidden and keyable are affected)
        verbose (bool, optional): If True, log messages will be displayed for each attribute state change operation.
        log_level (int, optional): The logging level to use when verbose is True. Default is logging.INFO.
        raise_exceptions (bool, optional): If active, the function will raise exceptions whenever something fails.

    Examples:
        # Lock a single attribute
        set_locked_hidden_state(attribute_path="myObject.myAttribute", locked=True)

        # Hide multiple attributes for multiple objects
        set_locked_hidden_state(obj_list=["object1", "object2"], attr_list=["attr1", "attr2"], hidden=True)
    """
    attributes_to_set = set()
    # Add One Line Attribute
    if attribute_path and isinstance(attribute_path, str):
        attributes_to_set.add(attribute_path)

    # Add object and attribute lists
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    if isinstance(attr_list, str):
        attr_list = [attr_list]
    if obj_list and attr_list and isinstance(obj_list, list) and isinstance(attr_list, list):  # Exists and is list
        for attr in attr_list:
            for obj in obj_list:
                attributes_to_set.add(f'{obj}.{attr}')

    # Set Locked/Hidden State
    for attr_path in attributes_to_set:
        try:
            if isinstance(locked, bool):
                if locked is True:
                    cmds.setAttr(attr_path, lock=True)
                elif locked is False:
                    cmds.setAttr(attr_path, lock=False)
            if isinstance(hidden, bool):
                if hidden is True:
                    cmds.setAttr(attr_path, keyable=False, channelBox=False)
                elif hidden is False:
                    cmds.setAttr(attr_path, channelBox=True)
                    cmds.setAttr(attr_path, keyable=True)
        except Exception as e:
            message = f'Unable to set attribute state for "{attr_path}". Issue: "{e}".'
            log_when_true(logger, message, do_log=verbose, level=log_level)
            if raise_exceptions:
                raise e


def set_trs_attr(target_obj, value_tuple, translate=False, rotate=False, scale=False,
                 space="world", verbose=True, log_level=logging.INFO):
    """
    Sets an attribute to the provided value (Uses "cmds.xform" function with world space)
    Default is translate only, use arguments to determine which channel to affect (translate, rotate, scale)

    Args:
        target_obj (str): Name of the target object (object that will receive transforms)
        value_tuple (tuple, list): A tuple or list  with three (3) floats used to set attributes. e.g. (1.5, 2, 5)
        translate (bool, optional): If active, it will apply these values to translate. Default False.
        rotate (bool, optional): If active, it will apply these values to rotate. Default False.
        scale (bool, optional): If active, it will apply these values to scale. Default False.
        space (str, optional): Method used to apply values, can be "world" for world-space or "object" for object-space.
                               World-space moves the object as if it didn't have parents or hierarchy.
                               Object-space moves the object by simply changing the values
        verbose (bool, optional): If True, log messages will be displayed for each attribute retrieval operation.
        log_level (int, optional): The logging level to use when verbose is True. Default is logging.INFO.

    """
    if not target_obj or not cmds.objExists(target_obj):
        message = f'Unable to set attribute "{target_obj}" does not exist or has non-unique name.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return
    if value_tuple and isinstance(value_tuple, list):
        value_tuple = tuple(value_tuple)
    if not value_tuple or not isinstance(value_tuple, tuple):
        message = f'Unable to set value "{value_tuple}". It must be a tuple or a list with three (3) floats.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return
    try:
        # Translate
        if translate and space == "world":
            cmds.xform(target_obj, ws=True, t=value_tuple)
        elif translate and space == "object":
            set_attr(f'{target_obj}.tx', value=value_tuple[0], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.ty', value=value_tuple[1], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.tz', value=value_tuple[2], verbose=verbose, log_level=log_level)
        # Rotate
        if rotate and space == "world":
            cmds.xform(target_obj, ws=True, ro=value_tuple)
        elif rotate and space == "object":
            set_attr(f'{target_obj}.rx', value=value_tuple[0], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.ry', value=value_tuple[1], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.rz', value=value_tuple[2], verbose=verbose, log_level=log_level)
        # Scale
        if scale and space == "world":
            cmds.xform(target_obj, ws=True, s=value_tuple)
        elif scale and space == "object":
            set_attr(f'{target_obj}.sx', value=value_tuple[0], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.sy', value=value_tuple[1], verbose=verbose, log_level=log_level)
            set_attr(f'{target_obj}.sz', value=value_tuple[2], verbose=verbose, log_level=log_level)
    except Exception as e:
        message = f'An error was raised while setting attributes "{e}".'
        log_when_true(logger, message, do_log=verbose, level=log_level)


def hide_lock_default_attrs(obj_list, translate=False, rotate=False, scale=False, visibility=False):
    """
    Locks default TRS+V channels
    Args:
        obj_list (str, list): Name of the object(s) to lock TRS+V attributes
        translate (bool, optional): If active, translate (position) will be affected. (locked, hidden)
        rotate (bool, optional): If active, rotate (rotation) will be affected. (locked, hidden)
        scale (bool, optional): If active, scale will be affected. (locked, hidden)
        visibility (bool, optional): If active, function also locks and hides visibility
    """
    channels = []
    if not obj_list:
        return
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if translate:
        channels.append('t')
    if rotate:
        channels.append('r')
    if scale:
        channels.append('s')
    for obj in obj_list:
        for channel in channels:
            for axis in ['x', 'y', 'z']:
                cmds.setAttr(f'{obj}.{channel}{axis}', lock=True, keyable=False, channelBox=False)
        if visibility:
            cmds.setAttr(f'{obj}.v', lock=True, keyable=False, channelBox=False)


def freeze_channels(obj_list, freeze_translate=True, freeze_rotate=True, freeze_scale=True):
    """
    Freeze individual channels of an object's translation, rotation, or scale in Autodesk Maya.

    Args:
        obj_list (str, list): The name of the object or a list of objects. (str is automatically converted to list)
        freeze_translate (bool, optional): When active, it will attempt to freeze translate.
        freeze_rotate (bool, optional): When active, it will attempt to freeze rotate.
        freeze_scale (bool, optional): When active, it will attempt to freeze scale.
    Returns:
        bool: True if all provided objects were fully frozen. False if something failed.
    """
    all_frozen = True
    if not obj_list:
        logger.debug('Nothing frozen. Empty "object_list" argument.')
        return False
    if isinstance(obj_list, str):  # Convert to list in case it's just one object.
        obj_list = [obj_list]
    for obj in obj_list:
        if not obj or not cmds.objExists(obj):
            all_frozen = False
            continue
        try:
            if freeze_translate:
                cmds.makeIdentity(obj, apply=True, translate=True, rotate=False, scale=False)
        except Exception as e:
            logger.debug(f'Failed to free "translate" for "{obj}". Issue: {e}')
            all_frozen = False
        try:
            if freeze_rotate:
                cmds.makeIdentity(obj, apply=True, translate=False, rotate=True, scale=False)
        except Exception as e:
            logger.debug(f'Failed to free "rotate" for "{obj}". Issue: {e}')
            all_frozen = False
        try:
            if freeze_scale:
                cmds.makeIdentity(obj, apply=True, translate=False, rotate=False, scale=True)
        except Exception as e:
            logger.debug(f'Failed to free "scale" for "{obj}". Issue: {e}')
            all_frozen = False
    return all_frozen


def rescale(obj, scale, freeze=True):
    """
    Sets the scaleXYZ to the provided scale value.
    It's also possible to freeze the object, so its components receive a new scale instead.
    Args:
        obj (string) Name of the object, for example "pSphere1"
        scale (float) The new scale value, for example 0.5
                      (this would cause it to be half of its initial size in case it was previously one)
        freeze: (bool) Determines if the object scale should be frozen after updated
    """
    cmds.setAttr(obj + '.scaleX', scale)
    cmds.setAttr(obj + '.scaleY', scale)
    cmds.setAttr(obj + '.scaleZ', scale)
    if freeze:
        freeze_channels(obj, freeze_translate=False, freeze_rotate=False, freeze_scale=True)


def selection_unlock_default_channels(feedback=True):
    """
    Unlocks Translate, Rotate, Scale for the selected objects
    Args:
        feedback (bool, optional): If active, it will return feedback at the end of the operation.
    Returns:
        int: Number of affected objects.
    """
    func_name = 'Unlock Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=func_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning('Nothing selected. Please select an object and try again.')
        return
    unlocked_counter = 0
    try:
        for obj in selection:
            try:
                set_attr_state(obj_list=obj, attr_list=DEFAULT_ATTRS, locked=False, raise_exceptions=True)
                unlocked_counter += 1
            except Exception as e:
                errors += str(e) + '\n'
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=func_name)

    if errors != '':
        print('#### Errors: ####')
        print(errors)
        cmds.warning('Some channels were not unlocked . Open the script editor for a list of errors.')

    if feedback:
        feedback = FeedbackMessage(quantity=unlocked_counter,
                                   singular='object had its',
                                   plural='objects had their',
                                   conclusion='default channels unlocked.')
        feedback.print_inview_message()
    return unlocked_counter


def selection_unhide_default_channels(feedback=True):
    """
    Un-hides Translate, Rotate, Scale for the selected objects
    Args:
        feedback (bool, optional): If active, it will return feedback at the end of the operation.
    Returns:
        int: Number of affected objects.
    """
    func_name = 'Unhide Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=func_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning('Nothing selected. Please select an object and try again.')
        return
    unhidden_counter = 0
    try:
        for obj in selection:
            try:
                set_attr_state(obj_list=obj, attr_list=DEFAULT_ATTRS, hidden=False, raise_exceptions=True)
                unhidden_counter += 1
            except Exception as e:
                errors += str(e) + '\n'
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=func_name)

    if errors != '':
        print('#### Errors: ####')
        print(errors)
        cmds.warning('Some channels were not made visible . Open the script editor for a list of issues.')

    if feedback:
        feedback = FeedbackMessage(quantity=unhidden_counter,
                                   singular='object had its',
                                   plural='objects had their',
                                   conclusion='default channels made visible.')
        feedback.print_inview_message()
    return unhidden_counter


# --------------------------------------------- Getters ---------------------------------------------
def get_attr(attribute_path=None, obj_name=None, attr_name=None, enum_as_string=False,
             verbose=True, log_level=logging.INFO):
    """
    This function retrieves the value of the given attribute using the provided attribute path or
    object name and attribute name.

    Note, when getting a double3 and the result is a single element (usually a tuple) inside a list,
          it returns only the element instead to avoid the unnecessary nested return.

    Args:
        attribute_path (str, optional): Full path to the attribute in the format "object.attribute".
            Use this or provide obj_name and attr_name separately, not both.
        obj_name (str, optional): Name of the object that holds the attribute. Required if using attr_name.
        attr_name (str, optional): Name of the attribute to retrieve. Required if using obj_name.
        enum_as_string (bool, optional): If True and attribute is of type "enum", return the enum value as a string.
                                         If False, return the integer enum value. Defaults to False.
        verbose (bool, optional): If True, log error messages to console. Defaults to True.
        log_level (int, optional): Logging level for error messages, using the constants from the logging module.
            Defaults to logging.INFO.

    Returns:
        any: The value of the specified attribute. Returns None if the attribute is not found or if errors occur.

    Examples:
        value = get_attr(attribute_path="myCube.translateX")
        # Returns the X translation value of the "myCube" object.

        value = get_attr(obj_name="myCube", attr_name="rotateY")
        # Returns the Y rotation value of the "myCube" object.

        value = get_attr(attribute_path="mySphere.myEnumAttribute", enum_as_string=True)
        # Returns the enum value of the "myEnumAttribute" as a string.

    """
    # Validate parameters
    if attribute_path and (obj_name or attr_name):
        message = f'Unable to get attribute value. Multiple get methods were provided in the same function. ' \
                  f'Provide the entire path to attribute or separated object and attribute names, not both.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return None

    if obj_name and (not attr_name or not isinstance(attr_name, str)):
        message = f'Unable to get attribute. Missing attribute name or non-string provided.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return

    if attr_name and (not obj_name or not isinstance(obj_name, str)):
        message = f'Unable to get attribute. Missing source object name or non-string provided.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return

    if not attribute_path and obj_name and attr_name:
        attribute_path = f'{obj_name}.{attr_name}'

    if attribute_path and not cmds.objExists(attribute_path):
        message = f'Unable to get attribute. Missing source attribute or non-unique name conflict.'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return None

    # Get Attribute
    attr_type = cmds.getAttr(attribute_path, type=True) or ""
    if attr_type == "double3":
        value = cmds.getAttr(attribute_path)
        if value and len(value) == 1:
            value = value[0]
    elif enum_as_string and attr_type == "enum":
        value = cmds.getAttr(attribute_path, asString=True)
    else:
        value = cmds.getAttr(attribute_path)
    return value


def get_multiple_attr(attribute_path=None, obj_list=None, attr_list=None, enum_as_string=False,
                      verbose=True, log_level=logging.INFO, raise_exceptions=False):
    """
    This function retrieves the values of specified attributes using Maya's `cmds.getAttr` function.
    It provides options to get attributes for a single attribute path or multiple objects and attributes.
    It does not raise errors, but can log them with the provided level determined as an argument.

    Args:
        attribute_path (str, optional): A single-line object attribute path in the format "object.attribute".
        obj_list (str ,list, optional): The name of the object or a list of object names. e.g. ["cube1", "cube2"]
        attr_list (str ,list, optional): The name of the attribute or a list of attribute names. e.g. ["tx", "ty"]
        enum_as_string (bool, optional): If True and attribute is of type "enum", return the enum value as a string.
                                         If False, return the integer enum value. Defaults to False.
        verbose (bool, optional): If True, log messages will be displayed for each attribute retrieval operation.
        log_level (int, optional): The logging level to use when verbose is True. Default is logging.INFO.
        raise_exceptions (bool, optional): If active, the function will raise exceptions whenever something fails.

    Returns:
        dict: A dictionary containing attribute paths as keys and their corresponding values.

    Examples:
        # Get a single attribute value
        get_attr(attribute_path="myObject.myAttribute")

        # Get multiple attributes for multiple objects
        get_attr(obj_list=["object1", "object2"], attr_list=["attr1", "attr2"])
    """
    attribute_values = {}

    # Add One Line Attribute
    if attribute_path and isinstance(attribute_path, str):
        try:
            value = get_attr(attribute_path=attribute_path, enum_as_string=enum_as_string,
                             verbose=verbose, log_level=log_level)
            attribute_values[attribute_path] = value
        except Exception as e:
            message = f'Unable to retrieve attribute "{attribute_path}" value. Issue: "{e}".'
            log_when_true(logger, message, do_log=verbose, level=log_level)
            if raise_exceptions:
                raise e

    # Add object and attribute lists
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    if isinstance(attr_list, str):
        attr_list = [attr_list]
    if obj_list and attr_list and isinstance(obj_list, list) and isinstance(attr_list, list):
        for attr in attr_list:
            for obj in obj_list:
                attr_path = f'{obj}.{attr}'
                try:
                    value = get_attr(attribute_path=attr_path, enum_as_string=enum_as_string,
                                     verbose=verbose, log_level=log_level)
                    attribute_values[attr_path] = value
                except Exception as e:
                    message = f'Unable to retrieve attribute "{attr_path}" value. Issue: "{e}".'
                    log_when_true(logger, message, do_log=verbose, level=log_level)
                    if raise_exceptions:
                        raise e

    return attribute_values


def get_trs_attr_as_list(obj, verbose=True):
    """
    Gets Translate, Rotation and Scale values as a list
    Args:
        obj (str): Name of the source object
        verbose (bool, optional): If active, it will return a warning when the object is missing.
    Returns:
        list or None: A list with TRS values in order [TX, TY, TZ, RX, RY, RZ, SX, SY, SZ], None if missing object.
                     e.g. [0, 0, 0, 15, 15, 15, 1, 1, 1]
    """
    if not obj or not cmds.objExists(obj):
        if verbose:
            logger.warning(f'Unable to get TRS channels as list. Unable to find object "{obj}".')
        return
    output = []
    for channel in DEFAULT_CHANNELS:  # TRS
        for dimension in DEFAULT_DIMENSIONS:  # XYZ
            value = get_attr(f'{obj}.{channel}{dimension}')
            output.append(value)
    return output


def get_trs_attr_as_formatted_string(obj_list, decimal_place=2, add_description=False, add_object=True,
                                     separate_channels=False, strip_zeroes=True):
    """
    Returns transforms as list
    Args:
        obj_list (list, str): List objects to extract the transform from (If a string, it gets auto converted to list)
        decimal_place (int, optional): How precise you want the extracted values to be (formats the float it gets)
        add_object (bool, optional): If active, it will include a variable describing the source object name.
        add_description (bool, optional): If active, it will include a comment at the top describing data.
        separate_channels (bool, optional): If separating channels, it will return T, R and S as different lists
        strip_zeroes (bool, optional): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        str: A string with the python code for the transform values. [TX, TY, TZ, RX, RY, RZ, SX, SY, SZ]
             e.g.
                source_object = "pCube1"
                attr_list = [0, 0, 0, 15, 15, 15, 1, 1, 1] # TRS (XYZ)
    """
    if not obj_list:
        logger.debug(f'Unable to get TRS as formatted string. Missing source list.')
        return ""
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]

    output = ''
    for obj in obj_list:
        if add_description:
            output += f'\n# Transform Data for "{obj}":\n'
        data = []
        for channel in DEFAULT_CHANNELS:  # TRS
            for dimension in DEFAULT_DIMENSIONS:  # XYZ
                value = cmds.getAttr(obj + '.' + channel + dimension)
                if strip_zeroes:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f"))).rstrip('0').rstrip('.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                    data.append(formatted_value)
                else:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f")))
                    if formatted_value == '-0.0':
                        formatted_value = '0.0'
                    data.append(formatted_value)

        if not separate_channels:
            if add_object:
                output += f'source_obj = "{str(obj)}"\n'
            output += 'trs_attr_list = ' + str(data).replace("'", "")
        else:
            if add_object:
                output += f'source_obj = "{str(obj)}"' + '\n'
            output += 't_attr_list = [' + str(data[0]) + ', ' + str(data[1]) + ', ' + str(data[2]) + ']\n'
            output += 'r_attr_list = [' + str(data[3]) + ', ' + str(data[4]) + ', ' + str(data[5]) + ']\n'
            output += 's_attr_list = [' + str(data[6]) + ', ' + str(data[7]) + ', ' + str(data[8]) + ']\n'
    # Remove first and last new line
    _new_line = "\n"
    output = remove_prefix(output, _new_line)
    output = remove_suffix(output, _new_line)
    return output


def get_trs_attr_as_python(obj_list, use_loop=False, decimal_place=2, strip_zeroes=True):
    """
    Args:
        obj_list (list, str): List objects to extract the transform from (If a string, it gets auto converted to list)
        use_loop (optional, bool): If active, it will use a for loop in the output code (instead of simple lines)
        decimal_place (optional, int): How precise you want the extracted values to be (formats the float it gets)
        strip_zeroes (optional, bool): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        str: Python code used to set translate, rotate, and scale attributes.
    """
    if isinstance(obj_list, str):
        obj_list = [obj_list]

    output = ''
    for obj in obj_list:
        output += f'\n# Transform Data for "{obj}":\n'
        data = {}
        for channel in DEFAULT_CHANNELS:
            for dimension in DEFAULT_DIMENSIONS:
                attr_name = f"{obj}.{channel}{dimension}"
                value = cmds.getAttr(attr_name)
                formatted_value = format(value, f".{decimal_place}f")

                if strip_zeroes:
                    formatted_value = formatted_value.rstrip('0').rstrip('.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                else:
                    formatted_value = formatted_value

                if not cmds.getAttr(attr_name, lock=True) and not use_loop:
                    output += f'cmds.setAttr("{attr_name}", {formatted_value})\n'
                else:
                    data[channel + dimension] = float(formatted_value)

        if use_loop:
            import json
            data = json.dumps(data, ensure_ascii=False)
            output += f'for key, value in {data}.items():\n'
            output += f'\tif not cmds.getAttr(f"{obj}' + '.{key}"' + ', lock=True):\n'
            output += f'\t\tcmds.setAttr(f"{obj}' + '.{key}"' + ', value)\n'
    # Remove first and last new line
    _new_line = "\n"
    output = remove_prefix(output, _new_line)
    output = remove_suffix(output, _new_line)
    return output


def get_user_attr_to_python(obj_list, skip_locked=True, skip_connected=True):
    """
    Returns a string
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        skip_locked (bool, optional): If True, locked attributes will be ignored, otherwise all user-defined
                                      attributes are listed.
        skip_connected (bool, optional): If True, attributes receiving their data from a direct connections will be
                                        ignored as these cannot be set manually.

    Returns:
        str: Python code with extracted transform values.
             e.g.
             # User-Defined Attribute Data for "pSphere1":
             cmds.setAttr("pSphere1.myAttr", 0.0)"
    """
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    output = ''
    for obj in obj_list:
        output += '\n# User-Defined Attribute Data for "' + obj + '":\n'
        attributes = cmds.listAttr(obj, userDefined=True) or []
        # Check if locked
        if skip_locked:
            unlocked_attrs = []
            for attr in attributes:
                if not cmds.getAttr(f'{obj}.{attr}', lock=True):
                    unlocked_attrs.append(attr)
            attributes = unlocked_attrs
        if skip_connected:
            connected_attrs = []
            for attr in attributes:
                connections = cmds.listConnections(f'{obj}.{attr}', source=True, destination=False)
                if connections is None:
                    connected_attrs.append(attr)
            attributes = connected_attrs
        # Create code
        if not attributes:
            output += '# No user-defined attributes found on this object.\n'
        else:
            for attr in attributes:
                attr_type = cmds.getAttr(f'{obj}.{attr}', typ=True)
                value = cmds.getAttr(f'{obj}.{attr}')
                if attr_type == 'double3':
                    pass
                elif attr_type == 'string':
                    output += f'cmds.setAttr("{obj}.{attr}", """{str(value)}""", typ="string")\n'
                else:
                    output += f'cmds.setAttr("{obj}.{attr}", {str(value)})\n'
    # Remove first and last new line
    _new_line = "\n"
    output = remove_prefix(output, _new_line)
    output = remove_suffix(output, _new_line)
    return output


def list_user_defined_attr(obj, skip_nested=False, skip_parents=True):
    """
    Lists user defined attributes of a given Maya object.

    Args:
    obj (str): The name of the Maya object.
    skip_nested (bool, optional): If True, skip user-defined attributes that are nested under other attributes.
    skip_parents (bool, optional): If True, skip attributes that are parent of other of nested attributes.
                                   Warning, if both "skip_nested" and "skip_parents" are active simultaneously,
                                   vector attributes will be ignored completely.

    Returns:
    list: A list of user defined attribute names for the specified Maya object.
    """
    user_attrs = cmds.listAttr(obj, userDefined=True) or []
    to_skip = set()
    if skip_nested:
        for attr in user_attrs:
            children = cmds.attributeQuery(attr, node=obj, listChildren=True) or []
            to_skip.update(children)
    if skip_parents:
        for attr in user_attrs:
            children = cmds.attributeQuery(attr, node=obj, listChildren=True) or []
            if children:
                to_skip.add(attr)
    result = [item for item in user_attrs if item not in list(to_skip)]
    return result


# -------------------------------------------- Management -------------------------------------------
def add_attr_double_three(obj, attr_name, suffix="RGB", keyable=True):
    """
    Creates a double3 attribute and populates it with three (3) double attributes of the same name + suffix
    Args:
        obj (str): Name of the object to receive new attributes
        attr_name (str): Name of the attribute to be created
        suffix (str, optional) : Used as suffix for the three created attributes
        keyable (bool, optional): Determines if the attributes should be keyable or not. (Must be a 3 character string)
                                  First attribute uses the first letter, second the second letter, etc...
    """
    cmds.addAttr(obj, ln=attr_name, at='double3', k=keyable)
    cmds.addAttr(obj, ln=attr_name + suffix[0], at='double', k=keyable, parent=attr_name)
    cmds.addAttr(obj, ln=attr_name + suffix[1], at='double', k=keyable, parent=attr_name)
    cmds.addAttr(obj, ln=attr_name + suffix[2], at='double', k=keyable, parent=attr_name)


def add_separator_attr(target_object, attr_name="separator", custom_value=None):
    """
    Creates a locked enum attribute to be used as a separator
    Args:
        target_object (str, Node): Name of the object to affect in the operation
        attr_name (str, optional): Name of the attribute to add. Use camelCase for this string as it will obey the
                                   "niceName" pattern in Maya. e.g. "niceName" = "Nice Name"
        custom_value (str, None, optional): Enum value for the separator value.
                                               If not provided, default is "--------------". (14x "-")
    Returns:
        str: Full path to created attribute. 'target_object.attr_name'
    """
    separator_value = "-"*14
    if custom_value:
        separator_value = custom_value
    attribute_path = f'{target_object}.{attr_name}'
    if not cmds.objExists(attribute_path):
        cmds.addAttr(target_object, ln=attr_name, at='enum', en=separator_value, keyable=True)
        cmds.setAttr(attribute_path, e=True, lock=True)
    else:
        logger.warning(f'Separator attribute "{attribute_path}" already exists. Add Separator operation skipped.')
    return f'{target_object}.{attr_name}'


def add_attr(obj_list, attributes, attr_type="double", minimum=None, maximum=None, enum=None,
             default=None, is_keyable=True, verbose=False):
    """
    Adds attributes to the provided target list (list of objects)

    Args:
        obj_list (list, str): List of objects to which attributes will be added. (Strings are converted to list)
        attributes (list, str): List of attribute names to be added. (Strings are converted to single item list)
        attr_type (str, optional): Data type of the attribute (e.g., 'double', 'long', 'string', etc.).
                         For a full list see the documentation for "cmds.addAttr".
        minimum: Minimum value for the attribute. Optional.
        maximum: Maximum value for the attribute. Optional.
        enum (string, optional): A string with a list of potential enums. e.g. "Option1:Option2:Option3"
        default: Default value for the attribute. Optional.
        is_keyable (bool, optional): Whether the attribute should be keyable. Default is True.
        verbose (bool, optional): If active, this function will alert the user in case there were errors.
    Returns:
        list: List of created attributes.
    """
    added_attrs = []
    issues = {}
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if attributes and isinstance(attributes, str):
        attributes = [attributes]
    for target in obj_list:
        for attr_name in attributes:
            full_attr_name = f"{target}.{attr_name}"
            if not cmds.objExists(full_attr_name):
                attr_args = {'longName': attr_name}
                if attr_type != "string":
                    attr_args['attributeType'] = attr_type
                    if default is not None:  # Only works with non-string types
                        attr_args['defaultValue'] = default
                else:
                    attr_args['dataType'] = "string"
                if minimum is not None:
                    attr_args['minValue'] = minimum
                if maximum is not None:
                    attr_args['maxValue'] = maximum
                if is_keyable:
                    attr_args['keyable'] = True
                if enum:
                    attr_args['enumName'] = enum
                try:
                    cmds.addAttr(target, **attr_args)
                    if cmds.objExists(full_attr_name):
                        added_attrs.append(full_attr_name)
                        if attr_type == "string" and default is not None:  # Set String Default Value
                            cmds.setAttr(full_attr_name, str(default), typ='string')
                except Exception as e:
                    issues[full_attr_name] = e
    if issues and verbose:
        for attr, error in issues.items():
            logger.warning(f'"{attr}" returned the error: "{error}".')
        logger.warning('Errors were raised while adding attributes. See previous warnings for more information.')
    return added_attrs


def delete_user_defined_attrs(obj_list, delete_locked=True, verbose=True, raise_exceptions=False):
    """
    Deletes all User defined attributes for the selected objects.
    Args:
        obj_list (list, str): List of objects to delete user-defined attributes
                              (If a string, it gets auto converted to list with a single object)
        delete_locked (bool, optional): If active, it will also delete locked attributes.
        verbose (bool, optional): If active, it will print warning messages when necessary.
        raise_exceptions (bool, optional): If active, it will raise exceptions when something fails.
    Returns:
        list: List of deleted attributes
    """
    if not obj_list:
        logger.debug(f'Unable to delete user-defined attributes. Missing target list.')
        return []
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]

    custom_attributes = []
    deleted_attributes = []
    try:
        for obj in obj_list:
            attributes = cmds.listAttr(obj, userDefined=True) or []
            for attr in attributes:
                custom_attributes.append(f'{obj}.{attr}')

        for attr in custom_attributes:
            try:
                if delete_locked:
                    cmds.setAttr(f"{attr}", lock=False)
                cmds.deleteAttr(attr)
                deleted_attributes.append(attr)
            except Exception as e:
                logger.debug(str(e))
    except Exception as e:
        if verbose:
            logger.warning(f'An error occurred while deleting user-defined attributes. Issue: "{e}".')
        if raise_exceptions:
            raise e
    return deleted_attributes


def selection_delete_user_defined_attrs(delete_locked=True, feedback=True):
    """
    Deletes all User defined attributes for the selected objects.
    Args:
        delete_locked (bool, optional): If active, it will also delete locked attributes.
        feedback (bool, optional): If active, it will return feedback at the end of the operation.
    """
    function_name = 'Delete User Defined Attributes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)

    selection = cmds.ls(selection=True)
    if selection == 0:
        cmds.warning('Select at least one target object to delete custom attributes')
        return

    try:
        deleted_attrs = delete_user_defined_attrs(obj_list=selection,
                                                  delete_locked=delete_locked,
                                                  verbose=True) or []
        deleted_counter = 0
        if deleted_attrs:
            deleted_counter = len(deleted_attrs)
        if feedback:
            feedback = FeedbackMessage(quantity=deleted_counter,
                                       singular='user-defined attribute was',
                                       plural='user-defined attributes were',
                                       conclusion='deleted.',
                                       zero_overwrite_message='No user defined attributes were deleted.')
            feedback.print_inview_message()
    except Exception as e:
        cmds.warning(f'An error occurred while deleting user-defined attributes. Issue: "{e}".')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def copy_attr(source_attr_path, target_list, prefix=None):
    """
    Copies an attribute from a source object to a target object(s).

    Args:
        source_attr_path (str): The name of the attribute to copy, including the source object's name.
                                (e.g., "pSphere1.myAttr").
        target_list (str, list): The name of the target object(s) to copy the attribute to.
        prefix (str, optional): A prefix to add to the copied attribute name. Defaults to None.

    Returns:
        list: List of created attributes.
    """
    # Get attribute properties from the source attribute
    if not cmds.objExists(source_attr_path):
        logger.warning(f'Unable to copy attribute. Missing source attribute: "{source_attr_path}".')
        return []
    if '.' not in source_attr_path:
        logger.warning(f'Unable to copy attribute. Invalid source attribute: "{source_attr_path}".')
        return []
    # Extract Source obj and attr
    source_obj = source_attr_path.split('.')[0]
    source_attr = '.'.join(source_attr_path.split('.')[1:])
    # Get Attr Data
    attr_type = cmds.attributeQuery(source_attr, node=source_obj, attributeType=True)
    if attr_type == "typed":  # Update string to add pattern
        attr_type = "string"
    attr_data = {}
    if cmds.attributeQuery(source_attr, node=source_obj, minExists=True):
        min_val = cmds.attributeQuery(source_attr, node=source_obj, min=True)
        attr_data["minimum"] = min_val[0]
    if cmds.attributeQuery(source_attr, node=source_obj, maxExists=True):
        max_val = cmds.attributeQuery(source_attr, node=source_obj, max=True)
        attr_data["maximum"] = max_val[0]
    attr_data["is_keyable"] = cmds.attributeQuery(source_attr, node=source_obj, keyable=True)

    # If the attribute is of enum type, get enum names
    if attr_type == 'enum':
        enum_name = cmds.attributeQuery(source_attr, node=source_obj, listEnum=True)
        attr_data["enum"] = enum_name[0]

    # Adjust attribute name with prefix if provided
    if prefix:
        target_attr_name = f"{prefix}{upper_first_char(source_attr)}"
    else:
        target_attr_name = source_attr

    # Create attribute on target object with same properties
    current_value = cmds.getAttr(source_attr_path)
    return add_attr(obj_list=target_list,
                    attributes=target_attr_name,
                    attr_type=attr_type,
                    default=current_value, **attr_data, verbose=True)


def reroute_attr(source_attrs, target_obj, prefix=None, hide_source=True):
    """
    Copies an attribute from a source object to a target object(s),
    then uses the target object to control the previous initial attribute.
    obj1.attr <- controlled by <- obj2.attr

    Args:
        source_attrs (str, list): The name of the attribute to reroute, including the source object's name.
                                  (e.g., "pSphere1.myAttr").
        target_obj (str, list): The name of the target object to copy the attribute to. (new attribute holder)
        prefix (str, optional): A prefix to add to the copied attribute name. Defaults to None.
        hide_source (bool, optional): If True, the source attribute is hidden after receiving the data from
                                      the duplicated attribute.

    Returns:
        list: List of created attributes.
    """
    if isinstance(source_attrs, str):
        source_attrs = [source_attrs]
    created_attrs = []
    for source_attr in source_attrs:
        copied_attrs = copy_attr(source_attr_path=source_attr, target_list=target_obj, prefix=prefix)
        for copied_attr in copied_attrs:
            cmds.connectAttr(copied_attr, source_attr)
            created_attrs.append(copied_attr)
        if hide_source:
            cmds.setAttr(source_attr, keyable=False, channelBox=False)
    return created_attrs


# -------------------------------------------- Connection -------------------------------------------
def connect_attr(source_attr, target_attr_list, force=False,
                 verbose=False, log_level=logging.INFO, raise_exceptions=False):
    """
    This function sets locked or hidden states of specified attributes of objects using Maya's `cmds.setAttr` function.
    It provides options to set locked or hidden states for a single attribute path, multiple objects and attributes.
    It does not raise errors, but can log them with the provided level determined as an argument.

    Args:
        source_attr (str, optional): A single-line object attribute path in the format "object.attribute".
        target_attr_list (str ,list, optional): The name of the attribute or a list of attribute names to receive
                                                the connection. e.g. ["obj.tx", "obj.ty"]
        force (bool, optional): If active, it will try to force the connection (overwrite when existing)
        verbose (bool, optional): If True, log messages will be displayed describing the operation.
        log_level (int, optional): The logging level to use when verbose is True. Default is logging.INFO.
        raise_exceptions (bool, optional): If active, the function will raise exceptions whenever something fails.
    """
    if source_attr and not isinstance(source_attr, str):
        message = f'Unable to create connection invalid source attribute "{source_attr}".'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return
    if not cmds.objExists(source_attr):
        message = f'Unable to create connection missing source attribute "{source_attr}".'
        log_when_true(logger, message, do_log=verbose, level=log_level)
        return

    # Add object and attribute lists
    if isinstance(target_attr_list, str):
        target_attr_list = [target_attr_list]

    for target_attr in target_attr_list:
        try:
            cmds.connectAttr(source_attr, target_attr, force=force)
        except Exception as e:
            message = f'Unable to connect attributes. Issue: "{e}".'
            log_when_true(logger, message, do_log=verbose, level=log_level)
            if raise_exceptions:
                raise e


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    sel = cmds.ls(selection=True)
    # add_attr(obj_list=sel, attributes=["custom_attr_one", "custom_attr_two"])
    # delete_user_defined_attrs(sel)
    # cmds.file(new=True, force=True)
    # cube_one = cmds.polyCube(ch=False)[0]
    # cube_two = cmds.polyCube(ch=False)[0]
    # add_attr(cube_one, attr_type='double', attributes="doubleAttr")
    # add_attr(cube_one, attr_type='long', attributes="intAttr")
    # add_attr(cube_one, attr_type='enum', attributes="enumAttr", enum='Option1:Option2:Option3')
    # add_attr(cube_one, attr_type='bool', attributes="boolAttr")
    # add_attr(cube_one, attr_type='string', attributes="stringAttr")
    #
    # reroute_attr(source_attrs=[f'{cube_one}.doubleAttr', f'{cube_one}.intAttr', f'{cube_one}.enumAttr',
    #                            f'{cube_one}.boolAttr', f'{cube_one}.stringAttr'], target_obj=cube_two)
    print(get_user_attr_to_python(f"left_backKnee_driverJnt_ctrl"))
