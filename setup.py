#!/usr/bin/env python

import setuptools

with open("README.md", "r") as rf:
    long_description = rf.read()

setuptools.setup(
    name="chord_drop_box_service",
    version="0.1.0",

    python_requires=">=3.6",
    install_requires=["chord_lib @ git+https://github.com/c3g/chord_lib#egg=chord_lib[flask]", "Flask>=1.1,<2.0"],

    author="David Lougheed",
    author_email="david.lougheed@mail.mcgill.ca",

    description="Drop box and basic file management service for the CHORD project.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=["chord_drop_box_service"],
    include_package_data=True,

    url="TODO",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ]
)
