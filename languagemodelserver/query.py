#!/usr/bin/env python
from __future__ import print_function
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from ngram import Ngram, db


engine = create_engine('sqlite:////tmp/teste.db')

print("Opening session handle on database...")
Session = sessionmaker(bind=engine)
s = Session()

print("Creating tables in database...")
db.create_all()

print("Running ngram query for ALL ngrams...")
ngrams = Ngram.query.all()
print(ngrams)
for n in ngrams:
    print(n)
