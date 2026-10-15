#include "Round120NativeProof.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "ProcessPhaseLedger.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iomanip>
#include <limits>
#include <sstream>

namespace ebrp {
namespace {
void require(bool v,const char* message){if(!v)throw std::runtime_error(message);}
double down(double x){return std::nextafter(x,-std::numeric_limits<double>::infinity());}
double up(double x){return std::nextafter(x,std::numeric_limits<double>::infinity());}
double sumUp(double a,double b){return (a==0||b==0||a==-b)?a+b:up(a+b);}
double sumDown(double a,double b){return (a==0||b==0||a==-b)?a+b:down(a+b);}
std::string number(double x){std::ostringstream s;s<<std::setprecision(17)<<x;return s.str();}
bool numeric(const std::string& s){char* end=nullptr;std::strtod(s.c_str(),&end);return end!=s.c_str()&&!*end;}
struct Objective {std::string linear;double constant=0;long long terms=0;};
Objective objective(const std::string& expression) {
    std::istringstream input(expression);std::vector<std::string> tokens;std::string token;
    while(input>>token)tokens.push_back(token);
    Objective out;int sign=1;
    for(std::size_t k=0;k<tokens.size();) {
        if(tokens[k]=="+"||tokens[k]=="-"){sign=tokens[k++]=="+"?1:-1;continue;}
        if(numeric(tokens[k])) {
            const std::string coefficient=tokens[k++];
            if(k==tokens.size()||tokens[k]=="+"||tokens[k]=="-") {
                out.constant+=sign*std::stod(coefficient);sign=1;continue;
            }
            out.linear+=(sign<0?" - ":" + ")+coefficient+" "+tokens[k++];
        } else out.linear+=(sign<0?" - ":" + ")+std::string("1 ")+tokens[k++];
        ++out.terms;sign=1;
    }
    require(out.terms>0&&std::isfinite(out.constant),"round120_invalid_complete_linear_objective");
    return out;
}
}
bool round120Contains(const Round120Pair& p,double l,double u) {
    return std::isfinite(l)&&std::isfinite(u)&&p.a<=l&&l<=u&&u<=p.b;
}
Round120Pair makeRound120Pair(const std::array<Round119Certificate,2>& proof,const std::string& input_sha) {
    Round120Pair p;p.proof=proof;p.input_sha=input_sha;
    p.a=proof[0].parent_lower;p.b=proof[0].parent_upper;p.m=p.a+(p.b-p.a)/2;
    require(std::isfinite(p.a)&&std::isfinite(p.m)&&std::isfinite(p.b)&&p.a<p.m&&p.m<p.b,
        "round120_missing_or_degenerate_root_partition");
    for(int j=0;j<2;++j) {
        const auto& c=proof[j];
        require(c.parent=="L0"&&c.depth==0&&c.side==j&&c.leaf=="L0."+std::to_string(j)&&
            c.parent_lower==p.a&&c.parent_upper==p.b&&c.lower==(j?p.m:p.a)&&c.upper==(j?p.b:p.m)&&
            c.status=="OPTIMAL"&&c.call>0&&!c.model.empty()&&!c.path.empty()&&!c.scope.empty()&&
            std::isfinite(c.cutoff)&&c.cutoff>=0&&std::isfinite(c.bound),"round120_invalid_returned_root_LP_proof");
    }
    // Proven F>=0 permits this weaker fallback, but source contradictions are
    // separately fatal. Numerical LP evidence is not called a rational proof.
    p.beta0=std::max(0.0,down(std::min(proof[0].bound,proof[0].cutoff)-1e-7));
    p.beta1=std::max(0.0,down(std::min(proof[1].bound,proof[1].cutoff)-1e-7));
    return p;
}
Round120Rows round120Rows(const Round120Pair& p,bool conditional,double constant) {
    require(round120Contains(p,p.a,p.b)&&p.a<p.m&&p.m<p.b&&std::isfinite(constant),"round120_invalid_row_input");
    Round120Rows r;r.objective_constant=constant;
    r.lower_base=p.a==0?0:down(p.a);r.lower_delta=down(p.m-r.lower_base);
    for(int k=0;sumUp(r.lower_base,r.lower_delta)>p.m;++k) {
        require(k<32,"round120_lower_endpoint_arithmetic_unresolved");
        r.lower_delta=down(r.lower_delta-(sumUp(r.lower_base,r.lower_delta)-p.m));
    }
    r.upper_base=up(p.m);r.upper_delta=up(p.b-r.upper_base);
    for(int k=0;sumDown(r.upper_base,r.upper_delta)<p.b;++k) {
        require(k<32,"round120_upper_endpoint_arithmetic_unresolved");
        r.upper_delta=up(r.upper_delta+(p.b-sumDown(r.upper_base,r.upper_delta)));
    }
    const double beta0=conditional?p.beta0:std::min(p.beta0,p.beta1);
    const double beta1=conditional?p.beta1:beta0;
    r.objective_base=(beta0==constant)?0:down(beta0-constant);
    for(int k=0;sumUp(r.objective_base,constant)>beta0;++k) {
        require(k<32,"round120_objective_h0_arithmetic_unresolved");
        r.objective_base=down(r.objective_base-(sumUp(r.objective_base,constant)-beta0));
    }
    if(!conditional)
        while(sumUp(sumUp(r.objective_base,0),constant)>beta0)r.objective_base=down(r.objective_base);
    if(conditional&&beta1!=beta0) {
        r.objective_delta=down(beta1-constant-r.objective_base);
        for(int k=0;sumUp(sumUp(r.objective_base,r.objective_delta),constant)>beta1;++k) {
            require(k<32,"round120_objective_h1_arithmetic_unresolved");
            const double excess=sumUp(sumUp(r.objective_base,r.objective_delta),constant)-beta1;
            r.objective_delta=down(r.objective_delta-excess);
        }
    }
    require(round120Endpoints(r,p,conditional),"round120_outward_endpoint_check_failed");return r;
}
bool round120Endpoints(const Round120Rows& r,const Round120Pair& p,bool conditional) {
    const double beta0=conditional?p.beta0:std::min(p.beta0,p.beta1);
    const double beta1=conditional?p.beta1:beta0;
    return r.lower_base<=p.a&&sumUp(r.lower_base,r.lower_delta)<=p.m&&
        r.upper_base>=p.m&&sumDown(r.upper_base,r.upper_delta)>=p.b&&
        sumUp(r.objective_base,r.objective_constant)<=beta0&&
        sumUp(sumUp(r.objective_base,r.objective_delta),r.objective_constant)<=beta1;
}
CanonicalCompactModelArtifact extendRound120Artifact(const CanonicalCompactModelArtifact& base,
    const Round120Pair& p,bool conditional,const std::filesystem::path& path) {
    require(base.written&&!base.round120_extended&&base.interval_restricted&&
        round120Contains(p,base.gamma_L,base.gamma_U)&&fileSha256(base.path)==base.sha256,
        "round120_base_artifact_identity_or_scope_failed");
    require(!std::filesystem::exists(path),"round120_extension_output_already_exists");
    std::ifstream input(base.path);std::ostringstream material;material<<input.rdbuf();require(bool(input),"round120_base_read_failed");
    std::string text=material.str();
    const auto start=text.find(" obj: "),end=text.find("\nSubject To\n");
    require(start!=std::string::npos&&end!=std::string::npos&&start<end&&text.find("r120_h")==std::string::npos,
        "round120_objective_or_duplicate_install_failed");
    const auto obj=objective(text.substr(start+6,end-start-6));const auto r=round120Rows(p,conditional,obj.constant);
    std::ostringstream rows;rows<<std::setprecision(17)
        <<" r120_g_lower: G - "<<r.lower_delta<<" r120_h >= "<<r.lower_base<<'\n'
        <<" r120_g_upper: G - "<<r.upper_delta<<" r120_h <= "<<r.upper_base<<'\n'
        <<" r120_f_lower:"<<obj.linear;
    if(r.objective_delta!=0)rows<<(r.objective_delta>0?" - ":" + ")<<number(std::fabs(r.objective_delta))<<" r120_h";
    rows<<" >= "<<r.objective_base<<'\n';
    const auto bounds=text.find("Bounds\n");require(bounds!=std::string::npos,"round120_bounds_section_missing");
    text.insert(bounds,rows.str());
    text.insert(text.find("Bounds\n")+7," 0 <= r120_h <= 1\n");
    const auto binary=text.find("Binaries\n");
    require(binary!=std::string::npos,"round120_original_binary_section_missing");
    text.insert(binary+9," r120_h\n");
    {std::ofstream output(path);output<<text;output.close();require(bool(output),"round120_extension_write_failed");}
    CanonicalCompactModelArtifact a=base;a.path=path;a.sha256=fileSha256(path);
    a.row_signature=base.row_signature+"|round120:"+a.sha256;
    a.model_scope=base.model_scope+"_round120_original_projection_"+(conditional?"d1":"d0");
    a.round120_extended=true;a.round120_base_sha=base.sha256;a.round120_conditional=conditional;
    a.rows+=3;a.columns+=1;a.nonzeros+=4+obj.terms+(r.objective_delta!=0);
    // Bind actual decimal literals; independent Fraction audits also check
    // their exact sums against original binary64 endpoints and qualified beta.
    std::ofstream audit(path.string()+".round120.json");audit<<std::setprecision(17)
        <<"{\"base_SHA\":"<<std::quoted(base.sha256)<<",\"SHA\":"<<std::quoted(a.sha256)
        <<",\"conditional\":"<<(conditional?"true":"false")<<",\"a\":"<<p.a<<",\"m\":"<<p.m<<",\"b\":"<<p.b
        <<",\"beta0\":"<<p.beta0<<",\"beta1\":"<<p.beta1<<",\"objective_constant\":"<<obj.constant
        <<",\"lower_base\":"<<std::quoted(number(r.lower_base))<<",\"lower_delta\":"<<std::quoted(number(r.lower_delta))
        <<",\"upper_base\":"<<std::quoted(number(r.upper_base))<<",\"upper_delta\":"<<std::quoted(number(r.upper_delta))
        <<",\"objective_base\":"<<std::quoted(number(r.objective_base))<<",\"objective_delta\":"<<std::quoted(number(r.objective_delta))
        <<",\"rows_added\":3,\"columns_added\":1,\"native_fixing_or_branching\":\"unknown\"}\n";
    audit.close();require(bool(audit),"round120_coefficient_audit_write_failed");return a;
}
Round120NativeProof::Round120NativeProof(const Instance& in,const SolveOptions& opt,const std::filesystem::path& path,
    double a,double b,const std::vector<RoutePlan>& own):instance_(in),options_(opt),events_(path),a_(a),b_(b) {
    require(bool(events_),"round120_event_open_failed");observe(own,0);
}
void Round120NativeProof::record(const std::string& kind,const std::string& fields) {
    events_<<std::setprecision(17)<<"{\"sequence\":"<<++sequence_<<",\"kind\":"<<std::quoted(kind)
        <<",\"process_seconds\":"<<processElapsedSeconds(options_);
    if(!fields.empty())events_<<','<<fields;events_<<"}\n";events_.flush();require(bool(events_),"round120_event_write_failed");
}
void Round120NativeProof::observe(const std::vector<RoutePlan>& routes,long long call) {
    const auto v=verifySolution(instance_,routes,options_.lambda);
    require(v.feasible&&v.errors.empty()&&std::isfinite(v.objective)&&std::isfinite(v.G),"round120_physical_observer_rejected");
    for(int j=0;j<2;++j)if(present_[j]) {
        const auto& c=pending_[j];
        if(c.lower<=v.G&&v.G<=c.upper&&v.objective<=c.cutoff&&v.objective+1e-7<c.bound) {
            failed_=true;record("revoked","\"call\":"+std::to_string(call)+",\"reason\":\"same_scope_counterexample_all_dependencies_revoked\"");
            throw std::runtime_error("PROOF_RELIABILITY_PRIORITY: round120_root_source_counterexample");
        }
    }
    bool duplicate=false;for(const auto& old:witnesses_)if(old.final_inventory==v.final_inventory)duplicate=true;
    if(!duplicate)witnesses_.push_back(v);
}
void Round120NativeProof::add(const Round119Certificate& c) {
    if(c.parent!="L0"||c.depth!=0||c.parent_lower!=a_||c.parent_upper!=b_)return;
    require(!failed_,"round120_rejected_source_reused");
    if(decided_||ready_){record("late_root_proof_ignored","\"call\":"+std::to_string(c.call));return;}
    require(c.side==0||c.side==1,"round120_invalid_side");
    require(!present_[c.side],"round120_root_proof_overwrite");
    require(fileSha256(c.path)==c.model,"round120_source_model_changed");
    pending_[c.side]=c;present_[c.side]=true;
    for(const auto& v:witnesses_)if(c.lower<=v.G&&v.G<=c.upper&&v.objective<=c.cutoff&&v.objective+1e-7<c.bound) {
        failed_=true;record("revoked","\"reason\":\"returned_source_counterexample\"");
        throw std::runtime_error("PROOF_RELIABILITY_PRIORITY: round120_returned_root_LP_counterexample");
    }
    std::ostringstream s;s<<std::setprecision(17)<<"\"side\":"<<c.side<<",\"call\":"<<c.call
        <<",\"model\":"<<std::quoted(c.model)<<",\"path\":"<<std::quoted(c.path)<<",\"scope\":"<<std::quoted(c.scope)
        <<",\"status\":"<<std::quoted(c.status)<<",\"lower\":"<<c.lower<<",\"upper\":"<<c.upper
        <<",\"cutoff\":"<<c.cutoff<<",\"bound\":"<<c.bound;
    record("paid_root_LP_returned",s.str());
    if(present_[0]&&present_[1]) {
        pair_=makeRound120Pair(pending_,fileSha256(instance_.path));ready_=true;
        record("root_pair_registered","\"beta0\":"+number(pair_.beta0)+",\"beta1\":"+number(pair_.beta1));
    }
}
bool Round120NativeProof::firstInteger(const std::string& leaf,double l,double u,double remaining) {
    require(!failed_,"round120_invalid_dependencies_before_integer");
    if(decided_)return installed_;
    // If original AM split the root, the first descendant MIP seals nonexposure.
    decided_=true;installed_=leaf=="L0"&&ready_&&round120Contains(pair_,l,u)&&remaining>0;
    record(installed_?"root_install_admitted":"not_exposed",
        "\"leaf\":"+std::string("\"")+leaf+"\",\"pair_complete\":"+(ready_?"true":"false")+
        ",\"deadline_remaining\":"+number(std::max(0.0,remaining)));
    return installed_;
}
const Round120Pair& Round120NativeProof::pair() const {
    require(ready_&&!failed_,"round120_pair_unavailable_or_revoked");return pair_;
}
void Round120NativeProof::savePair(const std::filesystem::path& path) const {
    const auto& p=pair();std::ofstream f(path);f<<std::setprecision(17)<<"{\"a\":"<<p.a<<",\"m\":"<<p.m<<",\"b\":"<<p.b
        <<",\"beta0\":"<<p.beta0<<",\"beta1\":"<<p.beta1<<",\"input_SHA\":"<<std::quoted(p.input_sha)<<",\"proofs\":[";
    for(int j=0;j<2;++j){if(j)f<<',';const auto& c=p.proof[j];f<<"{\"side\":"<<j<<",\"call\":"<<c.call
        <<",\"epoch\":"<<c.epoch<<",\"model\":"<<std::quoted(c.model)<<",\"path\":"<<std::quoted(c.path)
        <<",\"scope\":"<<std::quoted(c.scope)<<",\"cutoff\":"<<c.cutoff<<",\"bound\":"<<c.bound
        <<",\"available_seconds\":"<<c.available_seconds<<'}';}
    f<<"],\"evidence_margin\":1e-7,\"rational_solver_certificate\":false}\n";f.close();require(bool(f),"round120_pair_write_failed");
}
}
