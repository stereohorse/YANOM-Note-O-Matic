# Notes on Mac OSX build

Used on OSX version 10.15.7
Build uses Pyinstaller

# About the spec file
The spec file is built using the command 
```
pyi-makespec --onefile --codesign-identity "Developer ID Application: Kevin Durston (4URXD6U67Z)" --noupx  -c --osx-entitlements-file entitlements.plist yanom.py
```

This builds a single file package that is code signed

The yanom.spec file has two modifications to allow the package to be built.

These modifications may not be required on some systems,a nd additional modifactions may be needed on others.  This is inconsistent, but it has been found that modification 2, detialed below, was not required for the first 2 months of building the package and then somehtingf somewehre chnaged and the hidden import was required to be added.

## spec file Modification 1

Add value to `datas` to find the `pyfiglet` fonts

```
datas=[('../venv/lib/python3.9/site-packages/pyfiglet', './pyfiglet')],
```

## spec file Modification 2
Add an entry for hidden import.  The module `pandas.plotting._matplotlib` was not located during builds.
At the top of the spec file add

```
from PyInstaller.utils.hooks import collect_submodules

hidden_imports_pandas=collect_submodules('pandas.plotting._matplotlib')
```

And in the analysis section set `hiddenimports` to

```
hiddenimports=hidden_imports_pandas,
```

# Building the package
There are three scripts to build the package.

`1_build_osx.py` This runs Pyinstaller and prepares the dist folder in the mac-osx-build for the final deployemnt zip file.

`2_notarise_package.py`  Creates a zip of the program and submits if for notarisation.  

`3_deploy_package.py` Creates a zip file that includes pandoc and data directory and copies it to the project root `dist` folder

## Test the package
Copy via internet to a clean VM of OSX and test the package runs and does not have any security warnings.




