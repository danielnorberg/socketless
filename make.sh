#!/bin/sh
find . -type f -name "*.c" -exec rm {} \;
find . -type f -name "*.so" -exec rm {} \;
python setup.py build_ext --inplace
