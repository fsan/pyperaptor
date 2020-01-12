from distutils.core import setup
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
  name = 'pyperaptor',
  packages = ['pyperaptor'],
  version = '0.1.3.1',
  license='MIT',
  description = 'Easy multithreading pipeline with Python 3',
  long_description = """
    PypeRaptor is a library that provides a functional pipeline structure.
    Each execution from the pipeline takes an input item from beginning to end and return the result.
    The Pipeline may be modified by add operator and expects a Node.
    To execute a Pipeline for a single item, user can execute **push** function with item. This execution will pushes the input
    through the pipeline calling every function in the way.
    To execute several items, user can set an Iterable in **process** function.

    A generator can be part of the pipeline, and is recommended to be the first item to when using Pipeline in parallel mode.
    When in parallel mode, PypeRaptor provides a Device as in a way to reserve resources and avoid racing conditions among its threads.

    For examples go to:
    http://github.com/fsan/pyperaptor

  """,
  author = 'fsan',
  author_email = "pabyo.sansinaeti@gmail.com",
  url = 'https://github.com/fsan/pyperaptor',
  download_url = 'https://github.com/fsan/pyperaptor/releases/download/0.1.3/pyperaptor-0.1.3.1.tar.gz',
  keywords = ['pipeline', 'dinossaurs', 'threading'],
  install_requires=[
      ],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Topic :: Other/Nonlisted Topic',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
  python_requires='>=3.6',
)
