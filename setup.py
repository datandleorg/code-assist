from setuptools import setup, find_packages

setup(
    name='code-assist',
    version='1.0.0',
    description='code assistant',
    author='Saravanan',
    packages=find_packages(),
    install_requires=[],  # Add any dependencies here
    entry_points={
        'console_scripts': [
            'code-assist = src.module:main'
        ]
    }
)