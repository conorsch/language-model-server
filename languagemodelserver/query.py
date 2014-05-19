#!/usr/bin/env python
from __future__ import print_function
import sys

from ngram import Ngram, db


print("Creating tables in database...")
db.create_all()

print("Running ngram query for ALL ngrams...")
ngrams = Ngram.query.all()
print(ngrams)
for n in ngrams:
    print(n)
