#!/bin/bash

# Generates ngram counts for partial corpus.
# Assumes partial corpus is present, and SRILM is installed.

# Ensure 'ngram-count' is installed (requires SRILM)
if ! type -P ngram-count &> /dev/null; then
    cat <<MSG
Command 'ngram-count' not found.
The SRILM toolset is not installed, or is not 
present in your PATH. See this page to install SRILM:

http://www.speech.sri.com/projects/srilm/download.html

Exiting...
MSG
    exit 1;
fi

python manage.py syncdb --noinput
python manage.py downloadCorpora
python manage.py prepareCorpora
python manage.py importNgrams

exit 0
