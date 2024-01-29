"""
Surface Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.curve_utils import get_curve, get_positions_from_curve, rescale_curve
from gt.utils.iterable_utils import sanitize_maya_list, filter_list_by_type
from gt.utils.attr_utils import hide_lock_default_attrs, set_trs_attr
from gt.utils.color_utils import set_color_viewport, ColorConstants
from gt.utils.transform_utils import match_transform
from gt.utils.math_utils import get_bbox_position
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SURFACE_TYPE = "nurbsSurface"


def is_surface_periodic(surface_shape):
    """
    Determine if a surface is periodic.
    Args:
        surface_shape (str): The name of the surface shape (or its transform).

    Returns:
        bool: True if the surface is periodic, False otherwise.
    """
    form_u = cmds.getAttr(f"{surface_shape}.formU")
    form_v = cmds.getAttr(f'{surface_shape}.formV')
    if form_u == 2 or form_v == 2:
        return True
    return False


def create_surface_from_object_list(obj_list, surface_name=None):
    """
    Creates a surface from a list of objects (according to list order)
    The surface is created using curve offsets.
        1. A curve is created using the position of the objects from the list.
        2. Two offset curves are created from the initial curve.
        3. A loft surface is created out of the two offset curves.
    Args:
        obj_list (list): List of objects used to generate the surface (order matters)
        surface_name (str, optional): Name of the generated surface.
    Returns:
        str or None: Generated surface (loft) object, otherwise None.
    """
    # Check if there are at least two objects in the list
    if len(obj_list) < 2:
        cmds.warning("At least two objects are required to create a surface.")
        return

    # Get positions of the objects
    positions = [cmds.xform(obj, query=True, translation=True, worldSpace=True) for obj in obj_list]

    # Create a curve with the given positions as control vertices (CVs)
    crv_mid = cmds.curve(d=1, p=positions, n=f'{surface_name}_curveFromList')
    crv_mid = Node(crv_mid)

    # Offset the duplicated curve positively
    offset_distance = 1
    crv_pos = cmds.offsetCurve(crv_mid, name=f'{crv_mid}PositiveOffset',
                               distance=offset_distance, constructionHistory=False)[0]
    crv_neg = cmds.offsetCurve(crv_mid, name=f'{crv_mid}NegativeOffset',
                               distance=-offset_distance, constructionHistory=False)[0]
    crv_pos = Node(crv_pos)
    crv_neg = Node(crv_neg)

    loft_parameters = {}
    if surface_name and isinstance(surface_name, str):
        loft_parameters["name"] = surface_name

    lofted_surface = cmds.loft(crv_pos, crv_neg,
                               range=True,
                               autoReverse=True,
                               degree=3,
                               uniform=True,
                               constructionHistory=False,
                               **loft_parameters)[0]
    cmds.delete([crv_mid, crv_pos, crv_neg])
    return lofted_surface


def multiply_surface_spans(input_surface, u_multiplier=0, v_multiplier=0, u_degree=1, v_degree=1):
    """
    Multiplies the number of spans in the U and V directions of a NURBS surface.

    Args:
        input_surface (str, Node): The name of the NURBS surface to be modified. (can be the shape or its transform)
        u_multiplier (int): Multiplier for the number of spans in the U direction. Default is 0.
        v_multiplier (int): Multiplier for the number of spans in the V direction. Default is 0.
        u_degree (int): Degree of the surface in the U direction. Default is 1.
        v_degree (int): Degree of the surface in the V direction. Default is 1.

    Returns:
        str or None: The name of the affected surface, otherwise None.

    Example:
        multiply_surface_spans("myNurbsSurface", u_multiplier=0, v_multiplier=3, u_degree=3, v_degree=3)
    """
    # Check existence
    if not input_surface or not cmds.objExists(input_surface):
        logger.debug(f'Unable to multiply surface division. Missing provided surface.')
        return
    # Check if the provided surface is a transform
    if cmds.objectType(input_surface) == 'transform':
        # If it's a transform, get the associated shape node
        shapes = cmds.listRelatives(input_surface, shapes=True, typ=SURFACE_TYPE)
        if shapes:
            input_surface = shapes[0]
        else:
            logger.debug(f'Unable to multiply surface division. '
                         f'No "nurbsSurface" found in the provided transform.')
            return

    # Get the number of spans in the U and V directions. 0 is ignored.
    num_spans_u = cmds.getAttr(f"{input_surface}.spansU")*u_multiplier
    num_spans_v = cmds.getAttr(f"{input_surface}.spansV")*v_multiplier

    # Prepare parameters and rebuild
    degree_params = {}
    if u_degree and isinstance(u_degree, int):
        degree_params["degreeU"] = u_degree
    if v_degree and isinstance(v_degree, int):
        degree_params["degreeV"] = v_degree
    surface = cmds.rebuildSurface(input_surface, spansU=num_spans_u, spansV=num_spans_v, **degree_params)
    if surface:
        return surface[0]


class Ribbon:
    def __init__(self,
                 prefix=None,
                 surface_data=None,
                 equidistant=True,
                 num_controls=5,
                 num_joints=20,
                 add_fk=False,
                 bind_joint_orient_offset=(90, 0, 0),
                 bind_joint_parenting=True
                 ):
        """
        Args:
            prefix (str): The system name to be added as a prefix to the created nodes.
                        If not provided, the name of the surface is used.
            surface_data (str, optional): The name of the surface to be used as a ribbon. (Can be its transform or shape)
                                     If not provided one will be created automatically.
            equidistant (int, optional): Determine if the controls should be equally spaced (True) or not (False).
            num_controls (int, optional): The number of controls to create.
            num_joints (int, optional): The number of joints to create on the ribbon.
            add_fk (int): Flag to add FK controls.
            bind_joint_orient_offset (tuple): An offset tuple with the X, Y, and Z rotation values.
            bind_joint_parenting (bool, optional): Define if bind joints will form a hierarchy (True) or not (False)
        """
        self.prefix = None
        self.equidistant = True
        self.num_controls = 5
        self.num_joints = 20
        self.fixed_radius = None
        self.add_fk = add_fk
        self.bind_joint_offset = None
        self.bind_joint_parenting = True

        # Surface Data
        self.surface_data = None
        self.surface_data_length = None  # When using a list of objects or positions, this is the length of the list.
        self.surface_spans_multiplier = 4

        if prefix:
            self.set_prefix(prefix=prefix)
        if surface_data:
            self.set_surface_data(surface_data=surface_data)
        if isinstance(equidistant, bool):
            self.set_equidistant(is_activated=equidistant)
        if num_controls:
            self.set_num_controls(num_controls=num_controls)
        if num_joints:
            self.set_num_joints(num_joints=num_joints)
        if bind_joint_orient_offset:
            self.set_bind_joint_orient_offset(offset_tuple=bind_joint_orient_offset)
        if isinstance(bind_joint_parenting, bool):
            self.set_bind_joint_hierarchy(state=bind_joint_parenting)

    def set_prefix(self, prefix):
        """
        Set the prefix attribute of the object.

        Args:
            prefix (str): The prefix to be added to the ribbon objects during the "build" process.
        """
        if not prefix or not isinstance(prefix, str):
            logger.debug('Unable to set prefix. Input must be a non-empty string.')
            return
        self.prefix = prefix

    def set_surface_data(self, surface_data):
        """
        Set the surface origin to be used as a ribbon of the object.
        Args:
            surface_data (str, list): Data used to create or connect ribbon surface.
                              If a string is provided, it should be the transform or shape of a nurbs surface.
                              If a list of objects or positions is used, a surface will be created using this data.
                              The function "clear_surface_data" can be used to remove previous provided data.
        """
        if not surface_data:
            logger.debug(f'Unable to set surface path. No data was provided.')
            return
        self.surface_data = surface_data

    def set_surface_span_multiplier(self, span_multiplier):
        """
        Sets the span multiplier value of the generated surface. That is, the number of divisions in between spans.
        For example, if a surface is created from point A to point B and the multiplier is set to zero or one,
        the surface will not change in any way, and be composed only of the starting and ending spans.
        Now if the multiplier is set to 2, the number of spans will double, essentially adding a span/edge in between
        the initial spans.
        This can be seen as a subdivision value for surfaces.
        Args:
            span_multiplier (int): New span multiplier value.
        """
        if not isinstance(span_multiplier, int):
            logger.debug(f'Unable to set span multiplier value. Input must be an integer.')
            return
        self.surface_spans_multiplier = span_multiplier

    def set_bind_joint_orient_offset(self, offset_tuple):
        """
        Sets an orientation offset (rotation) for the bind joints. Helpful for when matching orientation.
        Args:
            offset_tuple (tuple): An offset tuple with the X, Y, and Z rotation values.
        """
        if not isinstance(offset_tuple, tuple) or len(offset_tuple) < 3:
            logger.debug(f'Unable to set bind joint orient offset. '
                         f'Invalid input. Must be a tuple with X, Y and Z values.')
            return

        if not all(isinstance(num, (int, float)) for num in offset_tuple):
            logger.debug(f'Unable to set bind joint orient offset. '
                         f'Input must contain only numbers.')
            return

        self.bind_joint_offset = offset_tuple

    def set_bind_joint_hierarchy(self, state):
        """
        Sets Bind joint parenting (hierarchy)
        Args:
            state (bool, optional): Define if bind joints will form a hierarchy (True) or not (False)
        """
        if isinstance(state, bool):
            self.bind_joint_parenting = state

    def clear_surface_data(self):
        """
        Removes/Clears the currently set surface so a new one is automatically created during the "build" process.
        """
        self.surface_data = None

    def set_fixed_radius(self, radius):
        """
        Sets a fixed radius values
        Args:
            radius (int, float): A radius value to be set when creating bind joints.
                                 If not provided, one is calculated automatically.
        """
        if not radius or not isinstance(radius, (int, float)):
            logger.debug(f'Unable to set fixed radius. Input must be an integer or a float.')
            return
        self.fixed_radius = radius

    def clear_fixed_radius(self):
        """
        Removes/Clears the currently set fixed radius value.
        This causes the radius to be automatically calculated when building.
        """
        self.fixed_radius = None

    def set_equidistant(self, is_activated):
        """
        Set the equidistant attribute of the object.

        Args:
            is_activated (bool): Determine if the controls should be equally spaced (True) or not (False).
        """
        if not isinstance(is_activated, bool):
            logger.debug('Unable to set equidistant state. Input must be a bool (True or False)')
            return
        self.equidistant = is_activated

    def set_num_controls(self, num_controls):
        """
        Set the number of controls attribute of the object.

        Args:
            num_controls (int): The number of controls to create.
        """
        if not isinstance(num_controls, int) or num_controls <= 1:
            logger.debug('Unable to set number of controls. Input must be two or more.')
            return
        self.num_controls = num_controls

    def set_num_joints(self, num_joints):
        """
        Set the number of joints attribute of the object.
        Args:
            num_joints (int): The number of joints to be set.
        """
        if not isinstance(num_joints, int) or num_joints <= 0:
            logger.debug('Unable to set number of joints. Input must be a positive integer.')
            return
        self.num_joints = num_joints

    def _get_or_create_surface(self, prefix):
        """
        Gets or creates the surface used for the ribbon.
        The operation depends on the data stored in the "surface_data" variables.
        If empty, it will create a simple 1x24 surface to match the default size of the grid.
        If a path (string) is provided, it will use it as the surface, essentially using an existing surface.
        If a list of paths (strings) is provided, it will use the position of the objects to create a surface.
        If a list positions (3d tuples or lists) is provided, it will use the data to create a surface.

        This function will also update the "surface_data_length" according to the data found.
        No data = None.
        Path = None.
        List of paths = Length of the existing objects.
        List of positions = Length of the positions list.

        Args:
            prefix (str): Prefix to be added in front of the generated surface.
                          If an existing surface is found, this value is ignored.
        Returns:
            str: The surface name (path)
        """
        self.surface_data_length = None
        if isinstance(self.surface_data, str) and cmds.objExists(self.surface_data):
            return self.surface_data
        if isinstance(self.surface_data, (list, tuple)):
            # Object List
            _filter_obj_list = filter_list_by_type(self.surface_data, data_type=(str, Node))
            if _filter_obj_list:
                _obj_list = sanitize_maya_list(input_list=self.surface_data, sort_list=False,
                                               filter_unique=False, reverse_list=True)
                if not _obj_list or len(_obj_list) < 2:
                    logger.warning(f'Unable to create surface using object list. '
                                   f'At least two valid objects are necessary for this operation.')
                else:
                    self.surface_data_length = len(_obj_list)
                    _sur = create_surface_from_object_list(obj_list=_obj_list, surface_name=f"{prefix}_ribbon_sur")
                    multiply_surface_spans(input_surface=_sur, v_multiplier=self.surface_spans_multiplier, v_degree=3)
                    return _sur
            # Position List
            _filter_pos_list = filter_list_by_type(self.surface_data, data_type=(list, tuple), num_items=3)
            if _filter_pos_list:
                obj_list_locator = []
                for pos in self.surface_data:
                    locator_name = cmds.spaceLocator(name=f'{prefix}_temp_surface_assembly_locator')[0]
                    cmds.move(*pos, locator_name)
                    obj_list_locator.append(locator_name)
                obj_list_locator.reverse()
                self.surface_data_length = len(obj_list_locator)
                _sur = create_surface_from_object_list(obj_list=obj_list_locator,
                                                       surface_name=f"{prefix}_ribbon_sur")
                multiply_surface_spans(input_surface=_sur, v_multiplier=self.surface_spans_multiplier, v_degree=3)
                cmds.delete(obj_list_locator)
                return _sur

        surface = cmds.nurbsPlane(axis=(0, 1, 0), width=1, lengthRatio=24, degree=3,
                                  patchesU=1, patchesV=10, constructionHistory=False)[0]
        surface = cmds.rename(surface, f"{prefix}ribbon_sur")
        return surface

    def build(self):
        """
        Build a ribbon rig.
        """
        num_controls = self.num_controls
        num_joints = self.num_joints

        # Determine Prefix
        if not self.prefix:
            prefix = f''
        else:
            prefix = f'{self.prefix}_'

        # Create Surface in case not provided or missing
        input_surface = self._get_or_create_surface(prefix=prefix)
        input_surface = Node(input_surface)

        # Determine Surface Transform and Shape
        surface_shape = None
        if cmds.objectType(input_surface) == "transform":
            surface_shape = cmds.listRelatives(input_surface, shapes=True, fullPath=True)[0]
            surface_shape = Node(surface_shape)
        if cmds.objectType(input_surface) == SURFACE_TYPE:
            surface_shape = Node(input_surface)
            input_surface = cmds.listRelatives(surface_shape, parent=True, fullPath=True)[0]
            input_surface = Node(input_surface)
        cmds.delete(input_surface, constructionHistory=True)

        if not surface_shape:
            logger.warning(f'Unable to create ribbon. Failed to get or create surface.')
            return

        # Determine Direction ----------------------------------------------------------------------------
        u_curve = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)  # (.5 = center)
        v_curve = cmds.duplicateCurve(f'{input_surface}.u[.5]', local=True, ch=0)
        u_length = cmds.arclen(u_curve)
        v_length = cmds.arclen(v_curve)

        if u_length < v_length:
            cmds.reverseSurface(input_surface, direction=3, ch=False, replaceOriginal=True)
            cmds.reverseSurface(input_surface, direction=0, ch=False, replaceOriginal=True)

        u_curve_for_positions = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)[0]

        # U Positions
        is_periodic = is_surface_periodic(surface_shape=str(surface_shape))
        u_position_ctrls = get_positions_from_curve(curve=u_curve_for_positions, count=num_controls,
                                                    periodic=is_periodic, space="uv")
        u_position_joints = get_positions_from_curve(curve=u_curve_for_positions, count=num_joints,
                                                     periodic=is_periodic, space="uv")
        length = cmds.arclen(u_curve_for_positions)
        cmds.delete(u_curve, v_curve, u_curve_for_positions)

        # self.equidistant = False  # TODO TEMP @@@
        # # Determine positions when
        # if self.surface_data_length and self.equidistant is False:
        #     print(f'num_joints: {num_joints}')
        #     print(f'u_position_joints length: {len(u_position_joints)}')
        #     u_pos_value = 1/self.surface_data_length
        #     print(u_pos_value)
        #     print(u_position_joints)
        #
        # return
        # Organization ----------------------------------------------------------------------------------
        grp_suffix = NamingConstants.Suffix.GRP
        parent_group = cmds.group(name=f"{prefix}ribbon_{grp_suffix}", empty=True)
        parent_group = Node(parent_group)
        driver_joints_grp = cmds.group(name=f"{prefix}driver_joints_{grp_suffix}", empty=True)
        driver_joints_grp = Node(driver_joints_grp)
        control_grp = cmds.group(name=f"{prefix}controls_{grp_suffix}", empty=True)
        control_grp = Node(control_grp)
        follicles_grp = cmds.group(name=f"{prefix}follicles_{grp_suffix}", empty=True)
        follicles_grp = Node(follicles_grp)
        bind_grp = cmds.group(name=f"{prefix}bind_{grp_suffix}", empty=True)
        bind_grp = Node(bind_grp)
        setup_grp = cmds.group(name=f"{prefix}setup_{grp_suffix}", empty=True)
        setup_grp = Node(setup_grp)
        ribbon_crv = get_curve("_pin_pos_z")
        ribbon_crv.set_name(f"{prefix}base_{NamingConstants.Suffix.CTRL}")
        ribbon_ctrl = ribbon_crv.build()
        ribbon_ctrl = Node(ribbon_ctrl)
        rescale_curve(curve_transform=str(ribbon_ctrl), scale=length/10)
        ribbon_offset = cmds.group(name=f"{prefix}ctrl_main_offset", empty=True)
        ribbon_offset = Node(ribbon_offset)

        hierarchy_utils.parent(source_objects=ribbon_ctrl, target_parent=ribbon_offset)
        hierarchy_utils.parent(source_objects=control_grp, target_parent=ribbon_ctrl)
        hierarchy_utils.parent(source_objects=[ribbon_offset, bind_grp, setup_grp],
                               target_parent=parent_group)
        hierarchy_utils.parent(source_objects=[input_surface, driver_joints_grp, follicles_grp],
                               target_parent=setup_grp)
        # cmds.setAttr(f"{setup_grp}.visibility", 0)  # TODO TEMP @@@

        # Follicles -----------------------------------------------------------------------------------
        follicle_nodes = []
        follicle_transforms = []
        bind_joints = []
        if self.fixed_radius is None:
            bind_joint_radius = (length/60)/(float(num_joints)/40)
        else:
            bind_joint_radius = self.fixed_radius

        for index in range(num_joints):
            _follicle = Node(cmds.createNode("follicle"))
            _follicle_transform = Node(cmds.listRelatives(_follicle, p=True, fullPath=True)[0])
            _follicle_transform.rename(f"{prefix}follicle_{(index+1):02d}")

            follicle_transforms.append(_follicle_transform)
            follicle_nodes.append(_follicle)

            # Connect Follicle to Transforms
            cmds.connectAttr(f"{_follicle}.outTranslate", f"{_follicle_transform}.translate")
            cmds.connectAttr(f"{_follicle}.outRotate", f"{_follicle_transform}.rotate")

            # Attach Follicle to Surface
            cmds.connectAttr(f"{surface_shape}.worldMatrix[0]", f"{_follicle}.inputWorldMatrix")
            cmds.connectAttr(f"{surface_shape}.local", f"{_follicle}.inputSurface")

            cmds.setAttr(f'{_follicle}.parameterU', u_position_joints[index])
            cmds.setAttr(f'{_follicle}.parameterV', 0.5)

            cmds.parent(_follicle_transform, follicles_grp)

            # Bind Joint
            if prefix:
                joint_name = f"{prefix}{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            else:
                joint_name = f"bind_{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            joint = cmds.createNode("joint", name=joint_name)
            joint = Node(joint)
            bind_joints.append(joint)

            match_transform(source=_follicle_transform, target_list=joint)
            if self.bind_joint_offset:
                cmds.rotate(*self.bind_joint_offset, joint, relative=True, os=True)
            cmds.parentConstraint(_follicle_transform, joint, maintainOffset=True)
            cmds.setAttr(f"{joint}.radius", bind_joint_radius)

        if follicle_transforms:
            match_transform(source=follicle_transforms[0], target_list=ribbon_offset)
        else:
            bbox_center = get_bbox_position(input_surface)
            set_trs_attr(target_obj=ribbon_offset, value_tuple=bbox_center, translate=True)
        hierarchy_utils.parent(source_objects=bind_joints, target_parent=bind_grp)

        # Ribbon Controls -----------------------------------------------------------------------------------
        ctrl_ref_follicle_nodes = []
        ctrl_ref_follicle_transforms = []

        for index in range(num_controls):
            _follicle = Node(cmds.createNode("follicle"))
            _follicle_transform = cmds.listRelatives(_follicle, parent=True)[0]
            ctrl_ref_follicle_nodes.append(_follicle)
            ctrl_ref_follicle_transforms.append(_follicle_transform)

            cmds.connectAttr(f"{_follicle}.outTranslate", f"{_follicle_transform}.translate")
            cmds.connectAttr(f"{_follicle}.outRotate", f"{_follicle_transform}.rotate")
            cmds.connectAttr(f"{surface_shape}.worldMatrix[0]", f"{_follicle}.inputWorldMatrix")
            cmds.connectAttr(f"{surface_shape}.local", f"{_follicle}.inputSurface")

        divider_for_ctrls = num_controls
        if not is_periodic:
            divider_for_ctrls = num_controls-1
        if self.equidistant:
            for index, _follicle_transform in enumerate(ctrl_ref_follicle_nodes):
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_position_ctrls[index])
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
        else:
            u_pos = 0
            for _follicle_transform in ctrl_ref_follicle_nodes:
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_pos)
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
                u_pos = u_pos + (1.0 / divider_for_ctrls)

        ik_ctrl_scale = (length / 35) / (float(num_controls) / 5)  # TODO TEMP @@@
        ribbon_ctrls = []

        ctrl_offset_grps = []
        ctrl_joints = []
        ctrl_jnt_offset_grps = []
        ctrl_jnt_radius = bind_joint_radius * 2

        for index in range(num_controls):
            crv = get_curve("_cube")
            ctrl = Node(crv.build())
            ctrl.rename(f"{prefix}{NamingConstants.Suffix.CTRL}_{(index+1):02d}")
            scale = ((length/3)/num_controls, 1, 1)

            rescale_curve(curve_transform=ctrl, scale=scale)

            ribbon_ctrls.append(ctrl)

            ctrl_offset_grp = cmds.group(name=f"{ctrl.get_short_name()}_offset", empty=True)
            ctrl_offset_grp = Node(ctrl_offset_grp)
            hierarchy_utils.parent(source_objects=ctrl, target_parent=ctrl_offset_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_offset_grp)
            ctrl_offset_grps.append(ctrl_offset_grp)

            # Ribbon Driver Joint
            joint = cmds.createNode("joint", name=f'{prefix}driver_{(index+1):02d}_{NamingConstants.Suffix.JNT}')
            joint = Node(joint)
            ctrl_joints.append(joint)
            cmds.setAttr(f"{ctrl_joints[index]}.radius", ctrl_jnt_radius)
            ctrl_jnt_ofs_grp = cmds.group(name=f"{joint}_offset", empty=True)
            ctrl_jnt_ofs_grp = Node(ctrl_jnt_ofs_grp)
            hierarchy_utils.parent(source_objects=joint, target_parent=ctrl_jnt_ofs_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_jnt_ofs_grp)
            ctrl_jnt_offset_grps.append(ctrl_jnt_ofs_grp)

        hierarchy_utils.parent(source_objects=ctrl_offset_grps, target_parent=control_grp)
        hierarchy_utils.parent(source_objects=ctrl_jnt_offset_grps, target_parent=driver_joints_grp)

        hide_lock_default_attrs(obj_list=ctrl_offset_grps + ctrl_jnt_offset_grps,
                                translate=True, rotate=True, scale=True, visibility=False)

        cmds.delete(ctrl_ref_follicle_transforms)

        for (control, joint) in zip(ribbon_ctrls, ctrl_joints):
            cmds.parentConstraint(control, joint)
            cmds.scaleConstraint(control, joint)

        # Follicle Scale
        for fol in follicle_transforms:
            cmds.scaleConstraint(ribbon_ctrl, fol)

        # Bind the surface to driver joints
        nurbs_skin_cluster = cmds.skinCluster(ctrl_joints, input_surface,
                                              dropoffRate=2,
                                              maximumInfluences=num_controls-1,
                                              nurbsSamples=num_controls*5,
                                              bindMethod=0,  # Closest Distance
                                              name=f"{prefix}skinCluster")[0]
        cmds.skinPercent(nurbs_skin_cluster, input_surface, pruneWeights=0.2)

        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sy")
        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_ctrl}.sx")

        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sy")
        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_offset}.sx")

        # FK Controls ---------------------------------------------------------------------------------------
        fk_ctrls = []
        if self.add_fk and is_periodic:
            logger.warning(f'Unable to add FK controls. Input surface is periodic.')
        elif self.add_fk and not is_periodic:
            fk_offset_groups = []
            crv_obj = get_curve("_circle_pos_x")
            for index in range(1, num_controls):
                _ctrl = Node(crv_obj.build())
                _ctrl.rename(f'{prefix}fk_{index:02d}_ctrl')
                _offset = Node(cmds.group(name=f'{prefix}fk_{index:02d}_offset', empty=True))
                fk_ctrls.append(_ctrl)
                fk_offset_groups.append(_offset)
                cmds.parent(_ctrl, _offset)

            for (offset, ctrl) in zip(fk_offset_groups[1:], fk_ctrls[:-1]):
                cmds.parent(offset, ctrl)

            cmds.parent(fk_offset_groups[0], control_grp)

            # Re-scale FK controls
            fk_ctrl_scale = ik_ctrl_scale*2
            for fk_ctrl in fk_ctrls:
                rescale_curve(curve_transform=fk_ctrl, scale=fk_ctrl_scale)

            ik_ctrl_offset_grps = [cmds.group(ctrl,
                                              name=f"{ctrl.get_short_name()}_offset_grp") for ctrl in ribbon_ctrls]
            [cmds.xform(ik_ctrl_offset_grp, piv=(0, 0, 0), os=True) for ik_ctrl_offset_grp in ik_ctrl_offset_grps]

            for ik, fk in zip(ribbon_ctrls[:-1], fk_offset_groups):
                cmds.delete(cmds.parentConstraint(ik, fk))

            for fk, ik in zip(fk_ctrls, ik_ctrl_offset_grps[:-1]):
                cmds.parentConstraint(fk, ik)

            # Constrain Last Ctrl
            cmds.parentConstraint(fk_ctrls[-1], ik_ctrl_offset_grps[-1], mo=True)

            set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RigControl.TWEAK)
            hide_lock_default_attrs(fk_offset_groups, translate=True, rotate=True, scale=True)

            cmds.select(cl=True)

        # Parenting Binding Joints
        if self.bind_joint_parenting:
            for index in range(len(bind_joints) - 1):
                parent_joint = bind_joints[index]
                child_joint = bind_joints[index + 1]
                if cmds.objExists(parent_joint) and cmds.objExists(child_joint):
                    cmds.parent(child_joint, parent_joint)

        # Colors  ----------------------------------------------------------------------------------------
        set_color_viewport(obj_list=ribbon_ctrl, rgb_color=ColorConstants.RGB.WHITE)
        set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RGB.RED_INDIAN)
        set_color_viewport(obj_list=ribbon_ctrls, rgb_color=ColorConstants.RGB.BLUE_SKY)
        set_color_viewport(obj_list=bind_joints, rgb_color=ColorConstants.RGB.YELLOW)

        # Clear selection
        cmds.select(cl=True)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Clear Scene
    cmds.file(new=True, force=True)
    # Create Test Joints
    test_joints = [cmds.joint(p=(0, 0, 0)),
                   cmds.joint(p=(-5, 0, 0)),
                   cmds.joint(p=(-10, 2, 0)),
                   cmds.joint(p=(-15, 6, 3)),
                   cmds.joint(p=(-20, 10, 5)),
                   cmds.joint(p=(-25, 15, 10)),
                   cmds.joint(p=(-30, 15, 15))]
    # Create Ribbon
    ribbon_factory = Ribbon(equidistant=True,
                            num_controls=5,
                            num_joints=8,
                            add_fk=True)
    ribbon_factory.set_surface_data("mocked_sur")
    ribbon_factory.set_prefix("mocked")
    ribbon_factory.set_surface_data(test_joints)
    ribbon_factory.set_surface_span_multiplier(4)
    # ribbon_factory.set_surface_data([(0, 0, 0), (5, 0, 0), (10, 0, 0)])
    # print(ribbon_factory._get_or_create_surface(prefix="test"))
    ribbon_factory.build()
    # create_surface_from_object_list(test_joints)
    cmds.viewFit(all=True)
