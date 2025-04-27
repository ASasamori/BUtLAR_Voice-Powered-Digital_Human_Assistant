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

/// This is an enviornment variable that store your Yobe license.
constexpr auto ENV_VAR_LICENSE = "YOBE_LICENSE";

/// These are the template we are going to use to create Yobe::IDTemplate
// constexpr auto TEMPLATE_01 = AUDIO_FILES_PATH "/IDListener/suhani_template_01.wav";
// constexpr auto TEMPLATE_02 = AUDIO_FILES_PATH "/IDListener/suhani_template_02.wav";
constexpr auto TEMPLATE_01 = AUDIO_FILES_PATH "/IDListener/andrew_sasamori_template.wav";
constexpr auto TEMPLATE_02 = AUDIO_FILES_PATH "/IDListener/andrew_sasamori_template_2.wav";

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

int main(int argc, char* argv[]) {
    if (argc < 6) {
        std::cerr << "\nERROR- invalid arguments\n\n";
        std::cerr << "Example: IDListener_demo WAV_FILE_PATH [end-fire|broadside] [target-speaker|no-target] device_name license_file_path\n";
    } else {
        // Just printing out the setting the IDListener expects
        std::cout << "Just checking to see if the Yobe parameters match the audio file.\n";
        std::cout << "Expected sampling rate: " << Yobe::Info::SamplingRate() << '\n';
        std::cout << "Expected buffer size in seconds: " << Yobe::Info::AudioBufferTime() << '\n';
        std::cout << "Number expected input channels: " << Yobe::Info::InputChannels() << '\n';
        std::cout << "Number expected output channels: " << Yobe::Info::OutputChannels() << "\n\n";

        const std::string file_path(argv[1]);
        Yobe::MicOrientation mic_orientation = DemoUtil::GetMicOrientation(argv[2]);
        Yobe::OutputBufferType out_buffer_type = DemoUtil::GetOutputBufferType(argv[3]);
        
        // Preparing input buffer
        const auto input_buffer = DemoUtil::ReadAudioFile(file_path);

        std::cout << '\n';

        std::vector<float> processed_audio;
        std::string device_name = argv[4];
        std::string license_file_path = argv[5];
        
        try {
            // All the Yobe processing happens in this function
            processed_audio = YobeProcessing(getLicense(ENV_VAR_LICENSE), device_name, license_file_path, input_buffer, mic_orientation, out_buffer_type);
        } catch (const std::exception& e) {
            std::cerr << e.what() << '\n';
            return 1;
        }

        // Writing the processed data to a .wav file
        std::string output_file = file_path.substr(0, file_path.size()-4) + "_" + argv[2] + ".wav";
        DemoUtil::WriteAudioFile(output_file, processed_audio);
    }

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
