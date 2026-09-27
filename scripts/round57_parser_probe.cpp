#include "Parser.hpp"

#include <algorithm>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: round57_parser_probe <instance-root>\n";
        return 2;
    }
    const std::filesystem::path root(argv[1]);
    std::vector<std::filesystem::path> files;
    for (const auto& entry : std::filesystem::recursive_directory_iterator(root)) {
        if (entry.is_regular_file() && entry.path().extension() == ".txt") {
            files.push_back(entry.path());
        }
    }
    std::sort(files.begin(), files.end());
    int failures = 0;
    for (const auto& file : files) {
        try {
            const ebrp::Instance instance = ebrp::parseInstanceFile(
                file, 3600.0, 60.0, 60.0);
            std::cout << "PASS\t" << file.generic_string()
                      << "\t" << instance.V
                      << "\t" << instance.M
                      << "\t" << instance.Q.size()
                      << "\t" << instance.capacity.size()
                      << "\t" << instance.points.size()
                      << "\t" << instance.dist.size()
                      << "\t" << instance.distance_convention << "\n";
        } catch (const std::exception& error) {
            ++failures;
            std::cout << "FAIL\t" << file.generic_string()
                      << "\t0\t0\t0\t0\t0\t0\t" << error.what() << "\n";
        }
    }
    return failures == 0 ? 0 : 1;
}
