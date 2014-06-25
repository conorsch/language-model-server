#!/bin/bash

# Generates ngram counts for partial corpus.
# Assumes partial corpus is present, and SRILM is installed.

MANAGEPY="$(dirname $0)/manage.py"

python $MANAGEPY syncdb --noinput && \
python $MANAGEPY downloadCorpora && \
python $MANAGEPY prepareCorpora && \
python $MANAGEPY importNgrams

exit 0
