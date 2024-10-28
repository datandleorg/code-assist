from setuptools import setup, find_packages

setup(
    name='coder',
    version='1.0.0',
    description='code assistant',
    author='Saravanan',
    packages=find_packages(),
    install_requires=[],  # Add any dependencies here
    entry_points={
        'console_scripts': [
            'coder=codev1.src.module:main'
        ]
    }
)