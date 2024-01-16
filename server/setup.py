from setuptools import setup, find_packages


setup(
    name='QRServer',
    version='1.1.0',
    author='Fruktus, Kamil Jarosz',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    python_requires='>=3.8',
    install_requires=[
        'dataclasses',
        'toml',
    ],
    extras_require={
        'dev': [
            'wheel',
            'pytest',
            'flake8',
        ],
    },
)
