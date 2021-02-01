from setuptools import setup, find_packages

setup(name='pixiedust',
      version='1.1.19',
      description='Productivity library for Jupyter Notebook',
      url='https://github.com/pixiedust/pixiedust',
      author='David Taieb',
      author_email='data38777@gmail.com',
      install_requires=['geojson', 'astunparse', 'markdown', 'colour', 'requests', 'matplotlib',
                        'pandas'],
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
