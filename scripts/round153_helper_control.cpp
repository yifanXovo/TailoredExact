#include "Round153Research.hpp"
#include <iostream>
int main(int argc,char** argv){
    if(argc<3)return 2;
    std::vector<std::string> command;
    for(int i=2;i<argc;++i)command.push_back(argv[i]);
    const auto tick=std::chrono::steady_clock::now();
    const int result=ebrp::round153_detail::hiddenHelper(command,std::stod(argv[1]));
    std::cout<<"{\"exit\":"<<result<<",\"seconds\":"<<std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count()<<"}\n";
    return 0;
}
