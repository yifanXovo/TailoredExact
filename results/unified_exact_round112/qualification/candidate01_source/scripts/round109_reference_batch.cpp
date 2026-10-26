// Single-process zero-Optimize batch of the unchanged original P cold writer.
// No optimizer symbol, presolve, solution, basis, or Start is invoked.
#define main inherited_cold_reference_main
#include "../src/round65_reference_build.cpp"
#undef main
#include <sstream>
#include <vector>
int main(int argc,char** argv) {
    try {
        if(argc!=2)throw std::runtime_error("frozen TSV input T pickup drop lambda output_directory");
        std::ifstream input(argv[1]);if(!input)throw std::runtime_error("batch manifest unavailable");
        std::string line;int count=0;
        while(std::getline(input,line)) {
            if(!line.empty()&&line.back()=='\r')line.pop_back();
            if(line.empty())continue;
            std::istringstream row(line);std::vector<std::string> fields{"Round109ReferenceBatch"};std::string field;
            while(std::getline(row,field,'\t'))fields.push_back(field);
            if(fields.size()!=7)throw std::runtime_error("malformed frozen batch row");
            std::vector<char*> args;for(auto& value:fields)args.push_back(value.data());
            const int rc=inherited_cold_reference_main(static_cast<int>(args.size()),args.data());
            if(rc)return rc;
            std::cout<<"built_cold_reference\t"<<fields[1]<<"\tOptimize=0\n";++count;
        }
        if(count!=13)throw std::runtime_error("requires twelve new inputs plus one known qualification fixture");
        std::cout<<"batch_complete\t13\tOptimize=0\n";return 0;
    } catch(const std::exception& error) {std::cerr<<error.what()<<'\n';return 1;}
}
