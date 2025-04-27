# Capture git directory 
START_DIR=$(dirname "$(pwd)")
# echo "Starting in: $START_DIR"
YOBE_SDK="$HOME/YobeSDK-Release-GrandE-0.6.2-Linux"
echo "This path is $YOBE_SDK "

# Retrieve time stamp (MM_DD_HH_MM)
TIMESTAMP=$(date +"%m_%d_%H_%M")
RAW_OUTPUT="${TIMESTAMP}_output"


# Start total latency timer
TOTAL_START=$(date +%s.%N)
# This creates a .wav file in the specified location
cd  ~/YobeSDK-Release-GrandE-0.6.2-Linux/samples


SAMPLE_RATE=16000
CHANNELS=2
FORMAT="s16le"
BUFFER_SIZE=32000  # This should match the buffer size used in your C++ code

<<<<<<< HEAD:Audio/generate-wav.sh
pw-record -r $SAMPLE_RATE -c $CHANNELS -f $FORMAT -t raw | ./audio_stream_processor $AUDIO_FILES_PATH $INIT_DATA

# wav -d {number_of_seconds}; 10 seconds right now
# arecord -D plughw:2,0 -f S16_LE -r 16000 -c 2 -t wav -d 10 "$YOBE_SDK/samples/audio_files/IDListener/${RAW_OUTPUT}.wav"
=======
# pw-record -r $SAMPLE_RATE -c $CHANNELS -f $FORMAT -t raw | ./audio_stream_processor $AUDIO_FILES_PATH $INIT_DATA

# wav -d {number_of_seconds}; 10 seconds right now
arecord -D plughw:2,0 -f S16_LE -r 16000 -c 2 -t wav -d 10 "$YOBE_SDK/samples/audio_files/IDListener/${RAW_OUTPUT}.wav"
>>>>>>> main:previous_content/bash_files/generate-wav-original.sh

echo "A record has finished"
# Start timer
START_TIME=$(date +%s)

g++ -o "$START_DIR/Audio/normalize_raw" "$START_DIR/Audio/normalize_wav.cpp" -std=c++11

# Normalizes raw Audio
# Command follows the convention of: Executable, input, output
"$START_DIR/Audio/normalize_raw" "$YOBE_SDK/samples/audio_files/IDListener/${RAW_OUTPUT}.wav" "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}.wav"


# build ... broadside/endfire
cmake --build "$YOBE_SDK/samples/build" # New pi or if changing the C++ file

#Yobe Latency
DEMO_START=$(date +%s.%N)
# Build file and have to run from the samples directory
# ./build/IDListener_demo ./audio_files/IDListener/[file_location].wav broadside target-speaker "student-pc" ./build
# Output file will be in the same location, but have _processed.wav extension
./build/IDListener_demo "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}.wav" broadside target-speaker "student-pc" ./build

#Yobe Latency
DEMO_END=$(date +%s.%N)
DEMO_DURATION=$(echo "$DEMO_END - $DEMO_START" | bc)
echo "IDListener_demo duration: ${DEMO_DURATION} seconds"

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
# ASR_END=$(date +%s.%N)
# ASR_DURATION=$(echo "$ASR_END - $ASR_START" | bc)
# echo "Google ASR duration: ${ASR_DURATION} seconds"


###################################
# Andrew + Suhani's implementation
# source $START_DIR/.venv/bin/activate
# python3  $START_DIR/database/cloud_sql_generation.py "$START_DIR/Transcripts/Output_ASR/${TIMESTAMP}_ASR.txt" "$START_DIR/Transcripts/Output_Cloud_LLM/${TIMESTAMP}_Cloud_LLM.txt" "$START_DIR/database/OpenAI_Integration/api_key.json"
# deactivate
###################################

#####################################
# Noa + Jackie's implementation; Change to dynamic file
source ~/BUtLAR_Voice-Powered-Digital_Human_Assistant/Audio/venv/bin/activate
python3 $START_DIR/Audio/OpenAItesting.py "$START_DIR/Transcripts/Output_ASR/${TIMESTAMP}_ASR.txt" "$START_DIR/Transcripts/Output_LLM/${TIMESTAMP}_LLM.txt" "$START_DIR/database/OpenAI_Integration/api_key.json"
deactivate
#####################################

# End timer
END_TIME=$(date +%s)
ELAPSED_TIME=$((${END_TIME} - ${START_TIME}))
echo "Elapsed time: ${ELAPSED_TIME} seconds"

#####################################
source $START_DIR/.venv/bin/activate
python3 $START_DIR/D-iD/didVideoOutput.py "$START_DIR/database/OpenAI_Integration/api_key.json" "$START_DIR/Transcripts/Output_LLM/${TIMESTAMP}_LLM.txt" "$START_DIR/Transcripts/Vid_link/${TIMESTAMP}_video.txt"
deactivate
#####################################


# Calculate total elapsed time
# TOTAL_END=$(date +%s.%N)
# TOTAL_DURATION=$(echo "$TOTAL_END - $TOTAL_START" | bc)
# echo "Total script duration: ${TOTAL_DURATION} seconds"

# Cleanup
rm "$START_DIR/Audio/normalize_raw"
rm "$YOBE_SDK/samples/audio_files/IDListener/${TIMESTAMP}_processed.wav"
rm "$YOBE_SDK/samples/audio_files/IDListener/${RAW_OUTPUT}.wav"
rm "$YOBE_SDK/samples/audio_files/IDListener/normalize_${TIMESTAMP}.wav"