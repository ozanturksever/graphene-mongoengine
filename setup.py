from setuptools import find_packages, setup

setup(
    name='graphene-mongoengine',
    version='0.1',

    description='Graphene Mongoengine integration',
    long_description=open('README.md').read(),

    url='https://github.com/ozanturksever/graphene-mongoengine',

    author='Ozan Turksever',
    author_email='ozan.turksever@gmail.com',

    license='MIT',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    keywords='api graphql protocol rest relay graphene',

    packages=find_packages(exclude=['tests']),

    install_requires=[
        'six>=1.10.0',
        'graphene>=1.0',
        'mongoengine>=0.10.6'
        'iso8601',
        'singledispatch>=3.4.0.3',
    ],
    tests_require=[
        'pytest',
        'mock',
    ],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
)
