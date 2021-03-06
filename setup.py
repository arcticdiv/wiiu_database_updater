from setuptools import setup, find_packages


def read(filename):
    try:
        with open(filename, 'r') as f:
            return f.read()
    except IOError:
        return ''


setup(
    name='wiiu_database_updater',
    version='0.0.1',
    description='Updates the .json database files used by Wii U USB Helper',
    long_description=read('README.md'),
    author='arcticdiv',
    url='https://github.com/arcticdiv/wiiu_database_updater',
    license='Apache 2.0',
    packages=find_packages(),
    install_requires=read('requirements.txt').splitlines(),
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Utilities'
    ]
)
