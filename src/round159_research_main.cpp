#include "Round159JointResource.hpp"
#include <exception>
#include <iostream>

int main(int argc, char** argv) {
    try {
        if (argc < 5 || argc > 6) {
            std::cerr << "Round159Research baseline|joint|complete data rn out [start]\n";
            return 2;
        }
        return round159::run(argv[1],argv[2],argv[3],argv[4],argc==6?argv[5]:"");
    } catch(const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
