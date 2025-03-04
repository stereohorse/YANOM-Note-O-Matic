# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

hidden_imports_pandas=collect_submodules('pandas.plotting._matplotlib')

block_cipher = None


a = Analysis(['yanom.py'],
             pathex=['D:\\PyCharmProjects\\YANOM-Note-O-Matic\\src'],
             binaries=[],
             datas=[('D:\\PyCharmProjects\\YANOM-Note-O-Matic\\venv\\Lib\\site-packages\\pyfiglet', 'pyfiglet')],
             hiddenimports=hidden_imports_pandas,
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='yanom',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
