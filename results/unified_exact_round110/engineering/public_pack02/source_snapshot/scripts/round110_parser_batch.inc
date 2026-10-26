// Included after the original or repaired Parser.cpp in separate executables.
#include <cstdint>
#include <cstring>
#include <iomanip>
#include <iostream>

namespace {
void hexDouble(double x) {
    std::uint64_t bits; std::memcpy(&bits, &x, sizeof(bits));
    std::cout << std::hex << std::setw(16) << std::setfill('0') << bits << std::dec;
}
void hexText(const std::string& x) {
    for (unsigned char c : x) std::cout << std::hex << std::setw(2) << std::setfill('0') << static_cast<unsigned>(c);
    std::cout << std::dec;
}
template<class T> void integers(const char* name, const std::vector<T>& x) {
    std::cout << name; for (auto v:x) std::cout << '\t' << v; std::cout << '\n';
}
void doubles(const char* name, const std::vector<double>& x) {
    std::cout << name; for (double v:x) { std::cout << '\t'; hexDouble(v); } std::cout << '\n';
}
}

int main(int argc,char** argv) {
    try {
        if (argc!=2) return 2;
        // Finite extraction boundaries; payload itself contains arbitrary text.
        const std::vector<std::pair<std::string,std::string>> cases={
            {"initial","absent=[]"},{"initial","initial=[]"},
            {"initial","initial = [1\n2\r\t3]"},{"initial","initial=[4] initial=[5]"},
            {"initial","prefixinitial=[6]"},{"initial","initialX=[7] initial=[8]"},
            {"initial","initial = x [9] initial=[10]"},{"initial","initial=[1[2]3]"},
            {"initial","initial=[unclosed"},{"initial","initial=[unclosed initial=[11]"},
            {"points","weights=[1] points=\n\t [0,0; 1,2] initial=[4]"},
            {"initial","initial\v\f=\r\n[+1e0, -.5, +.5]"},
            {"weights","weights=[ ]\nweights=[3]"},
            {"initial",std::string("initial=[a\0b]tail",18)},
            {"initial","initial"+std::string(256,' ') +"="+std::string(256,'\t')+"[1]"},
            {"initial","initial=["+std::string(6000,'x')+"]"}};
        for (std::size_t i=0;i<cases.size();++i) {
            std::cout << "case\t" << i << '\t';
            hexText(ebrp::namedBracketPayload(cases[i].second,cases[i].first)); std::cout << '\n';
        }
        std::ifstream manifest(argv[1]); std::string line; unsigned count=0;
        while (std::getline(manifest,line)) {
            std::istringstream ss(line);std::string path,Ts; std::getline(ss,path,'\t');std::getline(ss,Ts,'\t');
            const auto a=ebrp::parseInstanceFile(path,std::stod(Ts),60,60);
            std::cout << "instance\t" << a.name << '\t' << a.V << '\t' << a.M << '\n';
            integers("Q",a.Q);integers("capacity",a.capacity);integers("initial",a.initial);integers("target",a.target);
            doubles("weights",a.weights);doubles("min_ratio",a.min_ratio);
            std::cout << "points";for (auto p:a.points) {std::cout << '\t';hexDouble(p.first);std::cout << '\t';hexDouble(p.second);}std::cout << '\n';
            for (const auto& row:a.dist) doubles("dist",row);
            doubles("time",{a.total_time_limit,a.pickup_time,a.drop_time});
            std::cerr << "metadata\t" << a.name << '\t' << a.path << '\t' << a.distance_convention << '\n';++count;
        }
        std::cerr << "batch_complete\t" << count << "\tOptimize=0\n";
        return count==12?0:3;
    } catch (const std::exception& ex) {std::cerr << ex.what() << '\n';return 1;}
}
