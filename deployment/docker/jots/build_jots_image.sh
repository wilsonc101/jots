#! /bin/bash

JOTS_PATH=$1
TAR_OUTFILE=$2

tar -cvf $TAR_OUTFILE -C $JOTS_PATH runserv.py
tar --append -f $TAR_OUTFILE -C $JOTS_PATH requirements.txt
tar --append -f $TAR_OUTFILE -C $JOTS_PATH __init__.py
tar --append -f $TAR_OUTFILE -C $JOTS_PATH mailer
tar --append -f $TAR_OUTFILE -C $JOTS_PATH pyauth
tar --append -f $TAR_OUTFILE -C $JOTS_PATH webapp


