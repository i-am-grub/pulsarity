# PropHazard
A demonstrator project for a RotorHazard variant

> [!WARNING]  
> This project is currently in a development only stage. Do not attempt to use it
> in a deployment setting.

## Development

The development of this project currently relies on python 3.11+ due to new features that were introduced
in this specific version. With python 3.11 being shipped with the release of Debian bookworm
(the preferred operating system for running this project), this constraint is currently accepted.
In the future, a rework may occur to allow for all currently supported versions of pythons.

### Poetry

Poetry is currently used to manage the python dependencies of the project. You can
install it using `pipx` or `pip`

```
pipx install poetry
```

> ***Optional***: Configure Poetry to setup a new venv in the project's root
> directory for you on install. (The follow command sets it for Poetry globally)
> ```
> poetry config virtualenvs.in-project true
> ```

After installing poetry, you can proceed to install the required dependencies using

```
poetry install
```

If you want to install the development requirements, use the following instead

```
poetry install --with dev
```


### Utilites

A few different utilites are used to help the development process. If contributing, 
please follow any guidelines/practices recommended by the following projects:

- poetry - dependency management
- mypy - static type checking
- Black - code formating
- pytest - unit testing
- pytest-cov - coverage testing
- sphinx - documentation

## Starting the Webserver

To start the webserver use

```
python -m prophazard
```