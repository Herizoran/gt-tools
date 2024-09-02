"""
Display Module - Update how you see elements in the viewport

Code Namespace:
    core_display  # import gt.core.display as core_display
"""

from gt.core.feedback import FeedbackMessage
from gt.core.naming import get_short_name
import maya.cmds as cmds
import maya.mel as mel
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def set_lra_state(obj_list, state=True, verbose=False):
    """
    Sets the state of the Local Rotation Axis (LRA) for the provided objects.
    Args:
        obj_list (list): A list of objects to be affected (strings, paths to the object)
        state (bool, optional): Visibility state. If True, it's visible/active/on.
                                If False, it's invisible/inactive/off
        verbose (bool, optional): If active, it will give warnings when the operation failed.
    Returns:
        list: List of affected objects.
    """
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    affected = []
    for obj in obj_list:
        try:
            cmds.setAttr(f"{obj}.displayLocalAxis", int(state))
            affected.append(obj)
        except Exception as e:
            if verbose:
                cmds.warning(f'Unable to set LRA state for "{str(obj)}". Issue: {e}')
    return affected


def toggle_uniform_lra(obj_list=None, verbose=True):
    """
    Makes the visibility of the Local Rotation Axis uniform  according to the current state of the majority of them.

    Args:
        obj_list (list, str): A list with the name of the objects it should affect. (Strings are converted into list)
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        bool or None: Current status of the LRA visibility (toggle target) or None if operation failed.
    """
    function_name = "Uniform LRA Toggle"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    lra_state_result = None
    try:
        errors = ""
        _target_list = None
        if obj_list and isinstance(obj_list, list):
            _target_list = obj_list
        if obj_list and isinstance(obj_list, str):
            _target_list = [obj_list]
        if not _target_list:
            _target_list = cmds.ls(selection=True, long=True) or []
        if not _target_list:
            cmds.warning("Select at least one object and try again.")
            return

        inactive_lra = []
        active_lra = []
        operation_result = "off"

        for obj in _target_list:
            try:
                current_lra_state = cmds.getAttr(obj + ".displayLocalAxis")
                if current_lra_state:
                    active_lra.append(obj)
                else:
                    inactive_lra.append(obj)
            except Exception as e:
                errors += str(e) + "\n"

        if len(active_lra) == 0:
            for obj in inactive_lra:
                try:
                    cmds.setAttr(obj + ".displayLocalAxis", 1)
                    operation_result = "on"
                    lra_state_result = True
                except Exception as e:
                    errors += str(e) + "\n"
        elif len(inactive_lra) == 0:
            for obj in active_lra:
                try:
                    cmds.setAttr(obj + ".displayLocalAxis", 0)
                    lra_state_result = False
                except Exception as e:
                    errors += str(e) + "\n"
        elif len(active_lra) > len(inactive_lra):
            for obj in inactive_lra:
                try:
                    cmds.setAttr(obj + ".displayLocalAxis", 1)
                    operation_result = "on"
                    lra_state_result = True
                except Exception as e:
                    errors += str(e) + "\n"
        else:
            for obj in active_lra:
                try:
                    cmds.setAttr(obj + ".displayLocalAxis", 0)
                    lra_state_result = False
                except Exception as e:
                    errors += str(e) + "\n"
        if verbose:
            feedback = FeedbackMessage(
                intro="LRA Visibility set to:",
                conclusion=str(operation_result),
                style_conclusion="color:#FF0000;text-decoration:underline;",
                zero_overwrite_message="No user defined attributes were deleted.",
            )
            feedback.print_inview_message(system_write=False)
            sys.stdout.write("\n" + 'Local Rotation Axes Visibility set to: "' + operation_result + '"')

        if errors != "" and verbose:
            print("#### Errors: ####")
            print(errors)
            cmds.warning("The script couldn't read or write some LRA states. Open script editor for more info.")
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    return lra_state_result


