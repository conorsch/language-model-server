#!/bin/zsh

#$ -o /dev/null
#$ -S /bin/zsh
#$ -j y
#$ -m n
#$ -q all.q
#$ -l h=bragi

# ***
# Description: starts a Trendstream server, looks for and corrects
#     noun-number errors in a POS-tagged, one-sentence-per-line, tokenized
#     text, stops the server, and then evaluates the output and provides
#     evaluation metrics. The input text file can optionally give some extra
#     info., such as whether or not a sentence is a clause (line starts with
#     "CLAUSE" or "NONCLAUSE" followed by a space) and whether or not a noun
#     is a subject (in which case, the noun tag is not the usual "NN"/"NNS").
# ***
# Usage details: ./run_detect_all_nn_errors.sh eval_dir input_file \
#     gold_standard_file morph_comp port_number threshold log_file
#
# Usage example: ./run_detect_all_nn_errors.sh eval_test test.pos \
#     test_all_correct_Nn.txt freeling 9091 0.6 log_test_freeling_0.6
# ***
# Note: NN_ERROR_DIR (your own project directory), SCRATCH (a "scratch"
#    directory that you have write permissions for), and the logging level in
#    the Python script (not in the arguments above) are defined below. The
#    resulting log file will be redirected to NN_ERROR_DIR.
#
# 1) eval_dir: assumed to be the relative path from within NN_ERROR_DIR to the
#    directory you want to use to store the output of the script. For example,
#    if you had a directory called "eval_test" inside your NN_ERROR_DIR, then
#    this argument would be simply "eval_test" (no extra slashes or anything).
# 2 & 3) input_file and gold standard file: must be in EVAL_DIR (the name of
#    the file only).
# 4) morph_comp: must be one of the following, "pckimmo", "freeling",
#    "lingua", or "jedimorph".
# 5) port_number: pick a number >= 0 for the port (usually > 9000)
# 6) threshold: a value >= 0
# 7) log_file: the name of the log that results from the script, which will be
#    stored in NN_ERROR_DIR
# ***

source /home/research/mmulholland/.zshrc

# Get start-time
BEGIN=$(date +"%s")

# Change path to your own ets_noun_number directory
NN_ERROR_DIR=/home/nlp-text/dynamic/mmulholland/conll-shared-task-2013/ets_noun_number

# Change the scratch path to a directory for which you have write permissions
SCRATCH=/home/research/mmulholland/conll_scratch

# Can be "info", "debug", or "warning", depending on how much information
# you want to be included in the Python logging output
LOGGING="debug"

# Change the EVAL_DIR directory to the one where your input/output is going.
# Also, the output of this script will have automatically generated names.
# For example, if you start with an input file called input.pos and you use
# lingua, three files will be generated: input.pos_lingua_output.txt, 
# input.pos_lingua_eval.tsv, and input.pos_lingua_eval_results.tsv.
EVAL_DIR="$NN_ERROR_DIR/$1"
INPUT="$EVAL_DIR/$2"
GOLD_INPUT="$EVAL_DIR/$3"
DETECT_OUT="$EVAL_DIR/$2_$4_output.txt"
EVAL_OUTPUT="$EVAL_DIR/$2_$4_eval.tsv"
EVAL_RES_OUTPUT="$EVAL_DIR/$2_$4_eval_results.tsv"
EVAL_LOG="$EVAL_DIR/log_eval_$4_$6" # Log file for evaluate.py script output
LOGFILE="$NN_ERROR_DIR/$7" # Log file for detect_nn_errors.py script output
ERROR_LOG="$NN_ERROR_DIR/log_detect_$4_$6" # Log file for recording output
	# from unexpected exits

# Start the TrendStream server on the given port (it might already be
# running)
$NN_ERROR_DIR/start_ts_server.sh $5 &
PID=$! # Store process-id for the start_ts_server.sh process just started

# Give it some time to connect and then find out if the process is still
# running (it should've stopped by now if it were not going to complete).
# If the process is not running, print error message and exit.
sleep 30s
PROC=`ps | grep $PID | wc -l`

if [[ $PROC -eq 0 ]]; then

echo "Unable to get server running on port $5. Exiting." &>! $ERROR_LOG
exit

fi

# Run the detect_nn_errors.py script with the given morphological
# component, input file, threshold level, and logging level and output to
# the given $LOGFILE. If the given morphological component is not
# recognized, print error message and exit.
if [[ "$4" == "pckimmo" ]]; then

python3.3 $NN_ERROR_DIR/detect_nn_errors.py -i $INPUT -o $DETECT_OUT --morph pckimmo -p $5 --threshold $6 --scratch $SCRATCH --log_level $LOGGING &>! $LOGFILE

elif [[ "$4" == "freeling" ]]; then

python3.3 $NN_ERROR_DIR/detect_nn_errors.py -i $INPUT -o $DETECT_OUT --morph freeling -p $5 --threshold $6 --log_level $LOGGING &>! $LOGFILE

elif [[ "$4" == "lingua" ]]; then

python3.3 $NN_ERROR_DIR/detect_nn_errors.py -i $INPUT -o $DETECT_OUT --morph lingua -p $5 --threshold $6 --log_level $LOGGING &>! $LOGFILE

elif [[ "$4" == "jedimorph" ]]; then

python3.3 $NN_ERROR_DIR/detect_nn_errors.py -i $INPUT -o $DETECT_OUT --morph jedimorph -p $5 --threshold $6 --log_level $LOGGING &>! $LOGFILE

else

echo "The morphological component in argument 4, $4, did not match any of the valid morphological components, including \"pckimmo\", \"freeling\", \"lingua\", and \"jedimorph\". Please try again." &>! $ERROR_LOG

# Try to kill the server before exiting (not sure if it's going to work
# -- or it might only work if being run on the grid engine and not
# locally...)
(kill -9 $PID &>> $NN_ERROR_DIR/log_ts_server && echo "\n\n$(date +"%c"): Killed server manually on port $5." &>> $NN_ERROR_DIR/log_ts_server) || $NN_ERROR_DIR/stop_ts_server.sh $5
exit

fi

# Try to kill the server (not sure if it's going to work -- or it might
# only work if being run on the grid engine and not locally...)
(kill -9 $PID &>> $NN_ERROR_DIR/log_ts_server && echo "\n\n$(date +"%c"): Killed server manually on port $5." &>> $NN_ERROR_DIR/log_ts_server) || $NN_ERROR_DIR/stop_ts_server.sh $5

# Do evaluation of output file with given gold standard file
python2 $NN_ERROR_DIR/evaluate.py -g $GOLD_INPUT -o $INPUT -s $DETECT_OUT -out $EVAL_OUTPUT -res $EVAL_RES_OUTPUT &>! $EVAL_LOG

# Get end-time and calculate the total amount of time, appending the
# total in hours and minutes to $LOGFILE
END=$(date +"%s")
TIME=`expr $END - $BEGIN`
HOURS=`expr $TIME / 3600`
SECONDS=`expr $TIME % 3600`
MINUTES=`expr $SECONDS / 60`
echo "\n\nTotal time = $HOURS hours and $MINUTES minutes" &>> $LOGFILE