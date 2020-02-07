# ENGIN-2201 Bridge Project
Bridge Project for College of DuPage's ENGIN-2201 Statics class

## Getting Started
### EXE
The precompiled exe is uploaded. If you'd rather compile it yourself for security purposes, the instructions are below.
### Compilation Instructions
#### Linux / Ubuntu
1) Download Python, Anaconda.
2) conda create --name bridge numpy nomkl matplotlib pytz pyqt
3) conda activate bridge
4) pip install pyinstaller
5) Navigate to directory with gui.py and bridge.py
6) pyinstaller gui.py --hidden-import='pkg_resources.py2_warn' --onefile
7) The EXE will now be located in ./dist. 

## Usage
Design a truss structure. Make sure the left and right nodes are pinned (vertical and horizontal supports) and make sure there is at least one node on the roadway between them (minimum 3 roadway nodes).

To save your bridge, press the Save Bridge button and save it to a .txt file. You can then run the bridge using my program, or see the pretty animation using the old program.

## Images
#### Bridge GUI
<img src="https://i.imgur.com/d56HND8.png">

#### Old Program

![Bridge Demo](https://i.imgur.com/rNWAU2n.gif)
