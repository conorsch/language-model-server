#!/usr/bin/env python
from __future__ import print_function
import sys

from flask import Flask
app = Flask(__name__)

from ngram import Ngram, db


@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
