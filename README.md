# PropHazard
A demonstrator project for a RotorHazard variant

## Development

The development of this project currently relies on python 3.11+ due to new features that were introduced
in this specific version. With python 3.11 being shipped with the release of Debian bookworm
(the preferred operating system for running this project), this constraint is currently accepted.
In the future, a rework may occur to allow for all currently supported versions of pythons.

### Poetry

Poetry is currently used to manage the python dependencies of the project. If not already installed
on your system, you can install it using `pipx`

```
pipx install poetry
```

After installing poetry, you can install the current dependencies using

```
poetry install
```