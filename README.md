language-model-server
=====================

Inspired by ([Madnani, 2009]), this project tries to implement a queryable server for an English language model of variable n-gram order. 

Requirements
------------
 - [SRILM] toolkit
 - [nltk]


Installation
--------------
The most complicated aspect of the installation will be compiling [SRILM]. 
Once you have that toolkit downloaded and added to your $PATH, run the 
```bootstrap.sh``` script to generate n-gram counts needed for the LM. 
Then ```pip install --user -r requirements.txt``` and you're off to the races.

#### Batteries sold separately
Due to licensing restrictions, you will need to provide the corpora 
yourself. We're working on using fully open corpora in the future.

[Madnani, 2009]:http://ojs.pythonpapers.org/index.php/tppsc/article/view/83
[SRILM]:http://www.speech.sri.com/projects/srilm/download.html
[nltk]:http://www.nltk.org/

