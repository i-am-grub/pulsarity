# Pulsarity

> [!CAUTION]  
> This project is currently in an early development stage; it is not currently usable to any degree.

A race timing and event management application inspired by RotorHazard. This project varies from RotorHazard
in a few ways, but the primary difference being the use of the python native asyncio framework instead of
the use of gevent to enable concurrency. This allows the use of optimizations and peformance boosts
in newer python versions and other features that the use of gevent (specifically the underly greenlet
package) prevents usage of.

## Development

The development of this project currently relies on python 3.14 due to new ensuring compatibility 
with the freethreading capabilities in that version. Depending on the release schedule of this
project, the project may be backported to support eariler versions of python to be compatible with
the python version being shipped with the current release of Debian (Raspbian) at the time of the
release.

### UV Environment

The project currently uses the [uv package manager](https://docs.astral.sh/uv/). With uv installed
as a command line tool, the standard and development dependencies can be installed with running the
following command at the root of the repo

```
uv sync
```

To start the default webserver, use

```
uv run pulsarity
```

### Venv and Pip Environment

The standard venv and pip packages can be used as well. Install your python virtual environment at the
root of the repo and use the following command to install the dependencies and an editable version of
the project into the virtual environment

```
python -m pip install -e .
```

To start the default webserver, use

```
python -m pulsarity
```

### Utilites

A few different utilites are used to help the development process.

- uv - dependency management
- mypy - static type checking
- Black - code formating
- pytest - unit testing
- pytest-cov - coverage testing
- pylint - more static type analysis/linting
- sphinx - documentation
