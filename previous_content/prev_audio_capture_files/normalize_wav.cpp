#include <iostream>
#include <vector>
#include <fstream>
#include <cstring>
#include <algorithm>
#include <cmath>

// WAV header structure
struct WAVHeader {
    char riff[4];
    int32_t chunkSize;
    char wave[4];
    char fmt[4];
    int32_t subchunk1Size;
    int16_t audioFormat;
    int16_t numChannels;
    int32_t sampleRate;
    int32_t byteRate;
    int16_t blockAlign;
    int16_t bitsPerSample;
    char data[4];
    int32_t dataSize;
};

std::vector<double> normalizeAudio(const std::vector<double>& buffer) {
    if (buffer.empty()) {
        return buffer;
    }

    // Find the maximum absolute value in the buffer
    double max_abs = 0.0;
    for (const double& sample : buffer) {
        max_abs = std::max(max_abs, std::abs(sample));
    }

    // If audio is completely silent or already normalized, return original
    if (max_abs == 0.0 || max_abs == 1.0) {
        return buffer;
    }

    // Calculate normalization factor
    double normalize_factor = 1.0 / max_abs;

    // Apply normalization
    std::vector<double> normalized_buffer(buffer.size());
    for (size_t i = 0; i < buffer.size(); ++i) {
        normalized_buffer[i] = buffer[i] * normalize_factor;
    }

    return normalized_buffer;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " <input_wav> <output_wav>\n";
        return 1;
    }

    std::string input_file = argv[1];
    std::string output_file = argv[2];

    // Open input file
    std::ifstream inFile(input_file, std::ios::binary);
    if (!inFile) {
        std::cerr << "Cannot open input file: " << input_file << "\n";
        return 1;
    }

    // Read WAV header
    WAVHeader header;
    inFile.read(reinterpret_cast<char*>(&header), sizeof(WAVHeader));

    // Verify that it's a valid WAV file
    if (strncmp(header.riff, "RIFF", 4) != 0 || strncmp(header.wave, "WAVE", 4) != 0) {
        std::cerr << "Invalid WAV file\n";
        return 1;
    }

    // Read audio data
    std::vector<int16_t> raw_samples((header.dataSize) / sizeof(int16_t));
    inFile.read(reinterpret_cast<char*>(raw_samples.data()), header.dataSize);
    inFile.close();

    // Convert to doubles (normalized between -1 and 1)
    std::vector<double> samples(raw_samples.size());
    for (size_t i = 0; i < raw_samples.size(); ++i) {
        samples[i] = raw_samples[i] / 32768.0;
    }

    // Apply normalization
    auto normalized_samples = normalizeAudio(samples);

    // Report the normalization results
    double original_max = 0.0;
    double normalized_max = 0.0;
    for (size_t i = 0; i < samples.size(); ++i) {
        original_max = std::max(original_max, std::abs(samples[i]));
        normalized_max = std::max(normalized_max, std::abs(normalized_samples[i]));
    }
    std::cout << "Original peak amplitude: " << original_max << "\n";
    std::cout << "Normalized peak amplitude: " << normalized_max << "\n";

    // Convert back to int16_t
    for (size_t i = 0; i < normalized_samples.size(); ++i) {
        raw_samples[i] = static_cast<int16_t>(normalized_samples[i] * 32768.0);
    }

    // Write output file
    std::ofstream outFile(output_file, std::ios::binary);
    if (!outFile) {
        std::cerr << "Cannot open output file: " << output_file << "\n";
        return 1;
    }

    outFile.write(reinterpret_cast<char*>(&header), sizeof(WAVHeader));
    outFile.write(reinterpret_cast<char*>(raw_samples.data()), header.dataSize);
    outFile.close();

    std::cout << "Successfully normalized audio file\n";
    return 0;
}