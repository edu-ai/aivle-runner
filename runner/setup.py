from setuptools import setup, find_packages

setup(name='runner',
    version='0.0.1',
    author="Muhammad Rizki Aulia Rahman Maulana",
    author_email="rizki@rizkiarm.com",
    install_requires=['gym', 'numpy', 'sklearn'],
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "runner=runner.__main__:main",
        ],
    },
)