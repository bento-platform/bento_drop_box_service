#!/usr/bin/env python

import setuptools

with open("README.md", "r") as rf:
    long_description = rf.read()

setuptools.setup(
    name="chord_drop_box_service",
    version="0.2.0",

    python_requires=">=3.6",
    install_requires=[
        "chord_lib[flask]==0.5.0",
        "Flask>=1.1,<2.0",
        "boto3>=1.12.7,<1.13"
    ],

    author="David Lougheed",
    author_email="david.lougheed@mail.mcgill.ca",

    description="Drop box and basic file management service for the CHORD project.",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=setuptools.find_packages(),
    include_package_data=True,

    url="https://github.com/c3g/chord_drop_box_service",
    license="LGPLv3",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent"
    ]
)
