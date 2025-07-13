# Pulsarity

> [!CAUTION]  
> This project is currently in an early development stage; it is not currently usable to any degree.

A race timing and event management application inspired by RotorHazard. This project varies from RotorHazard
in a few ways, but the primary difference being the use of the python native asyncio framework instead of
the use of gevent to enable concurrency. This allows the use of optimizations and peformance boosts
in newer python versions and other features that the use of gevent (specifically the underly greenlet
package) prevents usage of.

## Development

The development of this project currently relies on python 3.11+ due to new features that were introduced
in this specific version. With python 3.11 being shipped with the release of Debian bookworm
(the preferred operating system for running this project), this constraint is currently accepted.
In the future, a rework may occur to allow for all currently supported versions of pythons.

### Utilites

A few different utilites are used to help the development process. If contributing, 
please follow any guidelines/practices recommended by the following projects:

- uv - dependency management
- mypy - static type checking
- Black - code formating
- pytest - unit testing
- pytest-cov - coverage testing
- pylint - more static type analysis
- tox - automated testing
- sphinx - documentation
