# Catkin-Builder-Sublime

Use Catkin build in Sublime Text 3.

## Prerequisites

Requires **ROS** (http://www.ros.org/install/)

If you can open a terminal, cd to your package directory and run "catkin build <package_name>" without issues, then this plugin shoud work.

## Usage:
Switch your build system in Sublime to Catkin by going to Tools -> Build system -> Catkin.
Build your files using Ctrl+B or Ctrl+Shift+B for build options.
  
Can be called on any type of file that is in a Catkin Package.
  
If the build process encounters an error the process will attempt to reprint the first error last so it can be found more easily (feature can be disabled by changing a flag see Other Options section).
  

## Installing

### Package Control
  Not yet part of Package Control (hopfully coming soon).
  
### Git install:
Clone the repo to your Sublime Text Packages directory.
This can be found by opening Sublime and going to Preferences->Browse Packages...
    
### Without Git:
Download the sorce zip and extract to a folder named "Catkin-Bulder-Sublime" in the Sublime Text Packages directory

## Build Variants
* **Catkin:** builds the package the file it is called from belongs to.
* **Catkin - build dependencies:** Builds the package and all the packages it depends on.
    
## Other Options
The Catkin.sublime-build script has several additional flags that can be passed to the build system

* **color:** Forces output to contain color information (Will only display correctly if additional plugins that allow Sublime Texts build output to support ANSI color)
* **keep_status:** Keeps all of the status messages that Catkin produces while running (Even if enabled the script will only output these messages once building finishes)
* **trim_output:** On by default, removes information about the workspace setup and other similar details from Catkins output
* **remove_q:** On by default, an ugly workaround for an issue encountered with the output of Catkin. Indicators to start bold text appears as question marks in the output. This flag removes all question marks from the output including those that should appear in the text.
* **repeat_err:** On by default, repeats the first error encountered at the end of the error message.
  
## Known issues: 
* Catkin will return question marks to the script where bold text should begin/end. The current workaround for this is the --remove_q flag that removes all question marks from the output.
* Errors in finding Catkin will not be reported.
* Repeating error function is based on simple sting matching and far from bulletproof.

## Limitations:
  Only outputs at the start and end of building, with no updates during.
