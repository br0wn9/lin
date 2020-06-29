import os

from setuptools import find_packages, setup

from lin.version import __VERSION__

# We use the README as the long_description
readme_path = os.path.join(os.path.dirname(__file__), "README.rst")
with open(readme_path) as fp:
    long_description = fp.read()

setup(
    name="lin",
    version="{}.{}.{}".format(*__VERSION__),
    url="https://github.com/br0wn9/lin",
    author="Brown Guan",
    author_email="br0acwn@gmail.com",
    description="HTTP Web Server",
    long_description=long_description,
    license="BSD",
    zip_safe=False,
    packages=find_packages(exclude=['examples', 'tests']),
    include_package_data=True,
    entry_points={
        "console_scripts": ["lin = lin.cli:CommandInterface.entrypoint"]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Server",
    ],
)
