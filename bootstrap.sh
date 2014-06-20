#!/bin/bash

# Generates ngram counts for partial corpus.
# Assumes partial corpus is present, and SRILM is installed.

python manage.py syncdb --noinput && \
python manage.py downloadCorpora
python manage.py prepareCorpora && \
python manage.py importNgrams
exit 0
