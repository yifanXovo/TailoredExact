#include "Round64SharedResource.hpp"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {
std::string arc(const char* prefix,int k,int i,int j) {
    return std::string(prefix)+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);
}
std::string node(const char* prefix,int k,int i) {
    return std::string(prefix)+std::to_string(k)+"_"+std::to_string(i);
}
void emit(std::ostream& out,const std::string& name,
          const std::map<std::string,double>& terms,bool inequality=false) {
    out<<' '<<name<<':';
    for(const auto& [n,c]:terms) if(c!=0)out<<(c>0?" + ":" - ")<<std::fabs(c)<<' '<<n;
    out<<(inequality?" <= 0\n":" = 0\n");
}
}
bool validRound64SharedMode(const std::string& m) {
    return m=="off"||m=="q"||m=="t"||m=="sep"||m=="joint";
}
void appendRound64SharedModel(const Instance& in,const std::filesystem::path& path,const std::string& mode) {
    if(!validRound64SharedMode(mode))throw std::runtime_error("invalid shared resource mode");
    if(mode=="off")return;
    {
        std::ifstream input(path);
        if(!input)throw std::runtime_error("shared model input absent");
        const std::string original((std::istreambuf_iterator<char>(input)),{});
        if(original.find("r64_q_balance_")!=std::string::npos||original.find("r63_balance_")!=std::string::npos)
            throw std::runtime_error("duplicate shared/time block");
    }
    const auto data=prepareRound63Time(in);
    if(mode=="t"||mode=="sep"||mode=="joint")
        appendRound63TimeModel(in,path,mode=="t"?"explicit":"coupled");
    if(mode=="t")return;
    std::ifstream input(path);
    if(!input)throw std::runtime_error("shared model input absent");
    std::string text((std::istreambuf_iterator<char>(input)),{});input.close();
    std::ostringstream rows;rows<<std::setprecision(17);
    for(int k=0;k<in.M;++k)for(int i=1;i<=in.V;++i) {
        std::map<std::string,double> balance,load;
        // Fixed-zero depot departures are eliminated. Return columns remain.
        for(int j=0;j<=in.V;++j)if(i!=j) {
            const auto q=arc("r64q_",k,i,j);
            balance[q]=1;load[q]=1;
            emit(rows,arc("r64_q_capacity_",k,i,j),{{q,1},{arc("x_",k,i,j),-double(in.Q[k])}},true);
            if(mode=="joint"&&data.handling>0)
                emit(rows,arc("r64_shared_",k,i,j),{{q,data.handling},{arc("r63f_",k,i,j),-1}},true);
        }
        for(int h=1;h<=in.V;++h)if(h!=i)balance[arc("r64q_",k,h,i)]=-1;
        balance[node("p_",k,i)]=-1;balance[node("d_",k,i)]=1;
        load[node("load_",k,i)]=-1;
        emit(rows,node("r64_q_balance_",k,i),balance);
        emit(rows,node("r64_q_load_",k,i),load);
    }
    const auto bounds=text.find("\nBounds");
    if(bounds==std::string::npos)throw std::runtime_error("shared LP Bounds absent");
    // LP format default domain is continuous [0,+infinity). These new
    // names do not enter the inherited General/Binary sections.
    text.insert(bounds+1,rows.str());std::ofstream out(path);out<<text;
    if(!out)throw std::runtime_error("shared model persistence failure");
    writeRound63TimeData(data,path.string()+".round64.json");
}
std::map<std::string,double> round64RouteResourceValues(const Instance& in,const std::vector<RoutePlan>& routes) {
    const auto data=prepareRound63Time(in);std::map<std::string,double> values;
    for(const auto& route:routes) {
        if(route.vehicle<0||route.vehicle>=in.M||route.nodes.size()<2||route.nodes.front()!=0||route.nodes.back()!=0)
            throw std::runtime_error("invalid shared embedding route");
        int load=0;long double f=0,h=0;
        for(std::size_t pos=1;pos+1<route.nodes.size();++pos) {
            const int from=route.nodes[pos-1],i=route.nodes[pos],to=route.nodes[pos+1];
            if(i<1||i>in.V||from<0||from>in.V||to<0||to>in.V)throw std::runtime_error("invalid shared embedding station");
            const StopOperation* operation=nullptr;
            for(const auto& op:route.operations)if(op.station==i){if(operation)throw std::runtime_error("duplicate shared operation");operation=&op;}
            if(!operation||operation->pickup<0||operation->drop<0)throw std::runtime_error("missing shared operation");
            load+=operation->pickup-operation->drop;
            if(load<0||load>in.Q[route.vehicle])throw std::runtime_error("shared embedding prefix load");
            f+=data.travel[from][i]+static_cast<long double>(data.handling)*operation->pickup;
            h+=data.travel[from][i]+static_cast<long double>(data.handling)*operation->drop;
            values[arc("r64q_",route.vehicle,i,to)]=load;
            values[arc("r63f_",route.vehicle,i,to)]=static_cast<double>(f);
            values[arc("r64h_",route.vehicle,i,to)]=static_cast<double>(h);
        }
    }
    return values;
}
} // namespace ebrp
