# -*- mode: python -*-

block_cipher = None
VERSION = '0.4.0'

a = Analysis(['v2net.py'],
             pathex=['/Users/Jia/Dropbox/Projects/v2net'],
             binaries=[],
             datas=[('profile', 'profile'), ('extension', 'extension'), ('icon.png', '.')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='v2net',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='v2net')
app = BUNDLE(coll,
             name='V2Net.app',
             icon='icon.icns',
             bundle_identifier='com.boshuwan.V2Net',
             info_plist={
             'CFBundleName': 'V2Net',
             'CFBundleDisplayName': 'V2Net',
             'LSUIElement': 'True',
             'NSHighResolutionCapable': 'True',
             'CFBundleVersion': VERSION,
             'CFBundleShortVersionString': VERSION
             },)
