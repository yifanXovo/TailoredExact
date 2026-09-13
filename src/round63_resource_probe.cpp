// Bounded original-objective LP closure and continuous-flow feasibility checks.
// Every native call is recorded before optimize; none contributes a global F certificate.
#include "Round63TimeResource.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "Parser.hpp"
#include "FileSha256.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>

using namespace ebrp;
namespace {
std::string xname(int k,int i,int j){return "x_"+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
Round63TimePoint pointFrom(const Round63TimeData& d,const FixedIntervalMipOutcome& o) {
    std::map<std::string,double> values;for(const auto& v:o.lp_primal_dual_variable_evidence)values.emplace(v.name,v.primal_value);
    auto p=emptyRound63TimePoint(d);
    for(int k=0;k<d.M;++k)for(int i=0;i<=d.V;++i){if(i)p.pickup[k][i]=values.at("p_"+std::to_string(k)+"_"+std::to_string(i));
        for(int j=0;j<=d.V;++j)if(i!=j)p.x[k][i][j]=values.at(xname(k,i,j));}
    return p;
}
void savePoint(const FixedIntervalMipOutcome& o,const std::filesystem::path& path) {
    std::ofstream f(path);f<<std::setprecision(17)<<"variable,value,lower,upper\n";
    for(const auto& v:o.lp_primal_dual_variable_evidence)f<<v.name<<','<<v.primal_value<<','<<v.lower_bound<<','<<v.upper_bound<<'\n';
    if(!f)throw std::runtime_error("LP point persistence failed");
}
}
int main(int argc,char** argv) {
    try {
        const auto started=std::chrono::steady_clock::now();auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
        std::string input,source,expected,output;double T=3600,pickup=60,drop=60,cap=120;bool micro=false;
        for(int i=1;i<argc;++i){std::string a=argv[i];auto value=[&](){if(++i==argc)throw std::runtime_error("argument missing");return std::string(argv[i]);};
            if(a=="--input")input=value();else if(a=="--model")source=value();else if(a=="--expected-sha")expected=value();else if(a=="--out")output=value();
            else if(a=="--T")T=std::stod(value());else if(a=="--pickup-time")pickup=std::stod(value());else if(a=="--drop-time")drop=std::stod(value());
            else if(a=="--cap")cap=std::stod(value());else if(a=="--micro")micro=true;else throw std::runtime_error("unknown probe argument");}
        if(output.empty()||cap<=0||cap>300)throw std::runtime_error("invalid probe cap/output");
        const std::filesystem::path dir(output);std::filesystem::create_directories(dir);
        Instance in;
        if(micro){in.V=4;in.M=1;in.Q={3};in.initial.assign(5,5);in.capacity.assign(5,10);in.target.assign(5,5);in.weights.assign(5,.25);
            in.dist.assign(5,std::vector<double>(5));for(int i=0;i<5;++i)for(int j=0;j<5;++j)if(i!=j)in.dist[i][j]=(i*7+j*13)%11;
            in.total_time_limit=70;in.pickup_time=1;in.drop_time=1;}
        else {if(input.empty()||source.empty()||expected.empty()||fileSha256(source)!=expected)throw std::runtime_error("probe requires frozen source SHA");
            in=parseInstanceFile(input,T,pickup,drop);}
        const auto d=prepareRound63Time(in);writeRound63TimeData(d,dir/"resource.json");
        SolveOptions options;options.gurobi_presolve=-1;options.gurobi_seed=0;options.log_path=(dir/"environment.log").string();
        auto backend=makeGurobiFixedIntervalBackend(in,options);
        if(!backend||!backend->capabilities().available)throw std::runtime_error("probe backend unavailable");
        std::ofstream calls(dir/"native_calls.csv"),summary(dir/"lp_queries.csv"),cuts(dir/"cuts.jsonl"),terms(dir/"cut_points.csv"),separation(dir/"separation.csv");
        calls<<"query,arm,remaining_seconds,model_sha256,additional_rows\n";
        summary<<std::setprecision(17)<<"query,arm,status,optimal,objective,work,solver_seconds,rows,columns,nonzeros,valid,seconds\n";
        separation<<std::setprecision(17)<<"query,arm,vehicle,maximum_violation,all_violation,max_singleton_violation,support_size,seconds\n";
        terms<<std::setprecision(17)<<"query,vehicle,variable,value\n";int count=0,graphs=0,total_rows=0;double separation_seconds=0;bool closed=false;double base_obj=0,explicit_obj=0,simple_obj=0,closure_obj=0;
        std::vector<FixedIntervalMipRequest::AdditionalLinearRow> rows;
        auto solve=[&](const std::filesystem::path& path,const std::string& arm) {
            const double remaining=cap-elapsed()-3;if(remaining<=0||count>=(micro?24:67))throw std::runtime_error("probe bounded budget exhausted");
            FixedIntervalMipRequest req;req.solve_kind=FixedIntervalSolveKind::PaperLpRelaxation;req.leaf_id=arm+std::to_string(count);
            req.gamma_L=0;req.gamma_U=1;req.verified_cutoff=1e6;req.global_deadline_remaining_seconds=remaining;req.time_limit_seconds=remaining;
            req.canonical_model_path=path;req.canonical_model_fingerprint=fileSha256(path);req.canonical_row_signature=req.canonical_model_fingerprint;
            req.canonical_model_scope="diagnostic_physical_global";req.native_log_path=dir/("lp_"+std::to_string(count)+".log");
            req.capture_lp_primal_dual_evidence=true;req.interval_mip_policy="interval-mip-core-no-exhaustive-subset-duration";req.additional_linear_rows=rows;
            calls<<std::setprecision(17)<<count<<','<<arm<<','<<remaining<<','<<req.canonical_model_fingerprint<<','<<rows.size()<<'\n';calls.flush();++count;
            const auto o=backend->solve(req);const bool valid=o.optimal&&o.lp_terminal_valid&&o.lp_primal_dual_evidence_available&&o.model_fingerprint_matches_request;
            summary<<count-1<<','<<arm<<','<<o.native_status<<','<<o.optimal<<','<<o.lp_objective_value<<','<<o.work<<','<<o.solver_runtime_seconds<<','
                <<o.model_linear_constraint_count<<','<<o.model_variable_count<<','<<o.model_nonzero_count<<','<<valid<<','<<elapsed()<<'\n';summary.flush();
            if(!o.available||!o.attempted||(!micro&&!valid))throw std::runtime_error("invalid LP probe outcome: "+o.failure_reason+" "+o.native_status);
            return o;
        };
        auto analyze=[&](const FixedIntervalMipOutcome& o,const std::string& arm,bool add){
            auto p=pointFrom(d,o);std::map<std::string,double> values;for(const auto& v:o.lp_primal_dual_variable_evidence)values[v.name]=v.primal_value;
            const auto begin=std::chrono::steady_clock::now();bool any=false;std::vector<int> all(d.V);std::iota(all.begin(),all.end(),1);
            for(int k=0;k<d.M;++k){++graphs;auto cut=separateRound63Time(d,p,k);double single=0;
                for(int i=1;i<=d.V;++i)single=std::max(single,evaluateRound63TimeRow(d,p,round63TimeRow(d,k,{i})));
                separation<<count-1<<','<<arm<<','<<k<<','<<cut.violation<<','<<evaluateRound63TimeRow(d,p,round63TimeRow(d,k,all))<<','<<single<<','<<cut.support.size()<<','<<elapsed()<<'\n';
                if(cut.violated){any=true;writeRound63TimeCut(cut,cuts,count-1,0,-1);
                    for(const auto& [name,c]:cut.coefficients){(void)c;terms<<count-1<<','<<k<<','<<name<<','<<values.at(name)<<'\n';}
                    if(add&&rows.size()<256){FixedIntervalMipRequest::AdditionalLinearRow row;row.row_name="r63_cut_"+std::to_string(rows.size());row.scope="global";row.canonical_signature=cut.signature;
                        for(const auto& [name,c]:cut.coefficients){row.variable_names.push_back(name);row.coefficients.push_back(c);}rows.push_back(row);++total_rows;}
                }
            }
            separation_seconds+=std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();return any;
        };
        if(micro){
            std::mt19937 rng(630);std::uniform_real_distribution<double> u(0,1);std::ofstream check(dir/"micro.csv");check<<"query,maxcut,enumeration,native_status,flow_feasible,agrees\n";
            int feasible=0,infeasible=0;
            for(int q=0;q<24;++q){auto p=emptyRound63TimePoint(d);
                if(q%2==0){p.x[0][0][1]=p.x[0][1][2]=p.x[0][2][3]=p.x[0][3][4]=p.x[0][4][0]=1;p.pickup[0][1]=2;p.pickup[0][3]=2;}
                else for(int i=0;i<=d.V;++i){p.pickup[0][i]=u(rng)*8;for(int j=0;j<=d.V;++j)if(i!=j)p.x[0][i][j]=u(rng)*.08;}
                auto cut=separateRound63Time(d,p,0);++graphs;double best=0;
                for(int w=1;w<16;++w){std::vector<int> support;for(int i=1;i<=4;++i)if(w&(1<<(i-1)))support.push_back(i);best=std::max(best,evaluateRound63TimeRow(d,p,round63TimeRow(d,0,support)));}
                if(std::fabs(best-cut.violation)>1e-10)throw std::runtime_error("micro mincut mismatch");
                auto path=dir/("micro_"+std::to_string(q)+".lp");std::ofstream f(path);f<<std::setprecision(17)<<"Minimize\n obj: 0 f_1_0\nSubject To\n";
                for(int i=1;i<=d.V;++i){double a=d.handling*p.pickup[0][i];f<<" balance_"<<i<<":";
                    for(int j=0;j<=d.V;++j)if(i!=j)f<<" + f_"<<i<<'_'<<j;
                    for(int h=1;h<=d.V;++h)if(h!=i)f<<" - f_"<<h<<'_'<<i;
                    for(int h=0;h<=d.V;++h)if(h!=i)a+=d.travel[h][i]*p.x[0][h][i];f<<" = "<<a<<'\n';}
                f<<"Bounds\n";for(int i=1;i<=d.V;++i)for(int j=0;j<=d.V;++j)if(i!=j)f<<" 0 <= f_"<<i<<'_'<<j<<" <= "<<d.upper[i][j]*p.x[0][i][j]<<'\n';f<<"End\n";f.close();
                auto o=solve(path,"micro");bool ok=o.optimal;feasible+=ok;infeasible+=o.infeasible;
                bool agrees=ok==!cut.violated&&(ok||o.infeasible);check<<q<<','<<cut.violation<<','<<best<<','<<o.native_status<<','<<ok<<','<<agrees<<'\n';
                if(!agrees)throw std::runtime_error("micro explicit flow equivalence failure");
            }
            if(!feasible||!infeasible)throw std::runtime_error("micro classes absent");closed=true;
        } else {
            auto baseline=solve(source,"F0");base_obj=baseline.lp_objective_value;savePoint(baseline,dir/"F0_point.csv");analyze(baseline,"F0",false);
            auto flow=dir/"explicit.lp";std::filesystem::copy_file(source,flow);appendRound63TimeModel(in,flow,"explicit");
            auto o=solve(flow,"explicit");explicit_obj=o.lp_objective_value;savePoint(o,dir/"explicit_point.csv");analyze(o,"explicit",false);
            auto simple=dir/"simple.lp";std::filesystem::copy_file(source,simple);appendRound63TimeModel(in,simple,"simple");
            o=solve(simple,"simple");simple_obj=o.lp_objective_value;savePoint(o,dir/"simple_point.csv");analyze(o,"simple",false);
            std::set<std::string> seen;
            o=baseline;
            for(int iteration=0;iteration<64;++iteration){
                const bool violated=analyze(o,"closure",true);closure_obj=o.lp_objective_value;
                if(!violated){closed=true;savePoint(o,dir/"closed_point.csv");break;}
                for(const auto& row:rows)if(!seen.count(row.canonical_signature))seen.insert(row.canonical_signature);
                if(rows.size()!=seen.size())throw std::runtime_error("duplicate violated closure row");
                if(rows.size()>=256||cap-elapsed()<4||count>=67)break;
                o=solve(source,"closure");
            }
        }
        backend->release();const auto stats=backend->stats();
        std::ofstream result(dir/"probe_result.json");result<<std::setprecision(17)<<"{\"optimizer_calls\":"<<count<<",\"query_limit\":"<<(micro?24:67)
            <<",\"maxflow_calls\":"<<graphs<<",\"generated_rows\":"<<total_rows<<",\"closed\":"<<closed<<",\"F0\":"<<base_obj<<",\"explicit\":"<<explicit_obj
            <<",\"simple\":"<<simple_obj<<",\"closure\":"<<closure_obj<<",\"projection_objective_agrees\":"<<(closed&&std::fabs(explicit_obj-closure_obj)<1e-7)
            <<",\"separation_seconds\":"<<separation_seconds<<",\"process_seconds\":"<<elapsed()<<",\"parameter_roundtrip\":"<<stats.parameter_roundtrip_valid<<"}\n";
        std::cout<<"calls "<<count<<" closed "<<closed<<" F0 "<<base_obj<<" explicit "<<explicit_obj<<" closure "<<closure_obj<<'\n';return 0;
    } catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
