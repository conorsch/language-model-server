language-model-server
=====================

Inspired by ([Madnani, 2009]), this project tries to implement a queryable server for an English language model of variable n-gram order. 

![Ngram detail view screenshot](https://raw.githubusercontent.com/ronocdh/language-model-server/rest-api-docs/docs/img/ngram-single-view.png "Optional title")

Requirements
------------
 - [SRILM] toolkit
 - [nltk]

Installation
--------------
The most complicated aspect of the installation will be compiling [SRILM]. 
Once you have that toolkit downloaded and added to your $PATH, run these commands:

 1. ```pip install --user -r requirements.txt``` to install Python dependencies.
 2. ```./bootstrap.sh``` to build LM and load database
 3. ```python manage.py runserver [::]:8000``` to run the API server for ngram queries

Step 2 above can take a few minutes, depending on hardware.
Using a batch size of 1000 per database commit:

```
$ time ./bootstrap.sh

Creating tables ...
Installing custom SQL ...
Installing indexes ...
Installed 0 object(s) from 0 fixture(s)
Generating countfile from corpus 8/8 ('combined')...            
Building language model (/home/conor/gits/language-model-server/corpus/nltk-combined.lm)... done.
Number of 1-grams committed to database: 223000
Number of 2-grams committed to database: 1795000
Number of 3-grams committed to database: 445000
Number of 4-grams committed to database: 287000
Number of 5-grams committed to database: 176000
Finished loading database.

real    2m36.424s
user    2m31.558s
sys     0m3.919s
```

[Madnani, 2009]:http://ojs.pythonpapers.org/index.php/tppsc/article/view/83
[SRILM]:http://www.speech.sri.com/projects/srilm/download.html
[nltk]:http://www.nltk.org/

TODO
----
 - expand API with params for querying
 - write tests (damn it)
 - investigate open source LMs
   - kenLM for ngramModel?
