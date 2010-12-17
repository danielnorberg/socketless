#!/bin/sh
find . -type f -name "*.c" -exec rm {} \;
find . -type f -name "*.so" -exec rm {} \;
find . -type f -name "*.pyc" -exec rm {} \;
rm -rf build
