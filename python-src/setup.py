from distutils.core import setup

setup(
    name='moosync-ext',
    version='1.0',
    packages=["moosyncLib"],
    py_modules=[""],
    scripts=["main.py"],
    install_requires=["Brotli==1.1.0", "certifi==2023.7.22", "mutagen==1.47.0", "pex==2.1.148", "pycryptodomex==3.19.0", "websockets==12.0", "yt-dlp==2023.10.13", ""]
)