def toggle_uniform_jnt_label(jnt_list=None, verbose=True):
    """
    Makes the visibility of the Joint Labels uniform according to the current state of the majority of them.
    Args:
        jnt_list (list, str): A list with the name of the objects it should affect. (Strings are converted into list)
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        bool or None: Current status of the label visibility (toggle target) or None if operation failed.
    """

    function_name = "Uniform Joint Label Toggle"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    label_state = None
    try:
        errors = ""
        _joints = None
        if jnt_list and isinstance(jnt_list, list):
            _joints = jnt_list
        if jnt_list and isinstance(jnt_list, str):
            _joints = [jnt_list]
        if not _joints:
            _joints = cmds.ls(type="joint", long=True) or []

        inactive_label = []
        active_label = []
        operation_result = "off"

        for obj in _joints:
            try:
                current_label_state = cmds.getAttr(f"{obj}.drawLabel")
                if current_label_state:
                    active_label.append(obj)
                else:
                    inactive_label.append(obj)
            except Exception as e:
                errors += str(e) + "\n"

        if len(active_label) == 0:
            for obj in inactive_label:
                try:
                    cmds.setAttr(f"{obj}.drawLabel", 1)
                    operation_result = "on"
                    label_state = True
                except Exception as e:
                    errors += str(e) + "\n"
        elif len(inactive_label) == 0:
            for obj in active_label:
                try:
                    cmds.setAttr(f"{obj}.drawLabel", 0)
                    label_state = False
                except Exception as e:
                    errors += str(e) + "\n"
        elif len(active_label) > len(inactive_label):
            for obj in inactive_label:
                try:
                    cmds.setAttr(f"{obj}.drawLabel", 1)
                    operation_result = "on"
                    label_state = True
                except Exception as e:
                    errors += str(e) + "\n"
        else:
            for obj in active_label:
                try:
                    cmds.setAttr(f"{obj}.drawLabel", 0)
                    label_state = False
                except Exception as e:
                    errors += str(e) + "\n"
        if verbose:
            feedback = FeedbackMessage(
                quantity=len(_joints),
                skip_quantity_print=True,
                intro="Joint Label Visibility set to:",
                conclusion=str(operation_result),
                style_conclusion="color:#FF0000;text-decoration:underline;",
                zero_overwrite_message="No joints found in this scene.",
            )
            feedback.print_inview_message(system_write=False)
            sys.stdout.write("\n" + 'Joint Label Visibility set to: "' + operation_result + '"')

        if errors != "" and verbose:
            print("#### Errors: ####")
            print(errors)
            cmds.warning(
                'The script couldn\'t read or write some "drawLabel" states. ' "Open script editor for more info."
            )
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    return label_state


