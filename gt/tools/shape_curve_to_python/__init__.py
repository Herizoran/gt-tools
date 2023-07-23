"""
 GT Curve to Python - Script to convert curve shapes to python code.
 github.com/TrevisanGMW/gt-tools -  2020-01-02

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-01-03
 Minor patch adjustments to the script

 1.2 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 Added length checker for selection before running.

 1.3 - 2020-06-17
 Changed UI
 Added help menu
 Added icon

 1.4 - 2020-06-27
 No longer failing to generate curves with non-unique names
 Tweaked the color and text for the title and help menu

 1.5 - 2021-01-26
 Fixed way the curve is generated to account for closed and opened curves

 1.6 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.6.1 to 1.6.3 - 2022-07-14 to 2022-07-26
 Added logger
 Added patch version
 PEP8 General cleanup
 Updated script name
 Increased the size of the output window
 Updated help
 Added save to shelf
"""
# Tool Version
__version_tuple__ = (1, 6, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Curve to Python.
    """
    from gt.tools.shape_curve_to_python import shape_curve_to_python
    shape_curve_to_python.script_version = __version__
    shape_curve_to_python.build_gui_py_curve()


if __name__ == "__main__":
    launch_tool()
