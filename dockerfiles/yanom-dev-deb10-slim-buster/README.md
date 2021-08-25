# About the `yanom-dev-deb10-slim-buster` Docker Image

This Dockerfile will 
 - Build an image based off an official python image
 - Uses the YANOM source code to build a pyinstaller package
 - Moves the package into a folder called `yanom`, adds a `data` directory to it and a copy of `config.ini`
 - Creates a tarball of the yanom folder


This docker file is used along with the `yanom-prod-deb10-slim-buster` dockerfile to produce a deployable docker image.

There is a script `scripts/build-docker-image.sh` that will automate the process

## Additional files in this folder
`.dockerignore` can be used to minimise the amount copied to the image
`yanom.spec` is a file that is used by Pyinstaller inside the docker image.  

Note- a generic `yanom.spec` can not be created on the fly as Pyinstaller can not find `pyfiglets` or 

Modifications are in the datas line and 3 lines related to hidden imports

# Modification 1
Add value to `datas` to find the `pyfiglet` fonts

```
datas=[('/usr/local/lib/python3.9/site-packages/pyfiglet', './pyfiglet')],
```

# Modification 2
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