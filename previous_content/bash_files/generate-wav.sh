# Capture git directory 
START_DIR=$(dirname "$(pwd)")
echo "Starting in: $START_DIR"
YOBE_SDK="$HOME/YobeSDK-Release-GrandE-0.6.2-Linux"
echo "This path is $YOBE_SDK "

# Retrieve time stamp (MM_DD_HH_MM)
TIMESTAMP=$(date +"%m_%d_%H_%M")
RAW_OUTPUT="${TIMESTAMP}_output"

# Start 3 sec timer
DEMO_START=$(date +%s.%N)
# Start timer
START_TIME=$(date +%s.%N)

# Start total latency timer
TOTAL_START=$(date +%s.%N)
# This creates a .wav file in the specified location
cd  ~/YobeSDK-Release-GrandE-0.6.2-Linux/samples

SAMPLE_RATE=16000
CHANNELS=2
FORMAT="s16"
BUFFER_SIZE=16000	# Must match size used in Yobe SDK

# **** Adding in support for Pipewire audio streaming *** #
# build ... broadside/endfire
cmake --build "$YOBE_SDK/samples/build" # New pi or if changing the C++ file

# Rebuild audio processor into an executable
g++ -o audio_stream_processor audio_stream_processor.cpp
pw-record --rate $SAMPLE_RATE --channels $CHANNELS --format $FORMAT "${RAW_OUTPUT}.wav" | ./audio_stream_processor | ./build/IDListener_demo broadside target-speaker "student-pc" ./build

# SOMEHOW GOAL IS TO PIPE THIS DIRECTLY TO YOBE SINCE WE SURPASS THE NORMALIZING STEP

# TODO: ADD ELIF TO CHECK IF RUNNING BROADSIDE/ENDFIRE
# mv old_filename new_filename
mv "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}_broadside_processed.wav" "$YOBE_SDK/samples/audio_files/IDListener/${TIMESTAMP}_processed.wav"
# Hardcoded Broadside for now
"$START_DIR/Audio/normalize_raw" "$YOBE_SDK/samples/audio_files/IDListener/${TIMESTAMP}_processed.wav" "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}_broadside_processed.wav"
mv "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}_broadside_processed.wav" "$START_DIR/Transcripts/Audio_wav/${TIMESTAMP}_broadside.wav"
# Output file name is TIMESTAMP_{broadfire/endfire}.wav; which is processed and normalized

# Calling Google ASR on normalized Yobe output file
# We need to do this within a virtual environment
ASR_START=$(date +%s.%N)
source ~/gcloudenv/bin/activate
python ~/gcloudenv/googleTabulate.py "$START_DIR/Transcripts/Audio_wav/${TIMESTAMP}_broadside.wav" > "$START_DIR/Transcripts/Output_ASR/${TIMESTAMP}_ASR.txt"
deactivate

# ASR Latency
ASR_END=$(date +%s.%N)
ASR_DURATION=$(echo "$ASR_END - $ASR_START" | bc)
echo "Google ASR duration: ${ASR_DURATION} seconds"


###################################
# Andrew + Suhani's implementation
# source $START_DIR/.venv/bin/activate
# python3  $START_DIR/database/cloud_sql_generation.py "$START_DIR/Transcripts/Output_ASR/${TIMESTAMP}_ASR.txt" "$START_DIR/Transcripts/Output_Cloud_LLM/${TIMESTAMP}_Cloud_LLM.txt" "$START_DIR/database/OpenAI_Integration/api_key.json"
# deactivate
###################################

LLM_TIMER=$(date +%s.%N)
#####################################
# Noa + Jackie's implementation; Change to dynamic file
source ~/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/venv/bin/activate
python3 $START_DIR/Audio/OpenAItesting.py "$START_DIR/Transcripts/Output_ASR/${TIMESTAMP}_ASR.txt" "$START_DIR/Transcripts/Output_LLM/${TIMESTAMP}_LLM.txt" "$START_DIR/database/OpenAI_Integration/api_key.json"
deactivate
#####################################
LLM_TIMER_END=$(date +%s.%N)
LLM_DUR=$(echo "$LLM_TIMER_END - $LLM_TIMER" | bc)
echo "LLM Time: ${LLM_DUR} seconds"

# End timer
END_TIME=$(date +%s.%N)
ELAPSED_TIME=$(echo "$END_TIME - $START_TIME" | bc)
echo "Elapsed time: ${ELAPSED_TIME} seconds"

#####################################
# D-ID (Digital Human Video generation)
# source $START_DIR/.venv/bin/activate
# python3 $START_DIR/D-iD/didVideoOutput.py "$START_DIR/database/OpenAI_Integration/api_key.json" "$START_DIR/Transcripts/Output_LLM/${TIMESTAMP}_LLM.txt" "$START_DIR/Transcripts/Vid_link/${TIMESTAMP}_video.txt"
# deactivate
#####################################


# Calculate total elapsed time
TOTAL_END=$(date +%s.%N)
TOTAL_DURATION=$(echo "$TOTAL_END - $TOTAL_START" | bc)
echo "Total script duration: ${TOTAL_DURATION} seconds"

# Cleanup
# rm "$START_DIR/Audio/normalize_raw"
# rm "$YOBE_SDK/samples/audio_files/IDListener/${TIMESTAMP}_processed.wav"
# rm "$YOBE_SDK/samples/audio_files/IDListener/${RAW_OUTPUT}.wav"
# rm "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}.wav"
