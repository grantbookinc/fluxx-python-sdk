from distutils.core import setup


version = '0.0.1'
requires = ['requests>=2.12.3']
test_requirements = ['pytest>=2.8.0']


setup(
    name='fluxx_wrapper',
    py_modules=['fluxx_wrapper'],
    version=version,
    description='A simple wrapper around Fluxx GMS\'s REST API.',
    author='Connor Sullivan',
    author_email='sully4792@gmail.com',
    install_requires=requires,
    tests_require=test_requirements,
    url='https://github.com/theconnor/fluxx-python-sdk',
    download_url='https://github.com/theconnor/fluxx-python-sdk/tarball/' + version,
    keywords=['fluxx', 'gms', 'api', 'wrapper'],
    classifiers=[],
)
