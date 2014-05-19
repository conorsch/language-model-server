#!/usr/bin/env python
from __future__ import print_function
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from flask import Flask
app = Flask(__name__)

import ngram


testlm = 'output-counts/cna_tokenized_lower.lm'

dbpath = 'sqlite:////tmp/teste.db'
engine = create_engine(dbpath)
Base = declarative_base(bind=engine)

@app.route("/")
def hello():
    return "Hello World!"

if __name__ == "__main__":
    app.run()
