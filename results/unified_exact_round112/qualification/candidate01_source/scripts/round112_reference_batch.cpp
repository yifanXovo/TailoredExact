// One native process; final candidate's unchanged cold writer; zero Optimize.
#define main inherited_cold_reference_main
#include "../src/round65_reference_build.cpp"
#undef main
#include <sstream>
int main(int argc,char** argv) {try {
    if(argc!=2)throw std::runtime_error("frozen TSV required");
    std::ifstream input(argv[1]);std::string line;int count=0;
    while(std::getline(input,line)) {
        if(!line.empty() && line.back()=='\r')line.pop_back();
        if(line.empty())continue;
        std::istringstream row(line);std::vector<std::string> fields{"Round112ReferenceBatch"};std::string field;
        while(std::getline(row,field,'\t'))fields.push_back(field);
        if(fields.size()!=7)throw std::runtime_error("bad frozen reference row");
        std::vector<char*> args;for(auto& f:fields)args.push_back(f.data());
        if(inherited_cold_reference_main(int(args.size()),args.data()))return 1;
        ++count;
    }
    if(count!=8)throw std::runtime_error("requires five roles and three qualification inputs");
    std::cout<<"8 fresh cold references; Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
