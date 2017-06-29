#!/bin/bash

source .virtualenv/bin/activate
cd src
./manage.py addreceipts >> ../log/receipts.log 2>&1
