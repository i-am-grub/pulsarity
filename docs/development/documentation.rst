Building the documentation
===================================

Eventually, this project will be setup with automatic builds of
the documentation with Read the Docs. In the time being, building
the documentation is slightly a manual process. 

Install PropHazard with the ``docs`` dependencies::

    poetry install --with docs

To build the html files, run the following from the root directory
of the project::

    poetry run sphinx-build -b html docs docs/_build

The html docs will now be avaliable in ``docs/_build``
