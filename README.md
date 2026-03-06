# Pulsarity

> [!CAUTION]  
> This project is currently in early development -
> it is not a usable appication at this point in time.

A race timing and event management application inspired
by RotorHazard. This project varies from RotorHazard
in a few ways, but the primary difference being the use
of the python native asyncio framework to enable concurrency
instead of relying on the third party gevent package. This
allows for the use of optimizations and peformance 
improvements in newer python versions and other features 
that the use of gevent (specifically the underlying greenlet 
package) prevents usage of.

## Development

The development of this project currently relies on python
3.14 due to ensuring compatibility with the freethreading
capabilities officially introduced in the 3.14 release.
Depending on the initial release schedule of this project,
an official backport of the codecase to support eariler
versions of python may be created to support compatible
with the default python version being shipped with the
current release of Debian.

### UV Environment

The project currently uses the
[uv project manager](https://docs.astral.sh/uv/). With uv
installed as a command line tool, the standard and development
dependencies can be installed with running the following
command in the root of the repo:

```
uv sync
```

To start the default webserver, the following command can
be used:

```
uv run pulsarity
```

### Venv and Pip Environment

The standard venv and pip packages can be used as well.
Install your python virtual environment at the root of
the repo and use the following command to install the
dependencies and an editable version of the project into
the virtual environment:

```
python -m pip install -e .
```

To start the default webserver, the following command can
be used:

```
python -m pulsarity
```
