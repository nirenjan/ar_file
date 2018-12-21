import setuptools

with open("README.rst", "r") as fp:
    long_description = fp.read()

setuptools.setup(
    name="ar_file",
    version="0.0.1",
    author="Nirenjan Krishnan",
    author_email="nirenjan@gmail.com",
    description="Unix archive file library",
    long_description=long_description,
    url="https://github.com/nirenjan/ar_file",
    packages=setuptools.find_packages(),
    classifiers=[
      "Programming Language :: Python",
      "License :: OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
      "Operating System :: OS Independent"
    ]
)
