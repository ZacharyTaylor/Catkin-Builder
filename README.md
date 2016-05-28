# Catkin-Builder-Sublime

Use Catkin build in Sublime Text 3.

![Screenshot](https://raw.githubusercontent.com/ZacharyTaylor/Catkin-Builder/master/screenshot.gif)

## Prerequisites

Requires **ROS** (http://www.ros.org/install/) and Sublime Text 3

If you can open a terminal, cd to your ROS package directory and run "catkin build <package_name>" without issues, then this plugin should work.

## Usage
Switch your build system in Sublime to Catkin by going to Tools -> Build system -> Catkin.
Build your files using Ctrl+B or Ctrl+Shift+B for build options.
  
Can be called on any type of file that is in a Catkin Package.
  
If the build process generates errors, the first error encountered will be reprinted in a separate section below the other build errors. This behavior can be disabled (see the Options Section below).
  
## Installing

### Package Control
  Not yet part of Package Control (hopefully coming soon).
  
### Manual install:
1. Clone or download a zip of the repo.
2. Open your Sublime Text package directory by going into Sublime and clicking on Preferences -> Browse Packages
3. Place the files in a folder in the Sublime Text Packages folder.

## Build Variants
* **Catkin:** builds the package the file it is called from belongs to.
* **Catkin - build dependencies:** Builds the package and all the packages it depends on.
    
## Options
The Catkin.sublime-build script has several additional options that are set in the CatkinBuilder.sublime-settings file

* **color:** Forces output to contain ANSI color information (will only display correctly if additional plugins that allow Sublime Text's build output to support ANSI color are present)
* **status-updates:** On by default, provides status messages during building
* **trim_output:** On by default, removes information about the workspace setup and other similar details from Catkins output
* **replace_q:** On by default, an ugly workaround for an issue encountered with the output of Catkin. Some symbols appear as question marks in the output. This flag replaces all question marks including those that should appear in the text.
* **repeat_err:** On by default, repeats the first error encountered at the end of the error message.
  
## Known issues: 
* Catkin will return question marks to the script instead of some symbols. The current workaround for this is the replace_q flag that removes all question marks from the output.
* Repeating error function is based on simple string matching and far from bulletproof.
* Completely untested in anything that isn't Sublime Text 3 in Ubuntu 16.04, if you are run it on another OS let me know if it works or breaks
* Coloring of output is based on very simple keyword matching
