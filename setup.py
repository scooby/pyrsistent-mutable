from setuptools import setup

setup(
    name='pyrsistent-mutable',
    version='0.0.1',
    author='Ben Samuel',
    packages=['pyrsistent_mutable'],
    description='Import hook to update pysistent values with imperative syntax.',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ], python_requires=['python>=3'],
    install_requires=[
        'pyrsistent',
    ], license='MIT',
    extras_require={
        'debug': ['astunparse'],
    }, zip_safe=True
)
