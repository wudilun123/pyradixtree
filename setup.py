from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pyradixtree',
    version='0.0.1',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    url='https://github.com/wudilun123/pyradixtree.git',
    license='MIT',
    author='zhang dapao',
    author_email='wudilun123@gmail.com',
    description='pyradixtree, a python radix tree implementation',
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True,
    python_requires='>=3.8',
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Intended Audience :: Developers',
    ],
)
