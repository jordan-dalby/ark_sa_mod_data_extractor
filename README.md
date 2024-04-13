# ARK Survival Ascended Mod Data Extractor  
  
This Python tool is used to extract data directly from the ARK SA DevKit. The current version of this tool only supports engrams, PRs to add new features are welcome.  
  
This tool works by finding the ModDataAsset in your mod project and using the Additional Engram Blueprint Classes to find engrams to add to the result file. This tool will not detect engrams that are not in this list.  
  
This tool can generate two types of output:  
1. Standard output- this is a standard JSON file that contains all engrams with their name, path, engram entry, required level, required engram points, max stack size, and recipe.  
2. Beacon output- this outputs a .beacondata file that can be imported directly into Beacon, it contains all of the information that Beacon currently supports for engrams.  
  

## Usage  
  
This tool needs to be used directly inside the ARK DevKit.  
How to use this tool:  
1. Clone this repository into any directory you like  
2. Copy the path to the ```mod_parser.py``` file  
3. In the ARK DevKit, find the Output Log window  
4. Type the following command into that log:  
  
For standard JSON output:  
```
py "absolute/path/to/mod_parser.py" standard --mod-root-folder "/YourModFolderName" --output-folder "path/to/output/folder" --mod-name "Your Mod Name"
```
  
For Beacon output:  
```
py "absolute/path/to/mod_parser.py" beacon --mod-root-folder "/YourModFolderName" --mod-id "YourModId" --mod-name "Your Mod Name" --content-pack-id "beacon-specific-uuid-for-your-mod" --output-folder "path/to/output/folder"
```
  
5. Check your output folder for the file (either .json or .beacondata), this path is also printed after a successful run of the tool.  
  
When importing the .beacondata file into Beacon, you should make sure to delete all current entries, publish the changes, and then import the new ```.beacondata``` file. This is the most reliable way I have found of ensuring everything goes smoothly with the upload.  
  
  
## How do I get the content-pack-id?  

At present, Beacon hides this unique identifier in the ```.beacondata``` file. The best way I have found to retreive it (until it is exposed) is by disecting an exported ```.beacondata``` file. To do this, open your mod in the Beacon desktop app, if you don't have an engram added, add a temporary one. Select the engram (or any engram), and press Export. Save this file somewhere you can find it and open the ```.beacondata``` file with ideally 7zip, or change the extension to ```.tar.gz``` and open with WinRaR, there are two files in there, Manifest.json, and a UUID json file, the name of that UUID file is your content-pack-id.  
  
  
## Issues  
  
Please report any issues via the GitHub issue tracker.  
  

## Contribute  
  
Please feel free to contribute however you please. Note that pylint can be strict with formatting so I recommend using black to do it automatically. Check .pylintrc for specific settings related to this.
