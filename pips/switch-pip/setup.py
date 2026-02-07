from setuptools import setup, find_packages

setup(
    name="switch-pip",
    version="1.0.0",
    description="Switch pip index-url easily. Use custom mirrors or reset to PyPI.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="switch-pip",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "switch-pip=switch_pip.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Environment :: Console",
    ],
)