def toggle_full_hud(verbose=True):
    """
    Toggles common HUD options so all the common ones are either active or inactive
    Args:
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        bool or None: Current status of the hud visibility (toggle target) or None if operation failed.
    """
    hud_current_state = {}

    # 1 - Animation Details
    hud_current_state["animationDetailsVisibility"] = int(mel.eval("optionVar -q animationDetailsVisibility;"))
    # 2 - Cache
    try:
        from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud

        hud_current_state["CachePreferenceHud"] = int(CachePreferenceHud().get_value() or 0)
    except Exception as e:
        logger.debug(str(e))
        hud_current_state["CachePreferenceHud"] = 0
    # 3 - Camera Names
    hud_current_state["cameraNamesVisibility"] = int(mel.eval("optionVar -q cameraNamesVisibility;"))
    # 4 - Caps Lock
    hud_current_state["capsLockVisibility"] = int(mel.eval("optionVar -q capsLockVisibility;"))
    # 5 - Current Asset
    hud_current_state["currentContainerVisibility"] = int(mel.eval("optionVar -q currentContainerVisibility;"))
    # 6 - Current Frame
    hud_current_state["currentFrameVisibility"] = int(mel.eval("optionVar -q currentFrameVisibility;"))
    # 7 - Evaluation
    hud_current_state["evaluationVisibility"] = int(mel.eval("optionVar -q evaluationVisibility;"))
    # 8 - Focal Length
    hud_current_state["focalLengthVisibility"] = int(mel.eval("optionVar -q focalLengthVisibility;"))
    # 9 - Frame Rate
    hud_current_state["frameRateVisibility"] = int(mel.eval("optionVar -q frameRateVisibility;"))
    # 10 - HumanIK Details
    hud_current_state["hikDetailsVisibility"] = int(mel.eval("optionVar -q hikDetailsVisibility;"))
    # 11 - Material Loading Details
    hud_current_state["materialLoadingDetailsVisibility"] = int(
        mel.eval("optionVar -q materialLoadingDetailsVisibility;")
    )
    # 12 - Object Details
    hud_current_state["objectDetailsVisibility"] = int(mel.eval("optionVar -q objectDetailsVisibility;"))
    # 13 - Origin Axis - Ignored as non-hud element
    # hud_current_state['originAxesMenuUpdate'] = mel.eval('optionVar -q originAxesMenuUpdate;')
    # 14 - Particle Count
    hud_current_state["particleCountVisibility"] = int(mel.eval("optionVar -q particleCountVisibility;"))
    # 15 - Poly Count
    hud_current_state["polyCountVisibility"] = int(mel.eval("optionVar -q polyCountVisibility;"))
    # 16 - Scene Timecode
    hud_current_state["sceneTimecodeVisibility"] = int(mel.eval("optionVar -q sceneTimecodeVisibility;"))
    # 17 - Select Details
    hud_current_state["selectDetailsVisibility"] = int(mel.eval("optionVar -q selectDetailsVisibility;"))
    # 18 - Symmetry
    hud_current_state["symmetryVisibility"] = int(mel.eval("optionVar -q symmetryVisibility;"))
    # 19 - View Axis
    hud_current_state["viewAxisVisibility"] = int(mel.eval("optionVar -q viewAxisVisibility;"))
    # 20 - Viewport Renderer
    hud_current_state["viewportRendererVisibility"] = int(mel.eval("optionVar -q viewportRendererVisibility;"))
    # ------- Separator -------
    # 21 - In-view Messages
    hud_current_state["inViewMessageEnable"] = int(mel.eval("optionVar -q inViewMessageEnable;"))
    # 22 - In-view Editors
    hud_current_state["inViewEditorVisible"] = int(mel.eval("optionVar -q inViewEditorVisible;"))
    # Conditional - XGen Info
    hud_current_state["xgenHUDVisibility"] = int(mel.eval("optionVar -q xgenHUDVisibility;"))

    # Check if toggle ON or OFF
    toggle = True
    count = 0
    for item_state in hud_current_state:
        if hud_current_state.get(item_state):
            count += 1
    # More than half is on, so OFF else ON (Default)
    if count > len(hud_current_state) / 2:
        toggle = False

    # Toggles non-standard hud elements
    if toggle:
        mel.eval("setAnimationDetailsVisibility(true)")
        try:
            from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud

            CachePreferenceHud().set_value(True)
        except Exception as e:
            logger.debug(str(e))
        mel.eval("setCameraNamesVisibility(true)")
        mel.eval("setCapsLockVisibility(true)")
        mel.eval("setCurrentContainerVisibility(true)")
        mel.eval("setCurrentFrameVisibility(true)")
        mel.eval("SetEvaluationManagerHUDVisibility(1)")
        mel.eval("setFocalLengthVisibility(true)")
        mel.eval("setFrameRateVisibility(true)")
        if not hud_current_state.get("hikDetailsVisibility"):
            cmds.ToggleHikDetails()
            mel.eval("catchQuiet(setHikDetailsVisibility(true));")
        mel.eval("ToggleMaterialLoadingDetailsHUDVisibility(true)")
        mel.eval("setObjectDetailsVisibility(true)")
        mel.eval("setParticleCountVisibility(true)")
        mel.eval("setPolyCountVisibility(true)")
        mel.eval("setSceneTimecodeVisibility(true)")
        mel.eval("setSelectDetailsVisibility(true)")
        mel.eval("setSymmetryVisibility(true)")
        mel.eval("setViewAxisVisibility(true)")
        mel.eval("setViewportRendererVisibility(true)")
        mel.eval("catchQuiet(setXGenHUDVisibility(true));")

        if not hud_current_state.get("inViewMessageEnable"):
            cmds.ToggleInViewMessage()
        if not hud_current_state.get("inViewEditorVisible"):
            cmds.ToggleInViewEditor()
    else:
        mel.eval("setAnimationDetailsVisibility(false)")
        try:
            from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud

            CachePreferenceHud().set_value(False)
        except Exception as e:
            logger.debug(str(e))
        mel.eval("setCurrentContainerVisibility(false)")
        mel.eval("setCurrentFrameVisibility(false)")
        mel.eval("SetEvaluationManagerHUDVisibility(0)")
        mel.eval("setFocalLengthVisibility(false)")
        mel.eval("setFrameRateVisibility(false)")
        if hud_current_state.get("hikDetailsVisibility"):
            cmds.ToggleHikDetails()
            mel.eval("catchQuiet(setHikDetailsVisibility(false));")
            mel.eval("catchQuiet(hikDetailsKeyingMode());")
        mel.eval("ToggleMaterialLoadingDetailsHUDVisibility(false)")
        mel.eval("setObjectDetailsVisibility(false)")
        mel.eval("setParticleCountVisibility(false)")
        mel.eval("setPolyCountVisibility(false)")
        mel.eval("setSceneTimecodeVisibility(false)")
        mel.eval("setSelectDetailsVisibility(false)")
        mel.eval("setViewportRendererVisibility(false)")
        mel.eval("catchQuiet(setXGenHUDVisibility(false));")
    # Default states are preserved: camera names, caps lock, symmetry, view axis, in-view messages and in-view editor
    # Give feedback
    operation_result = "off"
    if toggle:
        operation_result = "on"
    if verbose:
        feedback = FeedbackMessage(
            intro="Hud Visibility set to:",
            conclusion=str(operation_result),
            style_conclusion="color:#FF0000;text-decoration:underline;",
            zero_overwrite_message="No user defined attributes were deleted.",
        )
        feedback.print_inview_message(system_write=False)
        sys.stdout.write("\n" + 'Hud Visibility set to: "' + operation_result + '"')
    return toggle


