from setuptools import setup

setup(name='pixiedust',
      version='0.40',
      description='Misc helpers for Spark Python Notebook',
      url='https://github.com/ibm-cds-labs/pixiedust',
      install_requires=['maven-artifact','mpld3'],
      author='David Taieb',
      author_email='david_taieb@us.ibm.com',
      license='Apache 2.0',
      packages=['pixiedust','pixiedust.packageManager','pixiedust.display',
            'pixiedust.display.table','pixiedust.display.graph','pixiedust.display.chart','pixiedust.display.chart.plugins',
            'pixiedust.display.tests','pixiedust.display.download',
            'pixiedust.services',
            'pixiedust.utils'],
      include_package_data=True,
      zip_safe=False)
