Building the Documentation Locally
===================================

The following process outlines the process of how
to build the documentation locally.

Install Pulsarity with the ``docs`` dependencies::

    uv sync --group docs

To build the html files, run the following from the root directory
of the project::

    uv run sphinx-build -b html docs docs/_build

The html docs will now be avaliable in ``docs/_build``
