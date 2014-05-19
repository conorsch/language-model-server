#!/usr/bin/env python
from __future__ import print_function
import sys

from ngram import Ngram, db, app


@app.route("/")
def hello():
    return "Hello World!"

@app.route("/ngram/<order>")
def getNgramByOrder(order):
    return Ngram.query.first_or_404()

if __name__ == "__main__":
    app.run()
