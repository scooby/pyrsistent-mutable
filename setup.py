from setuptools import setup

with open('README.rst') as fh:
    long_descr = fh.read()

setup(
    name='pyrsistent-mutable',
    version='0.0.6',
    author='Ben Samuel',
    packages=['pyrsistent_mutable'],
    description='Decorator to create and update immutable values with imperative syntax.',
    long_description=long_descr,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ], python_requires='>=2.6',
    install_requires=[
        'pyrsistent', 'astunparse', 'six'
    ], license='MIT',
    extras_require={},
    tests_require=['pytest', 'mock'],
    zip_safe=True,
    url='https://github.com/scooby/pyrsistent-mutable'
)
