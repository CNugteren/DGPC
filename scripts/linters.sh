#!/usr/bin/env sh

pylint src tests --max-line-length=120
mypy src tests
