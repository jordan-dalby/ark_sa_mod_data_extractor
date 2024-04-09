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
py "path/to/mod_parser.py" standard --mod-root-folder "/YourModFolderName" --output-folder "path/to/output/folder" --mod-name "Your Mod Name"
```
  
For Beacon output:  
```
py "path/to/mod_parser.py" beacon --mod-root-folder "/YourModFolderName" --mod-id "YourModId" --mod-name "Your Mod Name" --content-pack-id "beacon-specific-uuid-for-your-mod" --output-folder "path/to/output/folder"
```
  
5. Check your output folder for the file (either .json or .beacondata), this path is also printed after a successful run of the tool.  
  
    
## Issues  
  
Please report any issues via the GitHub issue tracker.  
  

## Contribute  
  
Please feel free to contribute however you please. Note that pylint can be strict with formatting so I recommend using black to do it automatically. Check .pylintrc for specific settings related to this.