from setuptools import setup

with open('README.md') as fh:
    long_descr = fh.read()

setup(
    name='pyrsistent-mutable',
    version='0.0.4',
    author='Ben Samuel',
    packages=['pyrsistent_mutable'],
    description='Decorator to create and update immutable values with imperative syntax.',
    long_description=long_descr,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ], python_requires='~=3.4',
    install_requires=[
        'pyrsistent', 'astunparse'
    ], license='MIT',
    extras_require={
    }, zip_safe=True,
    url='https://github.com/scooby/pyrsistent-mutable'
)
