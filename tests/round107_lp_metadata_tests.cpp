#include "Round107LpMetadata.hpp"
#include <fstream>
#include <iostream>
using namespace ebrp;
int main(int argc,char** argv) {
    try {
        auto check=[](const std::string& s,double rhs){std::istringstream f(s);const auto m=round107ReadLpCutoff(f,1);if(!m.present||m.rhs!=rhs)throw std::runtime_error("wrong cutoff");};
        check("Minimize\n obj: G + 0.1 e_2\n + 0.2 e_10 + 0 unused\nSubject To\n r1: 0.2 e_10 + G + 0.1 e_2 <= 0.9\nBounds\n",.9);
        check("Minimize\n obj: - G + 2 e_1\nSubject To\n r1: 2 e_1 - G <= 0.9\n r2: - 1 G + 2 e_1 <=\n 0.8\nEnd\n",.8);
        for(const auto& s:{"Minimize\n obj: G + 0.1 e_1\nSubject To\n r: G <= 1\nEnd\n",
             "Minimize\n obj: G\nSubject To\n r: G <= nan\nEnd\n",
             "Minimize\n obj: G + 1e309 e_1\nSubject To\n r: G <= 1\nEnd\n",
             "Subject To\n r: G <= 1\nEnd\n",
             "Minimize\n obj: G +\nSubject To\n r: G <= 1\nEnd\n"}) {
            bool failed=false;try{std::istringstream f(s);round107ReadLpCutoff(f,1);}catch(const std::runtime_error&){failed=true;}
            if(!failed)throw std::runtime_error("malformed/missing cutoff accepted");
        }
        for(int i=1;i<argc;++i){std::ifstream f(argv[i]);const auto m=round107ReadLpCutoff(f,1);std::cout<<argv[i]<<" cutoff="<<m.rhs<<'\n';}
        std::cout<<"Round107 LP metadata regressions PASS; Optimize=0\n";
    }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
