from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="tracktidy",
    version="0.1.0",
    author="Eddie",
    description="An all-in-one music manager for DJs and music enthusiasts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/tracktidy",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "tracktidy=tracktidy:main",
        ],
    },
)
