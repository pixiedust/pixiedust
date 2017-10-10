#!/bin/bash
if [ -z "${PIXIEDUST_EGG}" ]; then
    echo installing from PYPI
    pip install --upgrade pixiedust
else
    echo install from ${PIXIEDUST_EGG}
    pip install --exists-action=w -e ${PIXIEDUST_EGG}
fi    

jupyter pixiegateway --ip 0.0.0.0 --port 8888
