#include "Round62Thresholds.hpp"
#include "Parser.hpp"
#include <iostream>
#include <sstream>
#include <algorithm>
int main(int argc,char** argv){try{
    std::string input,out,es;double T=3600,pick=60,drop=60;
    for(int i=1;i<argc;++i){std::string a=argv[i];auto val=[&](){if(++i>=argc)throw std::runtime_error("missing value");return std::string(argv[i]);};
        if(a=="--input")input=val();else if(a=="--out")out=val();else if(a=="--T")T=std::stod(val());
        else if(a=="--pickup-time")pick=std::stod(val());else if(a=="--drop-time")drop=std::stod(val());
        else if(a=="--events")es=val();else throw std::runtime_error("unknown argument");}
    const auto in=ebrp::parseInstanceFile(input,T,pick,drop);auto p=ebrp::generateRound62Thresholds(in);
    std::filesystem::create_directories(out);
    ebrp::writeRound62ThresholdProof(in,p,ebrp::round62ThresholdRows(in,p,"conflicts"),std::filesystem::path(out)/"generated.json");
    if(!es.empty()) {
        std::vector<ebrp::Round62Event> events;std::istringstream stream(es);std::string item;
        while(std::getline(stream,item,',')){std::replace(item.begin(),item.end(),':',' ');std::istringstream f(item);ebrp::Round62Event e;
            if(!(f>>e.station>>e.direction>>e.quantity))throw std::runtime_error("bad event");events.push_back(e);}
        ebrp::Round62Conflict c;const bool proved=ebrp::proveRound62Conflict(in,p.shortest,events,&c);
        ebrp::Round62ThresholdProof example;example.shortest=p.shortest;example.margin=p.margin;
        if(proved){example.conflicts={c};example.dictionary=events;}
        ebrp::writeRound62ThresholdProof(in,example,proved?ebrp::round62ThresholdRows(in,example,"projection"):std::vector<ebrp::Round62Row>{},std::filesystem::path(out)/"regression.json");
        std::cout<<"regression_proved="<<proved<<'\n';
    }
    std::cout<<"events="<<p.dictionary.size()<<" conflicts="<<p.conflicts.size()<<" edges="<<p.incompatible_edges<<" seconds="<<p.seconds<<'\n';
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
