#!/bin/sh
cd $(dirname $0)
source clean-cython.sh
python cython-setup.py build_ext --inplace
if [ "$1" != "--leave-so" ]
  then
    find . -type f -name "*.so" -exec rm {} \;
fi
rm -rf build

