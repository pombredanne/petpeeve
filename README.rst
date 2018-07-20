===============================================
Pet Peeve: Resolution and installation toolset.
===============================================

Pet Peeve (PP onwards) is a tool to perform two operations:

* Dependency resolution
* Dependency installation

Being standlone, PP is designed to be injected into an isolated environment,
like this::

    PYTHONPATH=$PYTHONPATH:/path/to/src python -m petpeeve

It is therefore designed to require as little dependencies as possible. It
only depends on `pip` and `wheel`, both essential in modern Python executable
contexts, especially virtual environments. pip>=8.1.0 is supported.
