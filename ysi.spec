# -*- mode: python -*-

block_cipher = None


a = Analysis(['bin/ysi'],
             pathex=['/home/debian/Desktop/research/git/ysi-core'],
             binaries=[],
             datas=[],
             hiddenimports=['_scrypt', 'ysi_client.backend.drivers.disk', 'ysi_client.backend.drivers.ysi_resolver', 'ysi_client.backend.drivers.ysi_server', 'ysi_client.backend.drivers.dht', 'ysi_client.backend.drivers.dropbox', 'ysi_client.backend.drivers.gdrive', 'ysi_client.backend.drivers.http', 'ysi_client.backend.drivers.onedrive', 'ysi_client.backend.drivers.s3'],
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
          name='ysi',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='ysi')