def set_joint_name_as_label(joints=None, verbose=True):
    """
    Transfer the name of the joint to its label.
    Args:
        joints (list, str): A list with the name of the objects it should affect. (Strings are converted into list)
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        int: Number of affected joints.
    """
    _joints = None
    if joints and isinstance(joints, list):
        _joints = joints
    if joints and isinstance(joints, str):
        _joints = [joints]
    if not _joints:
        _joints = cmds.ls(selection=True, typ="joint") or []

    if not _joints:
        if verbose:
            cmds.warning("No joints found in selection. Select joints and try again.")
        return

    function_name = "Set Joint Name as Label"
    counter = 0
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        for joint in _joints:
            short_name = get_short_name(joint)
            cmds.setAttr(joint + ".side", 0)  # Center (No Extra String)
            cmds.setAttr(joint + ".type", 18)  # Other
            cmds.setAttr(joint + ".otherType", short_name, typ="string")
            counter += 1
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if verbose:
        feedback = FeedbackMessage(
            quantity=counter,
            singular="label was",
            plural="labels were",
            conclusion="updated.",
            zero_overwrite_message="No labels were updated.",
        )
        feedback.print_inview_message()
    return counter


def generate_udim_previews(verbose=True):
    """
    Generates UDIM previews for all file nodes
    Args:
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        int: Number of affected file nodes.
    """
    errors = ""
    counter = 0
    all_file_nodes = cmds.ls(type="file")
    for file_node in all_file_nodes:
        try:
            mel.eval(f"generateUvTilePreview {file_node};")
            counter += 1
        except Exception as e:
            errors += str(e) + "\n"

    if errors and verbose:
        print(("#" * 50) + "\n")
        print(errors)
        print("#" * 50)
    if verbose:
        feedback = FeedbackMessage(
            prefix="Previews generated for all",
            intro="UDIM",
            style_intro="color:#FF0000;text-decoration:underline;",
            conclusion="file nodes.",
        )
        feedback.print_inview_message()
    return counter


