"""
 GT Sphere Types - Sphere Types is a simple reminder for Modeling students that they don't need to only use the
 standard sphere for everything.
 github.com/TrevisanGMW/gt-tools -  2020-11-04
 Tested on Maya 2020 - Windows 10
 
 1.1 - 2020-11-22
 Minor changes to the UI
 
 1.2 - 2020-12-03
 Platonic Sphere A is now created with soft normals
 
 1.3 - 2021-01-25
 Adjusted the size of the spacing between buttons
 
 1.3.1 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 
 1.3.2 - 2021-06-22
 Fixed a little inconsistency on the size of the window

 1.3.3 - 2022-07-10
 PEP8 Cleanup

 To do:
 Improve generated window to give better feedback
 Add more sphere options
 Add sliders to control subdivision level
 
"""
try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2 import QtWidgets, QtGui, QtCore
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide import QtWidgets, QtGui, QtCore
    from PySide.QtGui import QIcon, QWidget

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as OpenMayaUI
import base64
import sys
import os

# Script Version
script_version = "1.3.3"

# Python Version
python_version = sys.version_info.major


def build_gui_sphere_type():
    """ Builds the UI for GT Sphere Types """
    if cmds.window("build_gui_sphere_type", exists=True):
        cmds.deleteUI("build_gui_sphere_type")

        # main dialog Start Here =================================================================================

    window_gui_sphere_type = cmds.window("build_gui_sphere_type", title='Sphere Types - (v' + script_version + ')',
                                         titleBar=True, minimizeButton=False, maximizeButton=False, sizeable=True)
    cmds.window(window_gui_sphere_type, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Generate Header Image
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True)
    header_img = icons_folder_dir + 'gt_m1_sphere_types.png'

    if os.path.isdir(icons_folder_dir) and os.path.exists(header_img) is False:
        image_enconded = 'iVBORw0KGgoAAAANSUhEUgAAAMgAAAA/CAYAAAClz4c/AAAACXBIWXMAAFxGAABcRgEUlENBAAAF8WlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4gPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iQWRvYmUgWE1QIENvcmUgNS42LWMxNDggNzkuMTY0MDM2LCAyMDE5LzA4LzEzLTAxOjA2OjU3ICAgICAgICAiPiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPiA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIiB4bWxuczp4bXA9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8iIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIiB4bWxuczpzdEV2dD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL3NUeXBlL1Jlc291cmNlRXZlbnQjIiB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iIHhtbG5zOnBob3Rvc2hvcD0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3Nob3AvMS4wLyIgeG1wOkNyZWF0b3JUb29sPSJBZG9iZSBQaG90b3Nob3AgMjEuMCAoV2luZG93cykiIHhtcDpDcmVhdGVEYXRlPSIyMDIwLTExLTA0VDE2OjEzOjMyLTA4OjAwIiB4bXA6TWV0YWRhdGFEYXRlPSIyMDIwLTExLTA0VDE2OjEzOjMyLTA4OjAwIiB4bXA6TW9kaWZ5RGF0ZT0iMjAyMC0xMS0wNFQxNjoxMzozMi0wODowMCIgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDpkODMyNzVmNi1mMTAwLTliNGMtOGMzYy1iOTJjYmJmN2I2ZDgiIHhtcE1NOkRvY3VtZW50SUQ9ImFkb2JlOmRvY2lkOnBob3Rvc2hvcDoyZDQ3MjNjNS0yMDM5LTUzNDgtYTRlYi02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'
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(header_img, 'wb')
        image_result.write(image_64_decode)
        image_result.close()

    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200), (2, 100), (3, 10)], cs=[(1, 10), (2, 5), (3, 5)])

    cmds.image(image=header_img)

    cmds.text("Sphere Options:")
    cmds.separator(h=5, p=content_main, st="none")
    cmds.rowColumnLayout(p=content_main, numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 10)],
                         cs=[(1, 10), (2, 5)])
    cmds.separator(h=3, p=content_main, st="none")
    cmds.button(l="Standard Sphere", c=lambda x: create_standard_sphere(), w=100)
    cmds.button(l="Platonic Sphere A", c=lambda x: create_platonic_sphere_a())
    cmds.rowColumnLayout(p=content_main, numberOfColumns=2, columnWidth=[(1, 100), (2, 100), (3, 10)],
                         cs=[(1, 10), (2, 5), (3, 5)])
    cmds.button(l="Cube Sphere", c=lambda x: create_cube_sphere(), w=100)
    cmds.button(l="Platonic Sphere B", c=lambda x: create_platonic_sphere_b())
    cmds.separator(h=10, st="none")

    # Show and Lock Window
    cmds.showWindow(window_gui_sphere_type)
    cmds.window(window_gui_sphere_type, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_gui_sphere_type)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/lambert.svg')

    widget.setWindowIcon(icon)

    # main dialog Ends Here =================================================================================


# Functions to get all the stuff we need

def create_standard_sphere():
    mel.eval('polySphere -r 1 -sx 20 -sy 20 -ax 0 1 0 -cuv 2 -ch 1; objectMoveCommand;')
    message = 'Create > Polygon Primitives > <span style=\"color:#FF0000;text-decoration:underline;\">Sphere</span>'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


def create_platonic_sphere_a():
    mel.eval('polyPlatonic -primitive 4 -subdivisionMode 0 -subdivisions 1 -radius 1 -sphericalInflation 1;')
    sphere = cmds.ls(selection=True)
    cmds.polySoftEdge(sphere, a=180)
    cmds.select(sphere)
    message = 'Create > Polygon Primitives > <span style=\"color:#FF0000;text-decoration:underline;\">' \
              'Platonic Solid</span>'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    cmds.inViewMessage(amg='(Settings: Icosahedron, Quads, 1, 1, 1)', pos='botLeft', fade=True, alpha=.9)


def create_cube_sphere():
    mel.eval('polyCube -w 2.25 -h 2.25 -d 2.25 -sx 1 -sy 1 -sz 1 -ax 0 1 0 -cuv 4 -ch 1;')
    mel.eval('polySmooth  -mth 0 -sdt 2 -ovb 1 -ofb 3 -ofc 0 -ost 0 -ocr 0 -dv 2 -bnr 1 -c 1 '
             '-kb 1 -ksb 1 -khe 0 -kt 1 -kmb 1 -suv 1 -peh 0 -sl 1 -dpe 1 -ps 0.1 -ro 1 -ch 1')
    # mel.eval('SelectToolOptionsMarkingMenu;')
    message = 'Create > Polygon Primitives > <span style=\"color:#FF0000;text-decoration:underline;\">Cube</span>'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    cmds.inViewMessage(amg='Mesh > <span style=\"color:#FF0000;text-decoration:underline;\">'
                           'Smooth</span> (2x)', pos='botLeft', fade=True, alpha=.9)


def create_platonic_sphere_b():
    mel.eval('polyPlatonic -primitive 2 -subdivisionMode 0 -subdivisions 2 -radius 1 -sphericalInflation 1;')
    message = 'Create > Polygon Primitives > <span style=\"color:#FF0000;text-decoration:underline;\">' \
              'Platonic Solid</span>'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    cmds.inViewMessage(amg='(Settings: Octaheadron, Quads, 2, 1, 1)', pos='botLeft', fade=True, alpha=.9)


# Build UI
if __name__ == "__main__":
    build_gui_sphere_type()
