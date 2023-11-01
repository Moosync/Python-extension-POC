from distutils.core import setup

setup(
    name='moosync-ext',
    version='1.0',
    packages=["moosyncLib"],
    py_modules=[""],
    scripts=["main.py"],
    install_requires=[
        'yt_dlp',
    ],
)
    