def reset_joint_display(jnt_list=None, verbose=True):
    """
    Resets the radius and drawStyle attributes for provided joints. (or all joints)
    then changes the global multiplier (jointDisplayScale) back to one

    Args:
        jnt_list (list, str): A list with the name of the objects it should affect. (Strings are converted into list)
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        int: Number of affected joints.
    """
    errors = ""
    target_radius = 1
    counter = 0

    _joints = None
    if jnt_list and isinstance(jnt_list, list):
        _joints = jnt_list
    if jnt_list and isinstance(jnt_list, str):
        _joints = [jnt_list]
    if not _joints:
        _joints = cmds.ls(type="joint", long=True) or []
    # Update joints
    for obj in _joints:
        try:
            if cmds.objExists(obj):
                if cmds.getAttr(obj + ".radius", lock=True) is False:
                    cmds.setAttr(obj + ".radius", 1)

                if cmds.getAttr(obj + ".v", lock=True) is False:
                    cmds.setAttr(obj + ".v", 1)

                if cmds.getAttr(obj + ".drawStyle", lock=True) is False:
                    cmds.setAttr(obj + ".drawStyle", 0)
                counter += 1
        except Exception as exception:
            logger.debug(str(exception))
            errors += str(exception) + "\n"
    cmds.jointDisplayScale(target_radius)
    # Give feedback
    if verbose:
        feedback = FeedbackMessage(
            quantity=counter,
            singular="joint had its",
            plural="joints had their",
            conclusion="display reset.",
            zero_overwrite_message="No joints found in this scene.",
        )
        feedback.print_inview_message(system_write=False)
        feedback.conclusion = '"radius", "drawStyle" and "visibility" attributes reset.'
        sys.stdout.write(f"\n{feedback.get_string_message()}")
    # Print errors
    if errors and verbose:
        print(("#" * 50) + "\n")
        print(errors)
        print("#" * 50)
        cmds.warning("A few joints were not fully reset. Open script editor for more details.")
    return counter


def delete_display_layers(layer_list=None, verbose=True):
    """
    Deletes provided (or all) display layers

    Args:
        layer_list (list, str): A list with the name of the layers it should affect. (Strings are converted into list)
        verbose (bool, optional): If True, it will return feedback about the operation.
    Returns:
        int: Number of affected joints.
    """
    function_name = "Delete All Display Layers"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        _layers = None
        if layer_list and isinstance(layer_list, list):
            _layers = layer_list
        if layer_list and isinstance(layer_list, str):
            _layers = [layer_list]
        if not _layers:
            _layers = cmds.ls(type="displayLayer", long=True) or []
        for layer in _layers:
            if layer != "defaultLayer":
                cmds.delete(layer)
                deleted_counter += 1
        if verbose:
            feedback = FeedbackMessage(
                quantity=deleted_counter,
                singular="layer was",
                plural="layers were",
                conclusion="deleted.",
                zero_overwrite_message="No display layers found in this scene.",
            )
            feedback.print_inview_message()

    except Exception as e:
        message = f"Error while deleting display layers: {str(e)}"
        if verbose:
            cmds.warning(message)
        else:
            logger.debug(message)
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    return deleted_counter


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    set_lra_state(cmds.ls(typ="joint"), True)
