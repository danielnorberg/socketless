#!/bin/sh
cd $(dirname $0)
source clean-cython.sh
python cython-setup.py build_ext --inplace
find . -type f -name "*.so" -exec rm {} \;
rm -rf build

