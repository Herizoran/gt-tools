"""
Auto Rigger Project Template for Biped Rigs
"""

import gt.tools.auto_rigger.module_biped_arm as module_biped_arm
import gt.tools.auto_rigger.module_biped_leg as module_biped_leg
import gt.tools.auto_rigger.module_biped_finger as module_biped_finger
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.module_spine as module_spine
import gt.tools.auto_rigger.module_root as module_root
import gt.tools.auto_rigger.module_head as module_head
import gt.tools.auto_rigger.module_attr_hub as module_attr_hub
import gt.tools.auto_rigger.module_utils as module_utils
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_template_biped():
    """
    Creates a template project for a biped rig
    Returns:
        RigProject: A rig project containing modules used in a biped rig
    """
    biped_project = tools_rig_frm.RigProject(name="Template Biped")

    # CreateModules
    new_scene = module_utils.ModuleNewScene()
    root = module_root.ModuleRoot()
    spine = module_spine.ModuleSpine()
    leg_lf = module_biped_leg.ModuleBipedLegLeft()
    leg_rt = module_biped_leg.ModuleBipedLegRight()
    arm_lf = module_biped_arm.ModuleBipedArmLeft()
    arm_rt = module_biped_arm.ModuleBipedArmRight()
    fingers_lf = module_biped_finger.ModuleBipedFingersLeft()
    fingers_rt = module_biped_finger.ModuleBipedFingersRight()
    head = module_head.ModuleHead()
    attr_hub = module_attr_hub.ModuleAttributeHub(name="Visibility Control")

    # Initial Preferences
    attr_hub.attr_switcher_proxy.set_initial_position(y=180)
    attr_hub.attr_switcher_proxy.set_name(name="visibility")

    # Parenting
    spine_hip_uuid = spine.hip_proxy.get_uuid()
    leg_lf.set_parent_uuid(spine_hip_uuid)
    leg_rt.set_parent_uuid(spine_hip_uuid)
    root_uuid = root.root_proxy.get_uuid()
    spine.set_parent_uuid(root_uuid)
    spine_chest_uuid = spine.chest_proxy.get_uuid()
    head.set_parent_uuid(spine_chest_uuid)
    arm_lf.set_parent_uuid(spine_chest_uuid)
    arm_rt.set_parent_uuid(spine_chest_uuid)
    wrist_lf_uuid = arm_lf.hand_proxy.get_uuid()
    fingers_lf.set_parent_uuid(wrist_lf_uuid)
    wrist_rt_uuid = arm_rt.hand_proxy.get_uuid()
    fingers_rt.set_parent_uuid(wrist_rt_uuid)

    # Add Modules
    biped_project.add_to_modules(new_scene)
    biped_project.add_to_modules(root)
    biped_project.add_to_modules(spine)
    biped_project.add_to_modules(head)
    biped_project.add_to_modules(arm_lf)
    biped_project.add_to_modules(arm_rt)
    biped_project.add_to_modules(leg_lf)
    biped_project.add_to_modules(leg_rt)
    biped_project.add_to_modules(fingers_lf)
    biped_project.add_to_modules(fingers_rt)
    biped_project.add_to_modules(attr_hub)

    return biped_project


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)

    a_biped_project = create_template_biped()
    # a_biped_project.set_preference_value_using_key(key="build_control_rig", value=False)
    # a_biped_project.set_preference_value_using_key(key="delete_proxy_after_build", value=False)
    a_biped_project.build_proxy()
    a_biped_project.build_rig()  # Comment out if running lines below

    # # Modify Proxy --------------------------------------------------------------------------------------------
    # cmds.setAttr(f"C_hips.tz", -2)
    # cmds.setAttr(f"C_spine03.tz", -2)
    # cmds.setAttr(f"L_upperArm.tz", -6)
    # cmds.setAttr(f"R_upperArm.tz", -6)
    # cmds.setAttr(f"L_hand.ty", -20)
    # cmds.setAttr(f"R_hand.ty", -20)

    # # Get Rebuild Data
    # a_biped_project.read_data_from_scene()
    # a_biped_project_as_dict = a_biped_project.get_project_as_dict()
    # a_biped_project.build_rig()

    # # Re-build -----------------------------------------------------------------------------------------------
    # cmds.file(new=True, force=True)
    # a_project2 = tools_rig_frm.RigProject()
    # a_project2.read_data_from_dict(a_biped_project_as_dict)
    # a_project2.build_proxy()
    # a_project2.build_rig()
    # import pprint
    # pprint.pprint(a_biped_project_as_dict)

    # Frame all
    cmds.viewFit(all=True)
