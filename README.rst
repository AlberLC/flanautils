FlanaUtils
==========

|license| |project_version| |python_version|

Set of utilities of all kinds to develop python projects.

|

Installation
------------

Python 3.10 or higher is required.

.. code-block::

    pip install flanautils

|

Features
--------

Data structures
~~~~~~~~~~~~~~~

- BiDict:
    Dictionary that saves references in both directions to access constantly by hashes both :code:`key -> value` and :code:`key <- vaue`. To achieve this, a copy of the dictionary is used but inverted.

- OrderedSet:
    A set that maintains the insertion order and implements all the methods of set and list, although since it is a structure based on hashes the traversal of all the elements and the use of Sequence-based functions (tuple, list, etc.) aren't efficient.

Models
~~~~~~
- Base class for serialize to bytes
- Base class for serialize to dict
- Base class for serialize to json
- Base class for calculate mean of objects
- Base class that acts as a object-document mapper (ODM)
- Base class for enums
- Plotly classes
- etc.

Functions
~~~~~~~~~

- Asyncs utils like :code:`do_later(...)`, :code:`do_every(...)`, etc.
- Decorators
- Exceptions
- Iterable utils like smart :code:`filter(...)`, :code:`find(...)`, :code:`flattn_iterator(...)`, :code:`frange(...)`, etc.
- Operating system utils like :code:`resolve_path(...)`, :code:`suppress_stderr(...)`, etc.
- Strings utils like :code:`cartesian_product_string_matching(...)`, :code:`join_last_separator(...)`, :code:`translate(...)`, :code:`words_to_numbers(...)`, etc.


.. |license| image:: https://img.shields.io/github/license/AlberLC/flanautils?style=flat
    :target: https://github.com/AlberLC/flanautils/blob/main/LICENSE
    :alt: License

.. |project_version| image:: https://img.shields.io/pypi/v/flanautils
    :target: https://pypi.org/project/flanautils/
    :alt: PyPI

.. |python_version| image:: https://img.shields.io/pypi/pyversions/flanautils
    :target: https://www.python.org/downloads/
    :alt: PyPI - Python Version