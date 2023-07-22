#! /bin/sh

HOME=../Src

MODULE=${HOME}/S2ImageDownloader.py

cd ${HOME}
python ${MODULE} B1 60 2020-01-01 2020-12-31
python ${MODULE} B2 10 2020-01-01 2020-12-31
python ${MODULE} B3 10 2020-01-01 2020-12-31
python ${MODULE} B4 10 2020-01-01 2020-12-31

exit 0
