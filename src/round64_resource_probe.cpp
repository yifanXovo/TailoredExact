// Seven LPs under one physical cap. Diagnostic original-variable projection;
// no result is an original integer-program certificate or a production cut.
#include "Round64SharedResource.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "FileSha256.hpp"
#include "Parser.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>

using namespace ebrp;
namespace {
void save(const FixedIntervalMipOutcome& o,const std::filesystem::path& path) {
    std::ofstream f(path);f<<std::setprecision(17)<<"variable,value,lower,upper\n";
    for(const auto& v:o.lp_primal_dual_variable_evidence)f<<v.name<<','<<v.primal_value<<','<<v.lower_bound<<','<<v.upper_bound<<'\n';
    if(!f)throw std::runtime_error("point persistence failed");
}
}
int main(int argc,char** argv) {
 try {
    const auto started=std::chrono::steady_clock::now();
    auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count();};
    std::string input,source,expected,output;double T=0,pickup=60,drop=60,cap=120;bool micro=false;
    for(int i=1;i<argc;++i) {
        const std::string a=argv[i];auto value=[&](){if(++i>=argc)throw std::runtime_error("missing argument");return std::string(argv[i]);};
        if(a=="--input")input=value();else if(a=="--model")source=value();else if(a=="--expected-sha")expected=value();
        else if(a=="--out")output=value();else if(a=="--T")T=std::stod(value());else if(a=="--pickup-time")pickup=std::stod(value());
        else if(a=="--drop-time")drop=std::stod(value());else if(a=="--cap")cap=std::stod(value());else if(a=="--micro")micro=true;
        else throw std::runtime_error("unknown argument "+a);
    }
    if(output.empty()||cap<=3||cap>300)throw std::runtime_error("invalid bounded probe cap/output");
    const std::filesystem::path dir(output);std::filesystem::create_directories(dir);Instance in;
    if(micro) {
        in.V=2;in.M=1;in.Q={1};in.initial={0,2,0};in.capacity={0,3,3};in.target={0,1,1};in.weights={0,.5,.5};
        in.total_time_limit=10;in.pickup_time=.5;in.drop_time=.5;in.dist.assign(3,std::vector<double>(3,0));in.dist[1][2]=9.9;
        source=(dir/"source.lp").string();std::ofstream f(source);f<<"Minimize\n obj: 0 load_0_1\nSubject To\n identity: load_0_1 - p_0_1 = 0\nBounds\n";
        const std::map<std::string,double> point={{"x_0_0_1",1},{"x_0_0_2",0},{"x_0_1_0",.1},{"x_0_1_2",.9},{"x_0_2_0",.9},{"x_0_2_1",0},
            {"p_0_1",.5},{"p_0_2",0},{"d_0_1",0},{"d_0_2",.4},{"load_0_1",.5},{"load_0_2",0}};
        f<<std::setprecision(17);for(const auto& [n,v]:point)f<<' '<<n<<" = "<<v<<'\n';f<<"End\n";f.close();expected=fileSha256(source);
    } else {
        if(input.empty()||source.empty()||expected.empty()||fileSha256(source)!=expected)throw std::runtime_error("frozen source required");
        in=parseInstanceFile(input,T,pickup,drop);
    }
    const auto data=prepareRound63Time(in);writeRound63TimeData(data,dir/"resource.json");
    SolveOptions options;options.gurobi_presolve=-1;options.gurobi_seed=0;options.log_path=(dir/"environment.log").string();
    auto backend=makeGurobiFixedIntervalBackend(in,options);if(!backend||!backend->capabilities().available)throw std::runtime_error("Gurobi unavailable");
    std::ofstream calls(dir/"native_calls.csv"),summary(dir/"lp_queries.csv");
    calls<<"query,arm,remaining_seconds,model_sha256,additional_rows\n";
    summary<<std::setprecision(17)<<"query,arm,status,optimal,infeasible,objective,work,solver_seconds,rows,columns,nonzeros,valid,seconds\n";
    int count=0;std::vector<FixedIntervalMipRequest::AdditionalLinearRow> pins;
    auto solve=[&](const std::filesystem::path& path,const std::string& arm) {
        const double remaining=cap-elapsed()-3;
        if(remaining<=0||count>=7)throw std::runtime_error("bounded seven-call probe exhausted");
        FixedIntervalMipRequest req;req.solve_kind=FixedIntervalSolveKind::PaperLpRelaxation;req.leaf_id=arm;
        req.gamma_L=0;req.gamma_U=1;req.verified_cutoff=1e6;req.global_deadline_remaining_seconds=remaining;req.time_limit_seconds=remaining;
        req.canonical_model_path=path;req.canonical_model_fingerprint=fileSha256(path);req.canonical_row_signature=req.canonical_model_fingerprint;
        req.canonical_model_scope=pins.empty()?"diagnostic_target_F0":"diagnostic_fixed_original_point";
        req.native_log_path=dir/(arm+".log");req.capture_lp_primal_dual_evidence=true;
        req.interval_mip_policy="interval-mip-core-no-exhaustive-subset-duration";req.additional_linear_rows=pins;
        calls<<std::setprecision(17)<<count<<','<<arm<<','<<remaining<<','<<req.canonical_model_fingerprint<<','<<pins.size()<<'\n';calls.flush();++count;
        auto o=backend->solve(req);
        bool valid=o.lp_terminal_valid&&o.model_fingerprint_matches_request&&
            ((o.optimal&&o.lp_primal_dual_evidence_available)||o.infeasible);
        summary<<count<<','<<arm<<','<<o.native_status<<','<<o.optimal<<','<<o.infeasible<<','<<o.lp_objective_value<<','<<o.work<<','
            <<o.solver_runtime_seconds<<','<<o.model_linear_constraint_count<<','<<o.model_variable_count<<','<<o.model_nonzero_count<<','<<valid<<','<<elapsed()<<'\n';summary.flush();
        if(!valid)throw std::runtime_error("invalid LP state "+arm+": "+o.failure_reason+" "+o.native_status);
        if(o.optimal)save(o,dir/(arm+"_point.csv"));
        return o;
    };
    std::map<std::string,FixedIntervalMipOutcome> outcomes;
    std::map<std::string,std::filesystem::path> models;
    for(const std::string mode:{"off","q","t","sep","joint"}) {
        auto path=dir/(mode+".lp");std::filesystem::copy_file(source,path);appendRound64SharedModel(in,path,mode);models[mode]=path;
        outcomes[mode]=solve(path,mode);
        if(!outcomes[mode].optimal&&!(micro&&mode=="joint"))throw std::runtime_error("unexpected target infeasibility");
    }
    // The complete original variable set is taken from actual canonical F0,
    // never guessed by filtering unknown names in an extended solution.
    std::map<std::string,double> sep_values;
    for(const auto& v:outcomes.at("sep").lp_primal_dual_variable_evidence)sep_values[v.name]=v.primal_value;
    std::ofstream pinfile(dir/"original_pins.csv");pinfile<<std::setprecision(17)<<"variable,value\n";
    for(const auto& v:outcomes.at("off").lp_primal_dual_variable_evidence) {
        FixedIntervalMipRequest::AdditionalLinearRow row;row.row_name="r64_pin_"+std::to_string(pins.size());
        row.canonical_signature="diagnostic_pin:"+v.name;row.scope="diagnostic_fixed_point";row.sense='=';
        row.rhs=sep_values.at(v.name);row.variable_names={v.name};row.coefficients={1};pins.push_back(row);pinfile<<v.name<<','<<row.rhs<<'\n';
    }
    pinfile.close();const auto sep=solve(models.at("sep"),"pinned_sep"),joint=solve(models.at("joint"),"pinned_joint");
    if(!sep.optimal)throw std::runtime_error("SEP pinned control is not feasible");
    if(micro&&!joint.infeasible)throw std::runtime_error("known strict projection witness lost");
    backend->release();std::ofstream result(dir/"probe_result.json");result<<std::setprecision(17)
        <<"{\"optimizer_calls\":"<<count<<",\"query_limit\":7,\"process_seconds\":"<<elapsed()<<",\"original_variables_pinned\":"<<pins.size()
        <<",\"pinned_sep_feasible\":"<<sep.optimal<<",\"pinned_joint_feasible\":"<<joint.optimal<<",\"pinned_joint_infeasible\":"<<joint.infeasible
        <<",\"parameter_roundtrip\":"<<backend->stats().parameter_roundtrip_valid<<",\"micro\":"<<micro<<"}\n";
    if(!result)throw std::runtime_error("result persistence failed");
    return 0;
 } catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
