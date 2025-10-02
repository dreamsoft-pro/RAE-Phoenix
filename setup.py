from setuptools import setup, find_packages

setup(
    name="feniks",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'feniks = scripts.apply_recipe:main',
        ],
    },
)
