"""
Auto Rigger Spine Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_or_create_joint_automation_group, get_driven_joint
from gt.tools.auto_rigger.rig_utils import duplicate_joint_for_automation, rescale_joint_radius
from gt.tools.auto_rigger.rig_utils import find_proxy_node_from_uuid, find_direction_curve_node
from gt.tools.auto_rigger.rig_utils import find_joint_node_from_uuid
from gt.utils.color_utils import ColorConstants, set_color_viewport, set_color_outliner
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.constraint_utils import equidistant_constraints
from gt.tools.auto_rigger.rig_utils import get_proxy_offset
from gt.utils.math_utils import dist_center_to_center
from gt.utils.transform_utils import Vector3
from gt.utils import hierarchy_utils
from gt.ui import resource_library
import maya.cmds as cmds
import logging
import re


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleSpine(ModuleGeneric):
    __version__ = '0.0.1-alpha'
    icon = resource_library.Icon.rigger_module_spine
    allow_parenting = True

    def __init__(self, name="Spine", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Hip (Base)
        self.hip = Proxy(name="hip")
        pos_hip = Vector3(y=84.5)
        self.hip.set_initial_position(xyz=pos_hip)
        self.hip.set_locator_scale(scale=1.5)
        self.hip.set_meta_type(value="hip")

        # Chest (End)
        self.chest = Proxy(name="chest")
        pos_chest = Vector3(y=114.5)
        self.chest.set_initial_position(xyz=pos_chest)
        self.chest.set_locator_scale(scale=1.5)
        self.chest.set_meta_type(value="chest")

        # Spines (In-between)
        self.spines = []
        self.set_spine_num(spine_num=3)

    def set_spine_num(self, spine_num):
        """
        Set a new number of spine proxies. These are the proxies in-between the hip proxy (base) and chest proxy (end)
        Args:
            spine_num (int): New number of spines to exist in-between hip and chest.
                             Minimum is zero (0) - No negative numbers.
        """
        spines_len = len(self.spines)
        # Same as current, skip
        if spines_len == spine_num:
            return
        # New number higher than current - Add more proxies (spines)
        if spines_len < spine_num:
            # Determine Initial Parent (Last spine, or hip)
            if self.spines:
                _parent_uuid = self.spines[-1].get_uuid()
            else:
                _parent_uuid = self.hip.get_uuid()
            # Create new spines
            for num in range(spines_len, spine_num):
                new_spine = Proxy(name=f'spine{str(num + 1).zfill(2)}')
                new_spine.set_locator_scale(scale=1)
                new_spine.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
                new_spine.set_meta_type(value=f'spine{str(num + 1).zfill(2)}')
                new_spine.add_meta_parent(line_parent=_parent_uuid)
                new_spine.set_parent_uuid(uuid=_parent_uuid)
                _parent_uuid = new_spine.get_uuid()
                self.spines.append(new_spine)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.spines) > spine_num:
            self.spines = self.spines[:spine_num]  # Truncate the list

        if self.spines:
            self.chest.add_meta_parent(line_parent=self.spines[-1].get_uuid())
        else:
            self.chest.add_meta_parent(line_parent=self.hip.get_uuid())

        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.hip]
        self.proxies.extend(self.spines)
        self.proxies.append(self.chest)

    def get_module_as_dict(self, **kwargs):
        """
        Overwrite to remove offset data from the export
        Args:
            kwargs: Key arguments, not used for anything
        """
        return super().get_module_as_dict(include_offset_data=False)

    def read_proxies_from_dict(self, proxy_dict):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            proxy_dict (dict): A proxy description dictionary. It must match an expected pattern for this to work:
                               Acceptable pattern: {"uuid_str": {<description>}}
                               "uuid_str" being the actual uuid string value of the proxy.
                               "<description>" being the output of the operation "proxy.get_proxy_as_dict()".
        """
        if not proxy_dict or not isinstance(proxy_dict, dict):
            logger.debug(f'Unable to read proxies from dictionary. Input must be a dictionary.')
            return
        # Determine Number of Spine Proxies
        _spine_num = 0
        spine_pattern = r'spine\d+'
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_TYPE)
                if bool(re.match(spine_pattern, meta_type)):
                    _spine_num += 1
        self.set_spine_num(_spine_num)
        self.read_type_matching_proxy_from_dict(proxy_dict)
        self.refresh_proxies_list()

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        is_valid = super().is_valid()  # Passthrough
        return is_valid

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        if self.parent_uuid:
            if self.hip:
                self.hip.set_parent_uuid(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        hip = find_proxy_node_from_uuid(self.hip.get_uuid())
        chest = find_proxy_node_from_uuid(self.chest.get_uuid())

        spines = []
        for spine in self.spines:
            spine_node = find_proxy_node_from_uuid(spine.get_uuid())
            spines.append(spine_node)
        self.hip.apply_offset_transform()
        self.chest.apply_offset_transform()

        spine_offsets = []
        for spine in spines:
            offset = get_proxy_offset(spine)
            spine_offsets.append(offset)
        equidistant_constraints(start=hip, end=chest, target_list=spine_offsets)

        self.hip.apply_transforms()
        self.chest.apply_transforms()
        for spine in self.spines:
            spine.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton(self):
        super().build_skeleton()  # Passthrough

    def build_skeleton_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.chest.set_parent_uuid(uuid=self.chest.get_meta_parent_uuid())
        super().build_skeleton_post()  # Passthrough
        self.chest.clear_parent_uuid()

    def build_rig(self):
        # Get Elements
        direction_crv = find_direction_curve_node()
        module_parent_jnt = find_joint_node_from_uuid(self.get_parent_uuid())  # TODO TEMP @@@
        hip_jnt = find_joint_node_from_uuid(self.hip.get_uuid())
        chest_jnt = find_joint_node_from_uuid(self.chest.get_uuid())
        middle_jnt_list = []
        for proxy in self.spines:
            mid_jnt = find_joint_node_from_uuid(proxy.get_uuid())
            if mid_jnt:
                middle_jnt_list.append(mid_jnt)

        module_jnt_list = [hip_jnt]
        module_jnt_list.extend(middle_jnt_list)
        module_jnt_list.append(chest_jnt)

        # Set Colors
        set_color_viewport(obj_list=module_jnt_list, rgb_color=ColorConstants.RigJoint.GENERAL)

        # Get Scale
        spine_scale = dist_center_to_center(hip_jnt, chest_jnt)

        joint_automation_grp = find_or_create_joint_automation_group()
        module_parent_jnt = get_driven_joint(self.get_parent_uuid())
        hierarchy_utils.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
        hip_parent = module_parent_jnt
        if module_parent_jnt:
            set_color_viewport(obj_list=hip_parent, rgb_color=ColorConstants.RigJoint.AUTOMATION)
            rescale_joint_radius(joint_list=hip_parent, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN)
        else:
            hip_parent = joint_automation_grp

        hip_fk = duplicate_joint_for_automation(hip_jnt, suffix="fk", parent=hip_parent)
        fk_joints = [hip_fk]
        last_mid_parent = hip_fk
        mid_fk_list = []
        for mid in middle_jnt_list:
            mid_fk = duplicate_joint_for_automation(mid, suffix="fk", parent=last_mid_parent)
            mid_fk_list.append(mid_fk)
            last_mid_parent = mid_fk
        fk_joints.extend(mid_fk_list)
        chest_fk = duplicate_joint_for_automation(chest_jnt, suffix="fk", parent=last_mid_parent)
        fk_joints.append(chest_fk)

        rescale_joint_radius(joint_list=fk_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_FK)
        set_color_viewport(obj_list=fk_joints, rgb_color=ColorConstants.RigJoint.FK)
        set_color_outliner(obj_list=fk_joints, rgb_color=ColorConstants.RigOutliner.FK)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    a_spine = ModuleSpine()
    a_spine.set_spine_num(0)
    a_spine.set_spine_num(6)
    a_project = RigProject()
    a_project.add_to_modules(a_spine)
    a_project.build_proxy()

    cmds.setAttr(f'hip.tx', 10)
    cmds.setAttr(f'spine02.tx', 10)

    a_project.read_data_from_scene()
    dictionary = a_project.get_project_as_dict()

    cmds.file(new=True, force=True)
    a_project2 = RigProject()
    a_project2.read_data_from_dict(dictionary)
    a_project2.build_proxy()
    a_project2.build_rig()

    # Show all
    cmds.viewFit(all=True)
