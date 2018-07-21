# -*- mode: python -*-

block_cipher = None
VERSION = '0.4.8'

a = Analysis(['v2net.py'],
             pathex=['/Users/Jia/Dropbox/Projects/v2net'],
             binaries=[],
             datas=[('profile', 'profile'), ('extension', 'extension'), ('icon.png', '.'), ('setproxy.sh', '.'), ('setting.ini', '.')],
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
          upx=False,
          console=False,
          icon='icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='v2net')
app = BUNDLE(coll,
             name='V2Net.app',
             icon='icon.icns',
             bundle_identifier='com.boshuwan.V2Net',
             info_plist={
             'CFBundleName': 'V2Net',
             'CFBundleDisplayName': 'V2Net',
             'NSHighResolutionCapable': True,
             'LSUIElement': True,
             'LSBackgroundOnly': True,
             'CFBundleVersion': VERSION,
             'CFBundleShortVersionString': VERSION
             },)
