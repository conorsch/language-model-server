language-model-server
=====================

Inspired by ([Madnani, 2009]), this project tries to implement a queryable server for an English language model of variable n-gram order. 

Requirements
------------
 - [SRILM] toolkit
 - [nltk]
 - Spiffy linguistic corpora (not included)


Installation
--------------
The most complicated aspect of the installation will be compiling [SRILM]. 
Once you have that toolkit downloaded and added to your $PATH, run these commands:

 1. ```pip install --user -r requirements.txt``` to install Python dependencies.
 2. ```./bootstrap.sh``` to generate n-gram counts needed for the LM. 
 3. ```python manage.py loadNgrams``` to import ngram data into SQLite database (only bigrams right now)

Step 3 above can take a few minutes, depending on hardware. 
Using a batch size of 10000 per database commit:

```
$ time python manage.py importNgrams

Extracting ngram args from flat file...
Inserting ngrams into database...
Found start of 2-grams block...
Number of 2-grams committed to database: 33060000
Finished reading 2-grams block...
Finished loading database.

real    3m48.216s
user    3m44.028s
sys     0m3.522s
```

However, generating fixtures via `dumpdata` takes considerably longer:
```
$ time python manage.py dumpdata --indent=4 > fixtures/2grams.json

real    29m51.253s
user    29m22.105s
sys     0m22.366s
```
Generating them via a custom command is much faster, though:
```
$ time python manage.py generateNgramFixtures 

Generating fixtures from ngrams in database...
Finished generating fixtures.

real    16m6.369s
user    15m47.030s
sys     0m14.472s
```

#### Batteries sold separately
Due to licensing restrictions, you will need to provide the corpora 
yourself. We're working on using fully open corpora in the future.

[Madnani, 2009]:http://ojs.pythonpapers.org/index.php/tppsc/article/view/83
[SRILM]:http://www.speech.sri.com/projects/srilm/download.html
[nltk]:http://www.nltk.org/

