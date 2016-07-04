from setuptools import setup

setup(name='pixiedust',
      version='0.11',
      description='Misc helpers for Spark Python Notebook',
      url='https://github.com/ibm-cds-labs/pixiedust',
      install_requires=['maven-artifact'],
      author='David Taieb',
      author_email='david_taieb@us.ibm.com',
      license='Apache 2.0',
      packages=['pixiedust','pixiedust.packageManager','pixiedust.display',
            'pixiedust.display.table','pixiedust.display.graph','pixiedust.display.chart'],
      zip_safe=False)