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
installed as a command line tool, the standard _and_ development
dependencies can be installed with running the following
command in the root of the repo:

```
uv sync
```

> [!NOTE] 
> This automatially installs the basic dependencies needed to
> run the application as well as the development dependencies 
> located under the `dev` dependency group found in the 
> `pyproject.toml` file.

> [!NOTE] 
> Additional extra dependencies or dependency groups can also be 
> install by either including the `--extra` or `--group` arguments.
> 
> E.g. To install the `pgsql` extra dependencies, append `--extra pgsql`
>
> E.g. To install the `docs` dependency group, append `--group docs`

To start the default webserver, the following command can
be used:

```
uv run pulsarity
```

### Venv and Pip Environment

The standard venv and pip packages can be used as well, but
do not provide automatially install the additional dependencies
recommended to have installed during development.
Install your python virtual environment at the root of
the repo and use the following command to install the
dependencies and an editable version of the project into
the virtual environment:

```
python -m pip install . -e
```

> [!Note] 
> This only installs the basic dependencies needed to
> run the application.

To install the the application with the `pgsql` extra dependency,
use the following command instead:

```
python -m pip install .[pgsql] -e
```

To start the default webserver, the following command can
be used:

```
python -m pulsarity
```
