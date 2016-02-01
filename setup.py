from setuptools import setup


setup(
    name='momo',
    version='0.1.0',
    description="Tiny CLI file manager",
    long_description=open('README.md').read(),
    keywords='momo files',
    author='Shichao An',
    author_email='shichao.an@nyu.edu',
    url='https://github.com/shichao-an/momo',
    license='BSD',
    install_requires=open('requirements.txt').read().splitlines(),
    py_modules=['momo'],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'momo = momo:main',
        ],
    },
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
)
