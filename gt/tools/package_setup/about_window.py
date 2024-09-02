from maya import OpenMayaUI as OpenMayaUI
import gt.core.version as core_version
import gt.ui.qt_import as ui_qt
import maya.cmds as cmds


def build_gui_about_gt_tools():
    """Creates "About" window for the GT Tools menu"""

    gt_version = core_version.get_installed_version()

    window_name = "build_gui_about_gt_tools"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title="About - GT Tools", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style="none")  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text("GT Tools", bgc=[0.4, 0.4, 0.4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style="none", p="main_column")  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l="Version Installed: " + gt_version, align="center", fn="boldLabelFont")
    cmds.separator(h=5, style="none")  # Empty Space
    cmds.text(l="GT Tools is a free collection of Maya scripts", align="center")

    cmds.separator(h=15, style="none")  # Empty Space
    cmds.text(l="About:", align="center", fn="boldLabelFont")
    cmds.text(
        l="This is my collection of scripts for Autodesk Maya.\n"
        "These scripts were created with the aim of automating,\n e"
        "nhancing or simply filling the missing details of what\n I find lacking in Maya.",
        align="center",
    )
    cmds.separator(h=15, style="none")  # Empty Space
    cmds.text(
        l="When installed you can find a pull-down menu that\n provides easy access to a variety of related tools.",
        align="center",
    )
    cmds.separator(h=5, style="none")  # Empty Space
    cmds.text(
        l="This menu contains sub-menus that have been\n organized to contain related tools.\n "
        "For example: modeling, rigging, utilities, etc...",
        align="center",
    )
    cmds.separator(h=15, style="none")  # Empty Space
    cmds.text(
        l="All of these items are supplied as is.\nYou alone are responsible for any issues.\n" "Use at your own risk.",
        align="center",
    )
    cmds.separator(h=15, style="none")  # Empty Space
    cmds.text(l="Hopefully these scripts are helpful to you\nas they are to me.", align="center")
    cmds.separator(h=15, style="none")  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.text("Guilherme Trevisan  ")
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.separator(h=15, style="none")  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style="none")  # Empty Space

    # Close Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style="none")
    cmds.button(l="OK", h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style="none")

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = ui_qt.shiboken.wrapInstance(int(qw), ui_qt.QtWidgets.QWidget)
    icon = ui_qt.QtGui.QIcon(":/question.png")
    widget.setWindowIcon(icon)

    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
