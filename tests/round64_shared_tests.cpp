#include "Round64SharedResource.hpp"
#include "MipStartMapping.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <cmath>
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace {
void require(bool b,const char* message){if(!b)throw std::runtime_error(message);}
std::string arc(const char* p,int k,int i,int j){return std::string(p)+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
ebrp::Instance toy() {
    ebrp::Instance in;in.V=4;in.M=2;in.Q={2,4};in.initial={0,5,5,5,5};in.capacity={0,10,10,10,10};in.target={0,5,5,5,5};in.weights={0,.25,.25,.25,.25};
    in.pickup_time=.3;in.drop_time=.7;in.total_time_limit=100;
    in.dist.assign(5,std::vector<double>(5));for(int i=0;i<5;++i)for(int j=0;j<5;++j)if(i!=j)in.dist[i][j]=(i*19+j*7)%17;
    return in;
}
void embedding() {
    auto in=toy();std::vector<int> order={1,2,3,4};int checked=0;bool recycled=false,loaded=false;
    do {for(int pattern=0;pattern<256;++pattern)for(int k=0;k<2;++k)for(int zero=0;zero<2;++zero) {
        auto data_in=in;if(zero)data_in.pickup_time=data_in.drop_time=0;
        ebrp::RoutePlan route;route.vehicle=k;route.nodes={0};int bits=pattern,load=0,total=0;bool legal=true;
        for(int i:order){int q=(bits%4<2?bits%4-2:bits%4-1);bits/=4;load+=q;total+=std::max(0,q);legal&=load>=0&&load<=in.Q[k];
            route.nodes.push_back(i);route.operations.push_back({i,std::max(0,q),std::max(0,-q)});}
        route.nodes.push_back(0);if(!legal)continue;
        double travel=0;for(std::size_t pos=1;pos<route.nodes.size();++pos)travel+=in.dist[route.nodes[pos-1]][route.nodes[pos]];
        data_in.total_time_limit=travel+(data_in.pickup_time+data_in.drop_time)*total;
        const auto d=ebrp::prepareRound63Time(data_in);auto v=ebrp::round64RouteResourceValues(data_in,{route});
        auto val=[&](const char* p,int i,int j){return v[arc(p,k,i,j)];};
        int prefix=0;
        for(std::size_t pos=1;pos+1<route.nodes.size();++pos) {
            int i=route.nodes[pos],next=route.nodes[pos+1],prev=route.nodes[pos-1];const auto& op=route.operations[pos-1];prefix+=op.pickup-op.drop;
            require(std::fabs(val("r63f_",i,next)-val("r64h_",i,next)-d.handling*prefix)<1e-12,"f=h+cq identity");
            require(val("r64q_",i,next)==prefix,"out(q)=load");require(val("r64h_",i,next)>=0,"negative h");
            require(val("r63f_",i,next)<=d.upper[i][next]+1e-12,"time capacity");
            require(d.handling*prefix<=d.upper[i][next]+1e-12,"projected load-time capacity");
            double bq=0,bf=0,bh=0;
            for(int j=0;j<=in.V;++j)if(i!=j){bq+=val("r64q_",i,j)-val("r64q_",j,i);bf+=val("r63f_",i,j)-val("r63f_",j,i);bh+=val("r64h_",i,j)-val("r64h_",j,i);}
            require(std::fabs(bq-op.pickup+op.drop)<1e-12,"q balance");
            require(std::fabs(bf-d.travel[prev][i]-d.handling*op.pickup)<1e-12,"f balance");
            require(std::fabs(bh-d.travel[prev][i]-d.handling*op.drop)<1e-12,"h balance");
        }
        for(int i=1;i<=4;++i)require(val("r64q_",0,i)==0&&val("r63f_",0,i)==0&&val("r64h_",0,i)==0,"depot departure");
        recycled|=total>in.Q[k];loaded|=load>0;++checked;
    }}while(std::next_permutation(order.begin(),order.end()));
    require(checked>100&&recycled&&loaded,"embedding coverage");
}
void mapping() {
    auto in=toy();ebrp::RoutePlan r{0,{0,1,2,3,4,0},{{1,2,0},{2,0,2},{3,2,0},{4,0,1}}};
    auto values=ebrp::round64RouteResourceValues(in,{r});ebrp::SolverNeutralModelDomain domain;
    for(int k=0;k<2;++k)for(int i=1;i<=4;++i)for(int j=0;j<=4;++j)if(i!=j)for(const char* prefix:{"r64q_","r63f_","r64h_"}) {
        domain.names.push_back(arc(prefix,k,i,j));domain.lower_bounds.push_back(0);domain.upper_bounds.push_back(1e6);domain.variable_types.push_back('C');
    }
    ebrp::SolveOptions options;const auto mapped=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,{r},"unit-current-verified",0,1,1e6,domain);
    require(mapped.complete,"resource start incomplete");
    for(std::size_t col=0;col<domain.names.size();++col)require(std::fabs(mapped.values[col]-values[domain.names[col]])<1e-12,"mapped resource differs");
    const auto invalid=ebrp::mapVerifiedRoutesToCanonicalModel(in,options,{r},"outside-domain",.9,1,1e6,domain);
    require(!invalid.complete,"inapplicable interval accepted");
}
void model() {
    auto in=toy();const auto path=std::filesystem::temp_directory_path()/"round64_solver_free_model.lp";
    auto write=[&](){std::ofstream f(path);f<<"Minimize\n obj: load_0_1\nSubject To\n basic: load_0_1 >= 0\nBounds\nEnd\n";};
    auto contents=[&](){std::ifstream f(path);return std::string((std::istreambuf_iterator<char>(f)),{});};
    write();const auto hash=ebrp::fileSha256(path);ebrp::appendRound64SharedModel(in,path,"off");require(hash==ebrp::fileSha256(path),"default modifies bytes");
    require(ebrp::SolveOptions{}.round64_shared_mode=="off","default not off");
    write();ebrp::appendRound64SharedModel(in,path,"q");auto q=contents();require(q.find("r64_q_load_")!=q.npos&&q.find("r63f_")==q.npos,"q isolation");
    write();ebrp::appendRound64SharedModel(in,path,"qcap");require(contents()==q,"provably redundant qcap must preserve Q model bytes");
    auto short_in=in;short_in.total_time_limit=10;
    write();ebrp::appendRound64SharedModel(short_in,path,"qcap");auto qcap=contents();
    require(qcap.find("r64_q_time_capacity_")!=qcap.npos&&qcap.find("r63f_")==qcap.npos,"projected capacity without f");
    write();ebrp::appendRound64SharedModel(in,path,"sep");auto sep=contents();require(sep.find("r63_carried_")!=sep.npos&&sep.find("r64_shared_")==sep.npos,"SEP B4 control");
    write();ebrp::appendRound64SharedModel(in,path,"joint");auto joint=contents();require(joint.find("r64_shared_")!=joint.npos&&joint.find("r64q_0_1_0")!=joint.npos,"joint/return absent");
    require(joint.find("r64q_0_0_")==joint.npos,"depot q should be eliminated");
    bool duplicate=false;try{ebrp::appendRound64SharedModel(in,path,"joint");}catch(...){duplicate=true;}require(duplicate,"duplicate block accepted");
    in.pickup_time=in.drop_time=0;write();ebrp::appendRound64SharedModel(in,path,"joint");require(contents().find("r64_shared_")==std::string::npos,"zero handling row retained");
    write();ebrp::appendRound64SharedModel(in,path,"qcap");require(contents()==q,"zero handling qcap is Q");
    require(!ebrp::validRound64SharedMode("auto-by-instance"),"nonuniform selector accepted");
    std::filesystem::remove(path);std::filesystem::remove(path.string()+".round63.json");std::filesystem::remove(path.string()+".round64.json");
}
}
int main(){try{embedding();mapping();model();std::cout<<"Round64 integer embeddings, shared identities, warm mapping and static isolation passed\n";return 0;}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
