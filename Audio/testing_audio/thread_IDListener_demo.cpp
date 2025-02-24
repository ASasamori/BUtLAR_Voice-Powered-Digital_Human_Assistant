// Yobe file that reads from std in and writes to std out
// THREADED VERSION

// File used for original Yobe Processing ID
// run from the samples directory:
// cmake --build build/
// ./build/IDListener_demo "temp.wav" broadside target-speaker "student-pc" ./build

/**
 * @file: IDListener_demo.cpp
 * @copywrite: Yobe Inc.
 * @date: 02/15/2023
 */

#include "util/demo_utils.hpp"
#include "util/client_license.h"

#include "yobe_create_listener.hpp"
#include "yobe_lib_util.hpp"

#include <fstream>
#include <iostream>
#include <vector>
#include <csignal>
#include <unistd.h>
#include <errno.h>

#include <queue>
#include <thread>
#include <mutex>
#include <condition_variable>

constexpr int SAMPLE_RATE = 16000;
constexpr int BUFFER_SIZE = 4096;

/// This is an enviornment variable that store your Yobe license.
constexpr auto ENV_VAR_LICENSE = "YOBE_LICENSE";

/// These are the template we are going to use to create Yobe::IDTemplate
constexpr auto TEMPLATE_01 = AUDIO_FILES_PATH "/IDListener/user_1_template_01.wav";
constexpr auto TEMPLATE_02 = AUDIO_FILES_PATH "/IDListener/user_1_template_02.wav";

// These file are in the audio file folder if you want to experiment.
// constexpr auto TEMPLATE_LONG = AUDIO_FILES_PATH "/IDListener/user_1_template_40s.wav";

/**
 * For example on how to use the IDListener read this function.
 *
 * @param[in] license The yobe license.
 * @param[in] input_buffer This is an interleaved audio buffer.
 *
 * @return A interleaved audio buffer.
 */
std::vector<float> YobeProcessing(const std::string& license, const std::string& machine_name, const std::string& file_path,  std::vector<float> input_buffer, Yobe::MicOrientation mic_orientation, Yobe::OutputBufferType out_buffer_type);

/**
 * This function shows you how to make a Yobe::IDTemplate.
 *
 * @return A template to be used with VerifyUser
 */
std::shared_ptr<Yobe::IDTemplate> CreateTemplateFromFile(const std::unique_ptr<Yobe::IDListener>& id_listener, const std::string& wav_file_path);

/// This ofstream is to demo the logging callback.
std::ofstream log_stream;

// flag for standard in things
volatile sig_atomic_t running = 1;
void handle_signal(int sig) {
    running = 0;
}

// Global queue for passing audio data to Yobe processing
std::queue<std::vector<float>> audio_queue;
std::mutex queue_mutex;
std::condition_variable queue_cv;
bool processing_done = false;

void YobeProcessingThread(const std::string& license, const std::string& device_name, const std::string& file_path, 
                          Yobe::MicOrientation mic_orientation, Yobe::OutputBufferType out_buffer_type) {
    while (true) {
        std::vector<float> input_buffer;

        // Lock queue access
        {
            std::unique_lock<std::mutex> lock(queue_mutex);
            queue_cv.wait(lock, [] { return !audio_queue.empty() || processing_done; });

            if (processing_done && audio_queue.empty()) break;  // Stop processing

            input_buffer = std::move(audio_queue.front());
            audio_queue.pop();
        }

        std::vector<float> processed_audio;
        try {
            processed_audio = YobeProcessing(license, device_name, file_path, input_buffer, mic_orientation, out_buffer_type);
        } catch (const std::exception& e) {
            std::cerr << "Yobe Processing Error: " << e.what() << std::endl;
            continue;
        }

        // Convert float back to int16 PCM for output
        std::vector<int16_t> output_pcm(processed_audio.size());
        for (size_t i = 0; i < processed_audio.size(); ++i) {
            output_pcm[i] = static_cast<int16_t>(std::max(-1.0f, std::min(1.0f, processed_audio[i])) * 32767);
        }

        // Write to stdout
        ssize_t bytes_written = write(STDOUT_FILENO, output_pcm.data(), output_pcm.size() * sizeof(int16_t));
        if (bytes_written < 0) {
            std::cerr << "Failed to write to stdout.\n";
        }
    }
}

int main(int argc, char* argv[]) {
    if (argc < 6) {
        std::cerr << "\nERROR- invalid arguments\n\n";
        return 1;
    }

    const std::string file_path(argv[1]);
    Yobe::MicOrientation mic_orientation = DemoUtil::GetMicOrientation(argv[2]);
    Yobe::OutputBufferType out_buffer_type = DemoUtil::GetOutputBufferType(argv[3]);
    std::string device_name = argv[4];
    std::string license_file_path = argv[5];

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    std::cout << "Listening for audio input...\n";

    // Start Yobe processing in a separate thread
    std::thread yobe_thread(YobeProcessingThread, getLicense(ENV_VAR_LICENSE), device_name, license_file_path, mic_orientation, out_buffer_type);

    // Read audio from stdin and push to queue
    while (running) {
        std::vector<int16_t> pcm_data(BUFFER_SIZE * 2);  // 2 channels
        ssize_t bytes_read = read(STDIN_FILENO, pcm_data.data(), pcm_data.size() * sizeof(int16_t));

        if (bytes_read <= 0) {
            std::cerr << "Failed to read from stdin or reached EOF.\n";
            break;
        }

        // Convert PCM int16 to float for Yobe
        std::vector<float> input_buffer;
        for (size_t i = 0; i < bytes_read / sizeof(int16_t); ++i) {
            input_buffer.push_back(static_cast<float>(pcm_data[i]) / 32768.0f);
        }

        // Add input buffer to the queue
        {
            std::lock_guard<std::mutex> lock(queue_mutex);
            audio_queue.push(std::move(input_buffer));
        }
        queue_cv.notify_one();
    }

    // Signal processing thread to stop
    {
        std::lock_guard<std::mutex> lock(queue_mutex);
        processing_done = true;
    }
    queue_cv.notify_one();

    yobe_thread.join(); // Wait for the processing thread to finish

    std::cout << "Exiting...\n";
    return 0;
}

