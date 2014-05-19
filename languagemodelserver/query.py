#!/usr/bin/env python
from __future__ import print_function
import sys

from ngram import Ngram, db

print("Running ngram query for ALL ngrams...")
ngrams = Ngram.query.yield_per(20)
print(ngrams)
for n in ngrams:
    print(n)
