#!/bin/bash

pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`
popd > /dev/null


~/.zerynth2/sys/python/bin/python -m unittest $SCRIPTPATH/tests/runner.py "$@"