void LogCallback(const char* mess) {
   log_stream << mess << '\n'; 
}

std::vector<float> YobeProcessing(const std::string& license, const std::string& device_name, const std::string& file_path, std::vector<float> input_buffer, Yobe::MicOrientation mic_orientation, Yobe::OutputBufferType out_buffer_type) {
    // Here we set up our logging callback
    log_stream.open("IDListener_demo.log");
    Yobe::Info::RegisterCallback(LogCallback);

    
    // Init the IDListener.
    auto id_listener = Yobe::Create::NewIDListener(license, device_name, file_path, INIT_DATA_PATH, mic_orientation, out_buffer_type);

    if (id_listener == nullptr) {
        std::cout << "Probably the library you have does not have biometrics." << std::endl;
        return {};
    }

    auto init_status = id_listener->GetStatus();

    if (init_status != Yobe::Status::YOBE_OK) {
        std::cout << "Init returned: " << Yobe::Info::StdError(init_status) << '\n';
        throw std::runtime_error("Initialization error");
    }

    // Calculate the input buffer size that you are going to pass in to ProcessBuffer.
    const auto input_size = Yobe::Info::InputBufferSize();
    

    // Prepare output buffer for collecting the out put from the IDListener.
    std::vector<float> output_buffer;

    // This is the pre-allocated buffer that will be returned with processed data in it.
    std::vector<float> scratch_buffer;

    auto status = Yobe::Status::YOBE_UNKNOWN;
    const auto total_input_samples = input_buffer.size();

    std::shared_ptr<Yobe::IDTemplate> id_template;

    DemoUtil::ZeroPadSignal(input_buffer);

    std::cout << "Yobe has started processing.\n";

    bool did_mid_process_enrollment = false;
    for (size_t input_index = 0; input_index < total_input_samples; input_index += input_size) {
        // This can be used to determine if the selected user was detected in the processed buffer.
        int template_index;

        // Here we are processing the audio a buffer at a time.
        status = id_listener->ProcessBuffer(&input_buffer[input_index], scratch_buffer, input_size, template_index);
        // log_stream << "Yobe::ProcessBuffer: " << Yobe::Info::StdError(status) << " | User detected: " << std::boolalpha << is_user_verify << "\n";

        // Process enough data to calibrate, then enroll.
        if (!did_mid_process_enrollment && status == Yobe::Status::YOBE_OK) {
            // An example of enrolling a user during processing.
            // Create two templates and merge them into one.
            auto template_1 = CreateTemplateFromFile(id_listener, TEMPLATE_01);
            auto template_2 = CreateTemplateFromFile(id_listener, TEMPLATE_02);
            id_template = id_listener->MergeUserTemplates({template_1, template_2});
            id_listener->SelectUser({id_template});
            did_mid_process_enrollment = true;
        }

        // Now we check the status to make sure that the audio got processed.
        if (status != Yobe::Status::YOBE_OK && status != Yobe::Status::NEEDS_MORE_DATA && status != Yobe::Status::CALIBRATION_DONE) {
            std::cout << "ProcessBuffer returned: " << Yobe::Info::StdError(status) << '\n';
        } else if (!scratch_buffer.empty()) {
            // Now we collect our scratch buffer into are output buffer
            output_buffer.insert(output_buffer.end(), scratch_buffer.begin(), scratch_buffer.end());
        }
    }

    // Here we are cleaning up and deiniting the IDListener.
    id_listener.reset();

    std::cout << "IDListener has finished processing.\n";

    // closing the log stream
    log_stream.close();

    return output_buffer;
}



std::shared_ptr<Yobe::IDTemplate> CreateTemplateFromFile(const std::unique_ptr<Yobe::IDListener>& id_listener, const std::string& wav_file_path) {
    std::cout << "Now registering a template.\n";

    auto template_samples = DemoUtil::ReadAudioFile(wav_file_path);
    std::uint32_t sample_idx = 0;
    Yobe::Status status = id_listener->StartEnrollment(Yobe::EnrollLength::MEDIUM);
    if(status == Yobe::Status::YOBE_ERROR) {
        std::cerr << "Error starting enrollment\n";
        throw;
    }

    while (status != Yobe::Status::ENROLLMENT_END) {
        if (sample_idx + Yobe::Info::InputBufferSize() > template_samples.size()) {
            std::cerr << "All template samples have been processed, need more audio! sample_idx: " << sample_idx << " template samples size: " << template_samples.size() << "\n";
            throw;
        }

        std::vector<float> out_samples{};
        int template_index;
        status = id_listener->ProcessBuffer(&template_samples[sample_idx], out_samples, Yobe::Info::InputBufferSize(), template_index);
        sample_idx += Yobe::Info::InputBufferSize();
    }
    auto enrollment_template = id_listener->GetIDTemplate();

    if (enrollment_template == nullptr) {
        std::cerr << "Template retrieved from id_listener was null.";
        throw;
    }

    return enrollment_template;
}


