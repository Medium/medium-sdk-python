from distutils.core import setup
setup(
    name='medium',
    packages=['medium'],
    install_requires=['requests', 'keyring', 'typer'],
    entry_points={'console_scripts': ['medium=medium.cli:app']},
    version='0.3.0',
    description='SDK for working with the Medium API',
    author='Kyle Hardgrave',
    author_email='kyle@medium.com',
    url='https://github.com/Medium/medium-sdk-python',
    download_url='https://github.com/Medium/medium-sdk-python/tarball/v0.3.0',
    keywords=['medium', 'sdk', 'oauth', 'api', 'cli'],
    classifiers=[],
)
