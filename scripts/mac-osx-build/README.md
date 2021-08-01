# Notes on Mac OSX build

Used on version 10.15
The yanom.spec file ahs two modifications to allow the package to be built.

These modifications may not be required on some systems,a nd additional modifactions may be needed on others.  This is inconsistent, but it has been found that modification 2, detialed below, was not required for the first 2 months of building the package and then somehtingf somewehre chnaged and the hidden import was required to be added.
# Modification 1

Add value to `datas` to find the `pyfiglet` fonts

```
datas=[('../venv/lib/python3.9/site-packages/pyfiglet', './pyfiglet')],
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

