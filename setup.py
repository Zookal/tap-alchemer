#!/usr/bin/env python
from setuptools import setup

#https://dzone.com/articles/executable-package-pip-install

setup(
    name="tap-alchemer",
    version="0.0.0",
    description="Singer.io tap for extracting Alchemer survey data",
    author="Adilson",
    url="http://github.com/Zookal/tap-alchemer",
    classifiers=["Programming Language :: Python :: 3 :: Only"],
    py_modules=["tap_alchemer"],
    install_requires=[
        "singer-python==5.12.2",
        "requests==2.27.1",
        "pendulum==2.1.2"
    ],
    extras_require={
        'dev': [
            'pylint',
            'ipdb',
            'requests==2.27.1',
            'nose',
        ]
    },
    entry_points="""
    [console_scripts]
    tap-alchemer=tap_alchemer:main
    """,
    packages=["tap_alchemer"],
    package_data = {
        "tap_alchemer": ["schemas/*.json"]
    },
    include_package_data=True,
)
