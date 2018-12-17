from setuptools import setup, find_packages
setup(name='pixiedust',
      version='1.1.15',
      description='Productivity library for Jupyter Notebook',
      url='https://github.com/pixiedust/pixiedust',
      install_requires=['mpld3', 'lxml', 'geojson', 'astunparse', 'markdown', 'colour', 'requests'],
      author='David Taieb',
      author_email='david_taieb@us.ibm.com',
      license='Apache 2.0',
      packages=find_packages(exclude=('tests', 'tests.*')),
      include_package_data=True,
      zip_safe=False,
      entry_points={
          'console_scripts': [
              'jupyter-pixiedust = install.pixiedustapp:main'
          ]
      }
     )
