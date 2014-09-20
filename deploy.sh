#!/bin/sh -e

ROOT=$(dirname $(readlink -f $0))
cd $ROOT

rsync -av . leon@sachiko.onegeek.org:/home/leon/wsgi.renaius --exclude .git
ssh leon@sachiko.onegeek.org touch /home/leon/wsgi.renaius/main.wsgi
