"""
Auto Rigger Base Framework
github.com/TrevisanGMW/gt-tools

RigProject > Module > Proxy > Joint/Control
"""
from gt.tools.auto_rigger.rig_utils import create_control_root_curve, find_proxy_node_from_uuid, find_proxy_from_uuid
from gt.tools.auto_rigger.rig_utils import parent_proxies, create_proxy_root_curve, create_proxy_visualization_lines
from gt.tools.auto_rigger.rig_utils import find_joint_node_from_uuid, get_proxy_offset, RiggerConstants
from gt.utils.uuid_utils import add_uuid_attr, is_uuid_valid, is_short_uuid_valid, generate_uuid
from gt.utils.curve_utils import Curve, get_curve, add_shape_scale_cluster
from gt.utils.attr_utils import add_separator_attr, set_attr, add_attr
from gt.utils.naming_utils import NamingConstants, get_long_name
from gt.utils.transform_utils import Transform, match_translate
from gt.utils.uuid_utils import get_object_from_uuid_attr
from gt.utils.control_utils import add_snapping_shape
from gt.utils.color_utils import add_side_color_setup
from gt.utils.string_utils import remove_prefix
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
from gt.ui import resource_library
from dataclasses import dataclass
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@dataclass
class ProxyData:
    """
    A proxy data class used as the proxy response for when the proxy is built.
    """
    name: str  # Long name of the generated proxy (full Maya path)
    offset: str  # Name of the proxy offset (parent of the proxy)
    setup: tuple  # Name of the proxy setup items (rig setup items)
    uuid: str  # Proxy UUID (Unique string pointing to generated proxy) - Not Maya UUID

    def __repr__(self):
        """
        String conversion returns the name of the proxy
        Returns:
            str: Proxy long name.
        """
        return self.name

    def get_short_name(self):
        """
        Gets the short version of the proxy name (default name is its long name)
        Note, this name might not be unique
        Returns:
            str: Short name of the proxy (short version of self.name) - Last name after "|" characters
        """
        from gt.utils.naming_utils import get_short_name
        return get_short_name(self.name)

    def get_long_name(self):
        """
        Gets the long version of the proxy name.
        Returns:
            str: Long name of the proxy. (a.k.a. Full Path)
        """
        return self.name

    def get_offset(self):
        """
        Gets the long version of the offset proxy group.
        Returns:
            str: Long name of the proxy group. (a.k.a. Full Path)
        """
        return self.offset

    def get_setup(self):
        """
        Gets the setup items tuple from the proxy data. This is a list of objects used to set up the proxy. (rig setup)
        Returns:
            tuple: A tuple with strings (full paths to the rig elements)
        """
        return self.setup

    def get_uuid(self):
        """
        Gets the proxy UUID
        Returns:
            str: Proxy UUID string
        """
        return self.uuid


