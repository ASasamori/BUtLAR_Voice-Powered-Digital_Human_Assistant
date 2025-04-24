// File used for original Yobe Processing ID
// run from the samples directory:
// cmake --build build/
// ./build/IDListener_demo "temp.wav" broadside target-speaker "student-pc" ./build

#define MINIAUDIO_IMPLEMENTATION
#include "miniaudio.h"
#include <stdio.h>
#include <signal.h>

#define SAMPLE_RATE 16000
#define BUFFER_SIZE 2048

volatile sig_atomic_t running = 1;

void handle_signal(int sig) {
    running = 0;
}

void data_callback(ma_device* pDevice, void* pOutput, const void* pInput, ma_uint32 frameCount) {
    if (pInput == NULL) {
        return;
    }

    // Write directly to stdout
    size_t written = fwrite(pInput, sizeof(ma_int16), frameCount * 2, stdout);
    fflush(stdout); // Ensure data is sent immediately

    // Optional loopback if needed
    memcpy(pOutput, pInput, frameCount * sizeof(ma_int16));
}

int main() {
    // Set up signal handling
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    ma_context context;
    ma_device_info* pCaptureDevices;
    ma_uint32 captureDeviceCount;
    ma_result result;

    // Initialize context
    result = ma_context_init(NULL, 0, NULL, &context);
    if (result != MA_SUCCESS) {
        fprintf(stderr, "Failed to initialize context.\n");
        return -1;
    }

    // Get available devices
    result = ma_context_get_devices(&context, NULL, NULL, &pCaptureDevices, &captureDeviceCount);
    if (result != MA_SUCCESS) {
        fprintf(stderr, "Failed to get device list.\n");
        ma_context_uninit(&context);
        return -1;
    }

    // Configure device
    ma_device_config deviceConfig = ma_device_config_init(ma_device_type_duplex);
    deviceConfig.capture.pDeviceID = &pCaptureDevices[1].id; // Rode mic ID
    deviceConfig.capture.format = ma_format_s16;
    deviceConfig.capture.channels = 2;
    deviceConfig.playback.format = ma_format_s16;
    deviceConfig.playback.channels = 2;
    deviceConfig.sampleRate = SAMPLE_RATE;
    deviceConfig.periodSizeInFrames = BUFFER_SIZE;
    deviceConfig.dataCallback = data_callback;

    // Initialize device
    ma_device device;
    result = ma_device_init(NULL, &deviceConfig, &device);
    if (result != MA_SUCCESS) {
        fprintf(stderr, "Failed to initialize device\n");
        ma_context_uninit(&context);
        return -1;
    }

    // Start device
    result = ma_device_start(&device);
    if (result != MA_SUCCESS) {
        fprintf(stderr, "Failed to start device\n");
        ma_device_uninit(&device);
        ma_context_uninit(&context);
        return -1;
    }

    // Run until signal received
    while (running) {
        ma_sleep(100);
        
    }

    // Cleanup
    ma_device_uninit(&device);
    ma_context_uninit(&context);
    return 0;
}