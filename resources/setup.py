"""
Setup script for TrackTidy
"""
from setuptools import setup, find_packages

setup(
    name="tracktidy",
    version="0.1.0",
    author="Eddie",
    description="Music Manager for DJs and Music Enthusiasts",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7",
    install_requires=[
        "rich",
        "mutagen",
        "spotipy",
        "requests",
    ],
    entry_points={
        "console_scripts": [
            "tracktidy=tracktidy.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