class Proxy:
    def __init__(self,
                 name=None,
                 transform=None,
                 offset_transform=None,
                 curve=None,
                 uuid=None,
                 parent_uuid=None,
                 locator_scale=None,
                 attr_dict=None,
                 metadata=None):

        # Default Values
        self.name = "proxy"
        self.transform = None
        self.offset_transform = None
        self.curve = get_curve('_proxy_joint')
        self.curve.set_name(name=self.name)
        self.uuid = generate_uuid(remove_dashes=True)
        self.parent_uuid = None
        self.locator_scale = 1  # 100% - Initial curve scale
        self.attr_dict = {}
        self.metadata = None

        if name:
            self.set_name(name)
        if transform:
            self.set_transform(transform)
        if offset_transform:
            self.set_offset_transform(offset_transform)
        if curve:
            self.set_curve(curve)
        if uuid:
            self.set_uuid(uuid)
        if parent_uuid:
            self.set_parent_uuid(parent_uuid)
        if locator_scale:
            self.set_locator_scale(locator_scale)
        if attr_dict:
            self.set_attr_dict(attr_dict=attr_dict)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    def is_valid(self):
        """
        Checks if the current proxy element is valid
        """
        if not self.name:
            logger.warning('Invalid proxy object. Missing name.')
            return False
        if not self.curve:
            logger.warning('Invalid proxy object. Missing curve.')
            return False
        return True

    def build(self, prefix=None, apply_transforms=False):
        """
        Builds a proxy object.
        Args:
            prefix (str, optional): If provided, this prefix will be added to the proxy when it's created.
            apply_transforms (bool, optional): If True, the creation of the proxy will apply transform values.
                                               Used by modules to only apply transforms after setup. (post script)
        Returns:
            ProxyData: Name of the proxy that was generated/built.
        """
        if not self.is_valid():
            logger.warning(f'Unable to build proxy. Invalid proxy object.')
            return

        name = self.name
        if prefix and isinstance(prefix, str):
            name = f'{prefix}_{name}'
            self.curve.set_name(name)
        proxy_offset = cmds.group(name=f'{name}_{NamingConstants.Suffix.OFFSET}', world=True, empty=True)
        proxy_crv = self.curve.build()
        if prefix:
            self.curve.set_name(self.name)  # Restore name without prefix
        proxy_crv = cmds.parent(proxy_crv, proxy_offset)[0]
        proxy_offset = get_long_name(proxy_offset)
        proxy_crv = get_long_name(proxy_crv)
        add_snapping_shape(proxy_crv)
        add_separator_attr(target_object=proxy_crv, attr_name=f'proxy{RiggerConstants.SEPARATOR_STD_SUFFIX}')
        uuid_attrs = add_uuid_attr(obj_list=proxy_crv,
                                   attr_name=RiggerConstants.PROXY_ATTR_UUID,
                                   set_initial_uuid_value=False)
        scale_attr = add_attr(target_list=proxy_crv, attributes=RiggerConstants.PROXY_ATTR_SCALE, default=1) or []
        loc_scale_cluster = None
        if scale_attr and len(scale_attr) == 1:
            scale_attr = scale_attr[0]
            loc_scale_cluster = add_shape_scale_cluster(proxy_crv, scale_driver_attr=scale_attr)
        for attr in uuid_attrs:
            set_attr(attribute_path=attr, value=self.uuid)
        # Set Transforms
        if self.offset_transform and apply_transforms:
            self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if self.transform and apply_transforms:
            self.transform.apply_transform(target_object=proxy_crv, world_space=True)
        # Set Locator Scale
        if self.locator_scale and scale_attr:
            cmds.refresh()  # Without refresh, it fails to show the correct scale
            set_attr(scale_attr, self.locator_scale)

        return ProxyData(name=proxy_crv, offset=proxy_offset, setup=(loc_scale_cluster,), uuid=self.get_uuid())

    def apply_offset_transform(self):
        """
        Attempts to apply transform values to the offset of the proxy.
        To be used only after proxy is built.
        """
        proxy_crv = find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv:
            proxy_offset = get_proxy_offset(proxy_crv)
            if proxy_offset and self.offset_transform:
                self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)

    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        proxy_crv = find_proxy_from_uuid(uuid_string=self.uuid)
        if proxy_crv and apply_offset:
            proxy_offset = get_proxy_offset(proxy_crv)
            if proxy_offset and self.offset_transform:
                self.offset_transform.apply_transform(target_object=proxy_offset, world_space=True)
        if proxy_crv and self.transform:
            self.transform.apply_transform(target_object=proxy_crv, world_space=True)

    def apply_attr_dict(self, target_obj=None):
        """
        Attempts to apply (set) attributes found under the attribute dictionary of this proxy
        Args:
            target_obj (str, optional): Affected object, this is the object to get its attributes updated.
                                        If not provided it will attempt to retrieve the proxy using its UUID
        """
        if not target_obj:
            target_obj = find_proxy_from_uuid(self.get_uuid())
        if not target_obj or not cmds.objExists(target_obj):
            logger.debug(f"Unable to apply proxy attributes. Failed to find target object.")
            return
        if self.attr_dict:
            for attr, value in self.attr_dict.items():
                set_attr(obj_list=str(target_obj), attr_list=str(attr), value=value)

    def _initialize_transform(self):
        """
        In case a transform is necessary and none is present,
        a default Transform object is created and stored in "self.transform".
        """
        if not self.transform:
            self.transform = Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

    def _initialize_offset_transform(self):
        """
        In case an offset transform is necessary and none is present,
        a default Transform object is created and stored in "self.offset_transform".
        """
        if not self.offset_transform:
            self.offset_transform = Transform()  # Default is T:(0,0,0) R:(0,0,0) and S:(1,1,1)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new proxy name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set new name. Expected string but got "{str(type(name))}"')
            return
        self.curve.set_name(name)
        self.name = name

    def set_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.transform = transform

    def set_initial_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position and the offset position as the same value causing it to be zeroed. (Initial position)
        Useful to determine where the proxy should initially appear and be able to go back to when zeroed.
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self.set_position(x=x, y=y, z=z, xyz=xyz)
        self.set_offset_position(x=x, y=y, z=z, xyz=xyz)

    def set_initial_transform(self, transform):
        """
        Sets the transform and the offset transform as the same value causing it to be zeroed. (Initial position)
        Useful to determine where the proxy should initially appear and be able to go back to when zeroed.
        Args:
            transform (Transform): A transform  describing position, rotation and scale. (Applied to offset and proxy)
        """
        self.set_transform(transform)
        self.set_offset_transform(transform)

    def set_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_transform()
        self.transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_offset_transform(self, transform):
        """
        Sets the transform for this proxy element
        Args:
            transform (Transform): A transform object describing position, rotation and scale.
        """
        if not transform or not isinstance(transform, Transform):
            logger.warning(f'Unable to set proxy transform. '
                           f'Must be a "Transform" object, but got "{str(type(transform))}".')
            return
        self.offset_transform = transform

    def set_offset_position(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the position of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the position. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the position. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the position. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_position(x=x, y=y, z=z, xyz=xyz)

    def set_offset_rotation(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the rotation of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the rotation. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the rotation. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the rotation. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_rotation(x=x, y=y, z=z, xyz=xyz)

    def set_offset_scale(self, x=None, y=None, z=None, xyz=None):
        """
        Sets the scale of the proxy element (introduce values to its curve)
        Args:
            x (float, int, optional): X value for the scale. If provided, you must provide Y and Z too.
            y (float, int, optional): Y value for the scale. If provided, you must provide X and Z too.
            z (float, int, optional): Z value for the scale. If provided, you must provide X and Y too.
            xyz (Vector3, list, tuple) A Vector3 with the new position or a tuple/list with X, Y and Z values.
        """
        self._initialize_offset_transform()
        self.offset_transform.set_scale(x=x, y=y, z=z, xyz=xyz)

    def set_curve(self, curve, inherit_curve_name=False):
        """
        Sets the curve used to build the proxy element
        Args:
            curve (Curve) A Curve object to be used for building the proxy element (its shape)
            inherit_curve_name (bool, optional): If active, this function try to extract the name of the curve and
                                                 change the name of the proxy to match it. Does nothing if name is None.
        """
        if not curve or not isinstance(curve, Curve):
            logger.debug(f'Unable to set proxy curve. Invalid input. Must be a valid Curve object.')
            return
        if not curve.is_curve_valid():
            logger.debug(f'Unable to set proxy curve. Curve object failed validation.')
            return
        if inherit_curve_name:
            self.set_name(curve.get_name())
        else:
            curve.set_name(name=self.name)
        self.curve = curve

    def set_locator_scale(self, scale):
        if not isinstance(scale, (float, int)):
            logger.debug(f'Unable to set locator scale. Invalid input.')
        self.locator_scale = scale

    def set_attr_dict(self, attr_dict):
        """
        Sets the attributes dictionary for this proxy. Attributes are any key/value pairs further describing the proxy.
        Args:
            attr_dict (dict): An attribute dictionary where the key is the attribute and value is the attribute value.
                              e.g. {"locatorScale": 1, "isVisible": True}
        """
        if not isinstance(attr_dict, dict):
            logger.warning(f'Unable to set attribute dictionary. '
                           f'Expected a dictionary, but got: "{str(type(attr_dict))}"')
            return
        self.attr_dict = attr_dict

    def add_to_attr_dict(self, attr, value):
        """
        Adds a new item to the attribute dictionary.
        If an element with the same key already exists in the attribute dictionary, it will be overwritten.
        Args:
            attr (str): Attribute name (also used as key on the dictionary)
            value (Any): Value for the attribute
        """
        self.attr_dict[attr] = value

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set proxy metadata. Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten.
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def add_meta_parent(self, line_parent):
        """
        Adds a meta parent UUID to the metadata dictionary. Initializes it in case it was not yet initialized.
        This is used to created visualization lines or other elements without actually parenting the element.
        Args:
            line_parent (str, Proxy): New meta parent, if a UUID string. If Proxy, it will get the UUID (get_uuid).
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        if isinstance(line_parent, str) and is_uuid_valid(line_parent):
            self.metadata[RiggerConstants.PROXY_META_PARENT] = line_parent
        if isinstance(line_parent, Proxy):
            self.metadata[RiggerConstants.PROXY_META_PARENT] = line_parent.get_uuid()

    def add_color(self, rgb_color):
        """
        Adds a color attribute to the metadata dictionary.
        This attribute is used to determine a fixed proxy color (instead of the side setup)
        Args:
            rgb_color (tuple, list): New RGB color. Must be a tuple or a list with 3 floats/integers
        """
        if isinstance(rgb_color, (tuple, list)) and len(rgb_color) >= 3:  # 3 = RGB
            if all(isinstance(item, (int, float)) for item in rgb_color):
                self.attr_dict["autoColor"] = False
                self.attr_dict["colorDefault"] = [rgb_color[0], rgb_color[1], rgb_color[2]]
            else:
                logger.debug(f'Unable to set color. Input must contain only numeric values.')
        else:
            logger.debug(f'Unable to set color. Input must be a tuple or a list with at least 3 elements (RGB).')

    def set_uuid(self, uuid):
        """
        Sets a new UUID for the proxy.
        If no UUID is provided or set a new one will be generated automatically,
        this function is used to force a specific value as UUID.
        Args:
            uuid (str): A new UUID for this proxy
        """
        error_message = f'Unable to set proxy UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.uuid = uuid
        else:
            logger.warning(error_message)

    def set_parent_uuid(self, uuid):
        """
        Sets a new parent UUID for the proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            uuid (str): A new UUID for the parent of this proxy
        """
        error_message = f'Unable to set proxy parent UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def set_parent_uuid_from_proxy(self, parent_proxy):
        """
        Sets the provided proxy as the parent  of this proxy. Its UUID  is extracted as parent_UUID for this proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            parent_proxy (Proxy): A proxy object. The UUID for the parent will be extracted from it.
                                  Will be the parent of this proxy when being parented.
        """
        error_message = f'Unable to set proxy parent UUID. Invalid proxy input.'
        if not parent_proxy or not isinstance(parent_proxy, Proxy):
            logger.warning(error_message)
            return
        parent_uuid = parent_proxy.get_uuid()
        self.set_parent_uuid(parent_uuid)

    def clear_parent_uuid(self):
        """
        Clears the parent UUID by setting the "parent_uuid" to None
        """
        self.parent_uuid = None

    def set_meta_type(self, value):
        """
        Adds a proxy meta type key and value to the metadata dictionary. Used to define proxy type in modules.
        Args:
            value (str, optional): Type "tag" used to determine overwrites.
                                   e.g. "hip", so the module knows it's a "hip" proxy.
        """
        self.add_to_metadata(key=RiggerConstants.PROXY_META_TYPE, value=value)

    def read_data_from_dict(self, proxy_dict):
        """
        Reads the data from a proxy dictionary and updates the values of this proxy to match it.
        Args:
            proxy_dict (dict): A dictionary describing the proxy data. e.g. {"name": "proxy", "parent": "1234...", ...}
        Returns:
            Proxy: This object (self)
        """
        if proxy_dict and not isinstance(proxy_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = proxy_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _parent = proxy_dict.get('parent')
        if _parent:
            self.set_parent_uuid(uuid=_parent)

        _loc_scale = proxy_dict.get('locatorScale')
        if _loc_scale:
            self.set_locator_scale(scale=_loc_scale)

        transform = proxy_dict.get('transform')
        if transform and len(transform) == 3:
            self._initialize_transform()
            self.transform.set_transform_from_dict(transform_dict=transform)

        offset_transform = proxy_dict.get('offsetTransform')
        if offset_transform and len(offset_transform) == 3:
            self._initialize_offset_transform()
            self.offset_transform.set_transform_from_dict(transform_dict=transform)

        attributes = proxy_dict.get('attributes')
        if attributes:
            self.set_attr_dict(attr_dict=attributes)

        metadata = proxy_dict.get('metadata')
        if metadata:
            self.set_metadata_dict(metadata=metadata)

        _uuid = proxy_dict.get('uuid')
        if _uuid:
            self.set_uuid(uuid=_uuid)
        return self

    def read_data_from_scene(self):
        """
        Attempts to find the proxy in the scene. If found, it reads the data into the proxy object.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            Proxy: This object (self)
        """
        ignore_attr_list = [RiggerConstants.PROXY_ATTR_UUID,
                            RiggerConstants.PROXY_ATTR_SCALE]
        proxy = get_object_from_uuid_attr(uuid_string=self.uuid, attr_name=RiggerConstants.PROXY_ATTR_UUID)
        if proxy:
            try:
                self._initialize_transform()
                self.transform.set_transform_from_object(proxy)
                attr_dict = {}
                user_attrs = cmds.listAttr(proxy, userDefined=True) or []
                for attr in user_attrs:
                    if not cmds.getAttr(f'{proxy}.{attr}', lock=True) and attr not in ignore_attr_list:
                        attr_dict[attr] = cmds.getAttr(f'{proxy}.{attr}')
                if attr_dict:
                    self.set_attr_dict(attr_dict=attr_dict)
            except Exception as e:
                logger.debug(f'Unable to read proxy data for "{str(self.name)}". Issue: {str(e)}')
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_meta_parent_uuid(self):
        """
        Gets the meta parent of this proxy (if present)
        Returns:
            str or None: The UUID set as meta parent, otherwise, None.
        """
        if self.metadata and isinstance(self.metadata, dict):
            return self.metadata.get(RiggerConstants.PROXY_META_PARENT, None)

    def get_name(self):
        """
        Gets the name property of the proxy.
        Returns:
            str or None: Name of the proxy, None if it's not set.
        """
        return self.name

    def get_uuid(self):
        """
        Gets the uuid value of this proxy.
        Returns:
            str: uuid string
        """
        return self.uuid

    def get_parent_uuid(self):
        """
        Gets the parent uuid value of this proxy.
        Returns:
            str: uuid string for the potential parent of this proxy.
        """
        return self.parent_uuid

    def get_locator_scale(self):
        """
        Gets the locator scale for this proxy
        Returns:
            float: The locator scale
        """
        return self.locator_scale

    def get_attr_dict(self):
        """
        Gets the attribute dictionary for this proxy
        Returns:
            dict: a dictionary where the key is the attribute name and the value is the value of the attribute.
                  e.g. {"locatorScale": 1, "isVisible": True}
        """
        return self.attr_dict

    def get_proxy_as_dict(self, include_uuid=False, include_transform_data=True, include_offset_data=True):
        """
        Returns all necessary information to recreate this proxy as a dictionary
        Args:
            include_uuid (bool, optional): If True, it will also include an "uuid" key and value in the dictionary.
            include_transform_data (bool, optional): If True, it will also export the transform data.
            include_offset_data (bool, optional): If True, it will also export the offset transform data.
        Returns:
            dict: Proxy data as a dictionary
        """
        # Create Proxy Data
        proxy_data = {"name": self.name,
                      "parent": self.get_parent_uuid(),
                      "locatorScale": self.locator_scale,
                      }

        if self.transform and include_transform_data:
            proxy_data["transform"] = self.transform.get_transform_as_dict()

        if self.offset_transform and include_offset_data:
            proxy_data["offsetTransform"] = self.offset_transform.get_transform_as_dict()

        if self.get_attr_dict():
            proxy_data["attributes"] = self.get_attr_dict()

        if self.get_metadata():
            proxy_data["metadata"] = self.get_metadata()

        if include_uuid and self.get_uuid():
            proxy_data["uuid"] = self.get_uuid()

        return proxy_data


class ModuleGeneric:
    icon = resource_library.Icon.dev_code  # TODO TEMP @@@

    def __init__(self,
                 name=None,
                 prefix=None,
                 proxies=None,
                 parent_uuid=None,
                 metadata=None):
        # Default Values
        self.name = None
        self.prefix = None
        self.proxies = []
        self.parent_uuid = None  # Module is parented to this object
        self.metadata = None
        self.active = True

        if name:
            self.set_name(name)
        if prefix:
            self.set_prefix(prefix)
        if proxies:
            self.set_proxies(proxies)
        if parent_uuid:
            self.set_parent_uuid(parent_uuid)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new module name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.name = name

    def set_prefix(self, prefix):
        """
        Sets a new module prefix.
        Args:
            prefix (str): New name to use on the proxy.
        """
        if not prefix or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def set_proxies(self, proxy_list):
        """
        Sets a new proxy name.
        Args:
            proxy_list (str): New name to use on the proxy.
        """
        if not proxy_list or not isinstance(proxy_list, list):
            logger.warning(f'Unable to set new list of proxies. '
                           f'Expected list of proxies but got "{str(proxy_list)}"')
            return
        self.proxies = proxy_list

    def add_to_proxies(self, proxy):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            proxy (Proxy, List[Proxy]): New proxy element to be added to this module or a list of proxies
        """
        if proxy and isinstance(proxy, Proxy):
            proxy = [proxy]
        if proxy and isinstance(proxy, list):
            for obj in proxy:
                if isinstance(obj, Proxy):
                    self.proxies.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Incompatible type.')
            return
        logger.debug(f'Unable to add proxy to module. '
                     f'Must be of the type "Proxy" or a list containing only Proxy elements.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set module metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def set_active_state(self, is_active):
        """
        Sets the "is_active" variable. This variable determines if the module will be skipped while in a project or not.
        Args:
            is_active (bool): True if active, False if inactive. Inactive modules are ignored when in a project.
        """
        if not isinstance(is_active, bool):
            logger.warning(f'Unable to set active state. '
                           f'Expected a boolean, but got: "{str(type(is_active))}"')
            return
        self.active = is_active

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def set_parent_uuid(self, uuid):
        """
        Sets a new parent UUID for the proxy.
        If a parent UUID is set, the proxy has enough information be re-parented when part of a set.
        Args:
            uuid (str): A new UUID for the parent of this proxy
        """
        error_message = f'Unable to set proxy parent UUID. Invalid UUID input.'
        if not uuid or not isinstance(uuid, str):
            logger.warning(error_message)
            return
        if is_uuid_valid(uuid) or is_short_uuid_valid(uuid):
            self.parent_uuid = uuid
        else:
            logger.warning(error_message)

    def clear_parent_uuid(self):
        """
        Clears the parent UUID by setting the "parent_uuid" attribute to None
        """
        self.parent_uuid = None

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

        self.proxies = []
        for uuid, description in proxy_dict.items():
            _proxy = Proxy()
            _proxy.set_uuid(uuid)
            _proxy.read_data_from_dict(proxy_dict=description)
            self.proxies.append(_proxy)

    def read_data_from_dict(self, module_dict):
        """
        Reads the data from a module dictionary and updates the values of this module to match it.
        Args:
            module_dict (dict): A dictionary describing the module data. e.g. {"name": "generic"}
        Returns:
            ModuleGeneric: This module (self)
        """
        if module_dict and not isinstance(module_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = module_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _prefix = module_dict.get('prefix')
        if _prefix:
            self.set_prefix(prefix=_prefix)

        _parent = module_dict.get('parent')
        if _parent:
            self.set_parent_uuid(uuid=_parent)

        _proxies = module_dict.get('proxies')
        if _proxies and isinstance(_proxies, dict):
            self.read_proxies_from_dict(proxy_dict=_proxies)

        is_active = module_dict.get('active')
        if isinstance(is_active, bool):
            self.set_active_state(is_active=is_active)

        metadata = module_dict.get('metadata')
        if metadata:
            self.set_metadata_dict(metadata=metadata)
        return self

    def read_data_from_scene(self):
        """
        Attempts to find the proxies in the scene. If found, their data is read into the proxy object.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            ModuleGeneric: This object (self)
        """
        for proxy in self.proxies:
            proxy.read_data_from_scene()
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_name(self):
        """
        Gets the name property of the rig module.
        Returns:
            str or None: Name of the rig module, None if it's not set.
        """
        return self.name

    def get_prefix(self):
        """
        Gets the prefix property of the rig module.
        Returns:
            str or None: Prefix of the rig module, None if it's not set.
        """
        return self.prefix

    def get_parent_uuid(self):
        """
        Gets the parent uuid value of this proxy.
        Returns:
            str: uuid string for the potential parent of this proxy.
        """
        return self.parent_uuid

    def get_proxies(self):
        """
        Gets the proxies in this rig module.
        Returns:
            list: A list of proxies found in this rig module.
        """
        return self.proxies

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_active_state(self):
        """
        Gets the active state. (True or False)
        Returns:
            bool: True if module is active, False if not.
        """
        return self.active

    def get_module_as_dict(self, include_module_name=False, include_offset_data=True):
        """
        Gets the properties of this module (including proxies) as a dictionary
        Args:
            include_module_name (bool, optional): If True, it will also include the name of the class in the dictionary.
                                                  e.g. "ModuleGeneric"
            include_offset_data (bool, optional): If True, it will include the offset transform data in the dictionary.
        Returns:
            dict: Dictionary describing this module
        """
        module_data = {}
        if self.name:
            module_data["name"] = self.name
        module_data["active"] = self.active
        if self.prefix:
            module_data["prefix"] = self.prefix
        if self.parent_uuid:
            module_data["parent"] = self.parent_uuid
        if self.metadata:
            module_data["metadata"] = self.metadata
        module_proxies = {}
        for proxy in self.proxies:
            module_proxies[proxy.get_uuid()] = proxy.get_proxy_as_dict(include_offset_data=include_offset_data)
        module_data["proxies"] = module_proxies
        if include_module_name:
            module_name = self.get_module_class_name()
            module_data["module"] = module_name
        return module_data

    def get_module_class_name(self, remove_module_prefix=False):
        """
        Gets the name of this class
        Args:
            remove_module_prefix (bool, optional): If True, it will remove the prefix word "Module" from class name.
                                                   Used to reduce the size of the string in JSON outputs.
        Returns:
            str: Class name as a string
        """
        if remove_module_prefix:
            return remove_prefix(input_string=str(self.__class__.__name__), prefix="Module")
        return str(self.__class__.__name__)

    # --------------------------------------------------- Misc ---------------------------------------------------
    def apply_transforms(self, apply_offset=False):
        """
        Attempts to apply offset and parent offset transforms to the proxy elements.
        To be used only after proxy is built.
        Args:
            apply_offset (bool, optional): If True, it will attempt to also apply the offset data. (Happens first)
        """
        for proxy in self.proxies:
            proxy.apply_transforms(apply_offset=apply_offset)

    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        if not self.proxies:
            logger.warning('Missing proxies. A rig module needs at least one proxy to function.')
            return False
        return True

    def build_proxy(self, project_prefix=None):
        """
        Builds the proxy representation of the rig (for the user to adjust and determine the pose)
        Args:
            project_prefix (str, optional): If provided, this prefix will be added to the proxies when they are created.
                                            This is an extra prefix, added on top of the module prefix (self.prefix)
                                            So the final pattern is "<project_prefix>_<module_prefix>_<name>"
                                            Module prefix is the prefix stored in this object "self.prefix"
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        proxy_data = []
        _prefix = ''
        prefix_list = []
        if project_prefix and isinstance(project_prefix, str):
            prefix_list.append(project_prefix)
        if self.prefix and isinstance(self.prefix, str):
            prefix_list.append(self.prefix)
        if prefix_list:
            _prefix = '_'.join(prefix_list)
        for proxy in self.proxies:
            proxy_data.append(proxy.build(prefix=_prefix, apply_transforms=False))
        return proxy_data

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Usually used to create extra behavior unique to this module. e.g. Constraints, automations.
        """
        logger.debug(f'"build_proxy_post" function for "{self.get_module_class_name()}" was called.')
        self.apply_transforms()

    def build_rig(self):
        """
        Runs build rig script.
        Expects proxy to be present in the scene.
        """
        logger.debug(f'"build_rig" function from "{self.get_module_class_name()}" was called.')
        for proxy in self.proxies:
            proxy_node = find_proxy_node_from_uuid(proxy.get_uuid())
            if not proxy_node:
                continue
            cmds.select(clear=True)  # When creating a joint, selection affects its hierarchy
            joint = cmds.joint(name=proxy_node.get_short_name())

            locator_scale = proxy.get_locator_scale()
            cmds.setAttr(f'{joint}.radius', locator_scale)
            match_translate(source=proxy_node, target_list=joint)

            # parent_proxy_node = find_joint_node_from_uuid(proxy.get_parent_uuid())
            # hierarchy_utils.parent(source_objects=joint, target_parent=parent_proxy_node)

            # Add proxy data for reference
            add_attr(target_list=joint,
                     attributes=RiggerConstants.JOINT_ATTR_UUID,
                     attr_type="string")
            set_attr(obj_list=joint, attr_list=RiggerConstants.JOINT_ATTR_UUID, value=proxy.get_uuid())
            cmds.select(clear=True)  # When creating a joint, the new joint is selected.

    def build_rig_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        logger.debug(f'"build_rig_post" function from "{self.get_module_class_name()}" was called.')
        for proxy in self.proxies:
            joint = find_joint_node_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            parent_joint_node = find_joint_node_from_uuid(proxy.get_parent_uuid())
            hierarchy_utils.parent(source_objects=joint, target_parent=parent_joint_node)
        cmds.select(clear=True)


class RigProject:
    icon = resource_library.Icon.dev_brain  # TODO TEMP @@@

    def __init__(self,
                 name=None,
                 prefix=None,
                 metadata=None):
        # Default Values
        self.name = "Untitled"
        self.prefix = None
        self.modules = []
        self.metadata = None

        if name:
            self.set_name(name=name)
        if prefix:
            self.set_prefix(prefix=prefix)
        if metadata:
            self.set_metadata_dict(metadata=metadata)

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_name(self, name):
        """
        Sets a new project name.
        Args:
            name (str): New name to use on the proxy.
        """
        if name is None or not isinstance(name, str):
            logger.warning(f'Unable to set name. Expected string but got "{str(type(name))}"')
            return
        self.name = name

    def set_prefix(self, prefix):
        """
        Sets a new module prefix.
        Args:
            prefix (str): New name to use on the proxy.
        """
        if not prefix or not isinstance(prefix, str):
            logger.warning(f'Unable to set prefix. Expected string but got "{str(type(prefix))}"')
            return
        self.prefix = prefix

    def add_to_modules(self, module):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            module (ModuleGeneric, List[ModuleGeneric]): New module element to be added to this project.
        """
        from gt.tools.auto_rigger.rig_modules import RigModules
        modules_attrs = vars(RigModules)
        all_modules = [attr for attr in modules_attrs if not (attr.startswith('__') and attr.endswith('__'))]
        if module and str(module.__class__.__name__) in all_modules:
            module = [module]
        if module and isinstance(module, list):
            for obj in module:
                if str(obj.__class__.__name__) in all_modules:
                    self.modules.append(obj)
                else:
                    logger.debug(f'Unable to add "{str(obj)}". Provided module not found in "RigModules".')
            return
        logger.debug(f'Unable to add provided module to rig project. '
                     f'Must be of the type "ModuleGeneric" or a list containing only ModuleGeneric elements.')

    def set_metadata_dict(self, metadata):
        """
        Sets the metadata property. The metadata is any extra value used to further describe the curve.
        Args:
            metadata (dict): A dictionary describing extra information about the curve
        """
        if not isinstance(metadata, dict):
            logger.warning(f'Unable to set rig project metadata. '
                           f'Expected a dictionary, but got: "{str(type(metadata))}"')
            return
        self.metadata = metadata

    def add_to_metadata(self, key, value):
        """
        Adds a new item to the metadata dictionary. Initializes it in case it was not yet initialized.
        If an element with the same key already exists in the metadata dictionary, it will be overwritten
        Args:
            key (str): Key of the new metadata element
            value (Any): Value of the new metadata element
        """
        if not self.metadata:  # Initialize metadata in case it was never used.
            self.metadata = {}
        self.metadata[key] = value

    def read_modules_from_dict(self, modules_dict):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            modules_dict (dict): A proxy description dictionary. It must match an expected pattern for this to work:
                                 Acceptable pattern: {"uuid_str": {<description>}}
                                 "uuid_str" being the actual uuid string value of the proxy.
                                 "<description>" being the output of the operation "proxy.get_proxy_as_dict()".
        """
        if not modules_dict or not isinstance(modules_dict, dict):
            logger.debug(f'Unable to read modules from dictionary. Input must be a dictionary.')
            return

        self.modules = []
        from gt.tools.auto_rigger.rig_modules import RigModules
        available_modules = vars(RigModules)
        for class_name, description in modules_dict.items():
            if not class_name.startswith("Module"):
                class_name = f'Module{class_name}'
            if class_name in available_modules:
                _module = available_modules.get(class_name)()
            else:
                _module = ModuleGeneric()
            _module.read_data_from_dict(module_dict=description)
            self.modules.append(_module)

    def read_data_from_dict(self, module_dict):
        """
        Reads the data from a project dictionary and updates the values of this project to match it.
        Args:
            module_dict (dict): A dictionary describing the project data. e.g. {"name": "untitled", "modules": ...}
        Returns:
            RigProject: This project (self)
        """
        self.modules = []
        self.metadata = None

        if module_dict and not isinstance(module_dict, dict):
            logger.debug(f'Unable o read data from dict. Input must be a dictionary.')
            return

        _name = module_dict.get('name')
        if _name:
            self.set_name(name=_name)

        _prefix = module_dict.get('prefix')
        if _prefix:
            self.set_prefix(prefix=_prefix)

        _modules = module_dict.get('modules')
        if _modules and isinstance(_modules, dict):
            self.read_modules_from_dict(modules_dict=_modules)

        metadata = module_dict.get('metadata')
        if metadata:
            self.set_metadata_dict(metadata=metadata)
        return self

    def read_data_from_scene(self):
        """
        Attempts to find the proxies within modules that are present in the scene. If found, their data is extracted.
        e.g. The user moved the proxy, a new position will be read and saved to this proxy.
             New custom attributes or anything else added to the proxy will also be saved.
        Returns:
            RigProject: This object (self)
        """
        for module in self.modules:
            module.read_data_from_scene()
        return self

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_name(self):
        """
        Gets the name property of the rig project.
        Returns:
            str or None: Name of the rig project, None if it's not set.
        """
        return self.name

    def get_prefix(self):
        """
        Gets the prefix property of the rig project.
        Returns:
            str or None: Prefix of the rig project, None if it's not set.
        """
        return self.prefix

    def get_modules(self):
        """
        Gets the modules of this rig project.
        Returns:
            list: A list of modules found in this project
        """
        return self.modules

    def get_metadata(self):
        """
        Gets the metadata property.
        Returns:
            dict: Metadata dictionary
        """
        return self.metadata

    def get_project_as_dict(self):
        """
        Gets the description for this project (including modules and its proxies) as a dictionary.
        Returns:
            dict: Dictionary describing this project.
        """
        project_modules = {}
        for module in self.modules:
            module_class_name = module.get_module_class_name(remove_module_prefix=True)
            project_modules[module_class_name] = module.get_module_as_dict()

        project_data = {}
        if self.name:
            project_data["name"] = self.name
        if self.prefix:
            project_data["prefix"] = self.prefix
        project_data["modules"] = project_modules
        if self.metadata:
            project_data["metadata"] = self.metadata

        return project_data

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig project is valid (can be used)
        """
        if not self.modules:
            logger.warning('Missing modules. A rig project needs at least one module to function.')
            return False
        return True

    def build_proxy(self, callback=None):
        """
        Builds Proxy/Guide Armature/Skeleton
        """
        cmds.refresh(suspend=True)
        try:
            root_transform, root_group = create_proxy_root_curve()
            setup = cmds.group(name=f"setup_{NamingConstants.Suffix.GRP}", empty=True, world=True)
            add_attr(target_list=setup, attr_type="string", is_keyable=False,
                     attributes=RiggerConstants.SETUP_DATA_ATTR, verbose=True)
            set_attr(obj_list=setup, attr_list=['overrideEnabled', 'overrideDisplayType'], value=1)
            hierarchy_utils.parent(source_objects=setup, target_parent=root_group)

            # Build Proxy
            proxy_data_list = []
            for module in self.modules:
                if not module.get_active_state():  # If not active, skip
                    continue
                proxy_data_list += module.build_proxy()

            for proxy_data in proxy_data_list:
                add_side_color_setup(obj=proxy_data.get_long_name())
                hierarchy_utils.parent(source_objects=proxy_data.get_setup(), target_parent=setup)
                hierarchy_utils.parent(source_objects=proxy_data.get_offset(), target_parent=root_transform)

            # Parent Proxy
            for module in self.modules:
                if not module.get_active_state():  # If not active, skip
                    continue
                parent_proxies(proxy_list=module.get_proxies())
                create_proxy_visualization_lines(proxy_list=module.get_proxies(), lines_parent=setup)
                for proxy in module.get_proxies():
                    proxy.apply_attr_dict()
                module.build_proxy_post()
        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()

    def build_rig(self, callback=None):
        """
        Builds Rig using Proxy/Guide Armature/Skeleton (from previous step (build_proxy)
        """
        cmds.refresh(suspend=True)
        try:
            root_transform, root_group = create_control_root_curve()
            setup = cmds.group(name=f"setup_{NamingConstants.Suffix.GRP}", empty=True, world=True)
            setup = Node(setup)
            add_attr(target_list=setup, attr_type="string", is_keyable=False,
                     attributes=RiggerConstants.SETUP_DATA_ATTR, verbose=True)
            set_attr(obj_list=setup, attr_list=['overrideEnabled', 'overrideDisplayType'], value=1)
            hierarchy_utils.parent(source_objects=setup, target_parent=root_group)

            # Build Rig
            for module in self.modules:
                if not module.get_active_state():  # If not active, skip
                    continue
                module.build_rig()

            # Build Rig Post
            for module in self.modules:
                if not module.get_active_state():  # If not active, skip
                    continue
                module.build_rig_post()

        except Exception as e:
            raise e
        finally:
            cmds.refresh(suspend=False)
            cmds.refresh()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    cmds.file(new=True, force=True)

    a_1st_proxy = Proxy(name="first")
    a_1st_proxy.set_position(y=5)
    a_2nd_proxy = Proxy(name="second")
    a_2nd_proxy.set_position(x=10)
    a_2nd_proxy.set_rotation(z=-35)
    a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())

    a_module = ModuleGeneric()
    a_module.add_to_proxies(a_1st_proxy)
    a_module.add_to_proxies(a_2nd_proxy)
    a_module.set_prefix("prefix")

    a_project = RigProject()
    a_project.add_to_modules(a_module)
    a_project.build_proxy()
    a_project.build_rig()
