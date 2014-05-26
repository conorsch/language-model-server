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
 3. ```./languagemodel/loadlm.py``` to import ngram data into SQLite database.

Steps 2 & 3 above can take 10-20 minutes, depending on hardware.

#### Batteries sold separately
Due to licensing restrictions, you will need to provide the corpora 
yourself. We're working on using fully open corpora in the future.

[Madnani, 2009]:http://ojs.pythonpapers.org/index.php/tppsc/article/view/83
[SRILM]:http://www.speech.sri.com/projects/srilm/download.html
[nltk]:http://www.nltk.org/

