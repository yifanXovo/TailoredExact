#pragma once
#include "Round146Research.hpp"

namespace ebrp {
namespace round148_detail {
inline void require(bool ok,const std::string& why){if(!ok)throw std::runtime_error("round148_"+why);}
// Each primitive encloses its exact real result. Slope selection is approximate;
// validity depends only on the subsequent enclosure at the actual finite b.
struct Interval {double lo=0,hi=0;};
inline double dn(double x){require(std::isfinite(x),"finite_arithmetic");return std::nextafter(x,-std::numeric_limits<double>::infinity());}
inline double up(double x){require(std::isfinite(x),"finite_arithmetic");return std::nextafter(x,std::numeric_limits<double>::infinity());}
inline Interval val(double x){require(std::isfinite(x),"finite_input");return {x,x};}
inline Interval add(Interval a,Interval b){if(a.lo==0&&a.hi==0)return b;if(b.lo==0&&b.hi==0)return a;return {dn(a.lo+b.lo),up(a.hi+b.hi)};}
inline Interval neg(Interval a){return {-a.hi,-a.lo};}
inline Interval sub(Interval a,Interval b){return add(a,neg(b));}
inline Interval mul(Interval a,Interval b){
    if((a.lo==0&&a.hi==0)||(b.lo==0&&b.hi==0))return {0,0};
    const double p[]={a.lo*b.lo,a.lo*b.hi,a.hi*b.lo,a.hi*b.hi};
    return {dn(*std::min_element(p,p+4)),up(*std::max_element(p,p+4))};
}
inline Interval div(Interval a,Interval b){require(b.lo>0,"positive_divisor");return mul(a,{dn(1./b.hi),up(1./b.lo)});}
inline Interval phi(Interval r,double t,int n){
    const auto v=sub(div(val(1),val(n)),div(r,val(t)));
    return {std::max(0.,v.lo),std::max(0.,v.hi)};
}
struct Selection {
    round143_detail::Row row{"r148_shared_S",{},'>',0};
    std::vector<double> slopes;
    double S=0,violation=0,seconds=0;
    std::string kind="affine_low";
};
inline Selection select(const round146_detail::Block& block,const std::vector<double>& c,
                        const std::map<std::string,double>& point){
    const auto tick=std::chrono::steady_clock::now();Selection out;const int n=int(c.size())-1;
    require(block.applicable&&n>0,"positive_domain");out.slopes.assign(n+1,0);
    long double S=0;for(int i=1;i<=n;++i)S+=(long double)c[i]*point.at("Y_"+std::to_string(i));out.S=double(S);
    std::vector<std::vector<const round146_detail::StateBound*>> states(n+1);
    for(const auto& st:block.states)if(st.feasible)states.at(st.i).push_back(&st);
    double ray=1e-8;int ray_i=0;bool ray_lower=false;
    for(int i=1;i<=n;++i){
        std::vector<double> candidates{0};long double low=0,high=0;
        for(const auto* st:states[i]){
            const long double r=(long double)c[i]*st->y;
            std::vector<long double> ts{st->lower,st->upper};
            if(st->lower<=n*r&&n*r<=st->upper)ts.push_back(n*r);
            const auto p=[&](long double t){return std::max(0.L,1.L/n-r/t);};
            for(std::size_t a=0;a<ts.size();++a)for(std::size_t b=a+1;b<ts.size();++b)if(ts[a]!=ts[b]){
                const double slope=double((p(ts[b])-p(ts[a]))/(ts[b]-ts[a]));
                if(std::isfinite(slope))candidates.push_back(slope);
            }
            const double mass=point.at(round143_detail::state(i,st->y));
            require(std::isfinite(mass)&&mass>=-1e-6&&mass<=1+1e-6,"primal_mass");
            low+=(long double)mass*st->lower;high+=(long double)mass*st->upper;
        }
        if(low-S>ray){ray=double(low-S);ray_i=i;ray_lower=true;}
        if(S-high>ray){ray=double(S-high);ray_i=i;ray_lower=false;}
        std::sort(candidates.begin(),candidates.end());candidates.erase(std::unique(candidates.begin(),candidates.end()),candidates.end());
        long double best=-std::numeric_limits<long double>::infinity();double chosen=0;
        for(double b:candidates){
            long double H=b*S;
            for(const auto* st:states[i]){
                const long double r=(long double)c[i]*st->y;
                const auto p=[&](long double t){return std::max(0.L,1.L/n-r/t)-b*t;};
                long double a=std::min(p(st->lower),p(st->upper));
                if(st->lower<=n*r&&n*r<=st->upper)a=std::min(a,-b*n*r);
                H+=point.at(round143_detail::state(i,st->y))*a;
            }
            if(H>best||(H==best&&std::fabs(b)<std::fabs(chosen))){best=H;chosen=b;}
        }
        out.slopes[i]=chosen;
    }
    Interval beta{0,0};for(int i=1;i<=n;++i)beta=add(beta,val(out.slopes[i]));
    if(!ray_i)out.row.coefficients["G"]=1;
    else out.kind=ray_lower?"moment_lower":"moment_upper";
    for(const auto& st:block.states)if(st.feasible){
        const auto r=mul(val(c[st.i]),val(st.y));Interval q;
        if(ray_i){
            const auto bound=val(st.i==ray_i?(ray_lower?st.lower:st.upper):0.);
            q=ray_lower?sub(bound,r):sub(r,bound);
        }else{
            const double b=out.slopes[st.i];
            double a=std::min(sub(phi(r,st.lower,n),mul(val(b),val(st.lower))).lo,
                              sub(phi(r,st.upper,n),mul(val(b),val(st.upper))).lo);
            const auto kink=mul(val(n),r);
            // If the exact kink could be in the interval, include its full
            // enclosure. Including an extra candidate only weakens a minimum.
            if(kink.lo<=st.upper&&kink.hi>=st.lower)a=std::min(a,neg(mul(val(b),kink)).lo);
            q=add(val(a),mul(beta,r));
        }
        double coefficient=q.lo;
        if(coefficient!=0&&std::fabs(coefficient)<1e-12)coefficient=-1e-12;
        if(coefficient)out.row.coefficients[round143_detail::state(st.i,st.y)]=-coefficient;
    }
    long double lhs=0;for(const auto& term:out.row.coefficients)lhs+=(long double)term.second*point.at(term.first);
    out.violation=double(-lhs);out.seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-tick).count();return out;
}
inline void emitRow(std::ostream& f,const round143_detail::Row& row){
    f<<"{\"name\":"<<std::quoted(row.name)<<",\"sense\":\">\",\"rhs\":0,\"terms\":{";bool first=true;
    for(const auto& t:row.coefficients){if(!first)f<<',';first=false;f<<std::quoted(t.first)<<':'<<t.second;}f<<"}}";
}
}
struct Round148Controls {
    bool enabled=false,attempted=false,ready=false;
    double gamma_L=0,gamma_U=0,cutoff=0;
    round148_detail::Selection selection;
    std::map<std::string,round143_detail::Row> expected;
};
inline Round148Controls& round148(){static Round148Controls c;return c;}
inline void round148ResetRun(){const bool enabled=round148().enabled;round148()=Round148Controls{};round148().enabled=enabled;}
namespace round148_detail {
inline void generate(const FixedIntervalMipRequest& request,const FixedIntervalMipOutcome& out,
                     const std::filesystem::path& path){
    auto& c=round148();require(c.enabled&&!c.attempted&&request.leaf_id=="L0","once_initial_root");c.attempted=true;
    c.gamma_L=request.gamma_L;c.gamma_U=request.gamma_U;c.cutoff=request.verified_cutoff;
    std::map<std::string,double> point;
    const bool qualified=round146().generated&&round146().block.applicable&&out.lp_terminal_valid&&out.optimal&&
        out.exact_zero_gap_roundtrip&&out.model_fingerprint_matches_request&&out.feasibility_consistency_gate&&out.lp_primal_dual_evidence_available;
    if(qualified){
        for(const auto& v:out.lp_primal_dual_variable_evidence)if(v.name=="G"||v.name.rfind("Y_",0)==0||v.name.rfind("state_",0)==0){
            require(v.lower_bound>=0,"nonnegative_selector_or_inventory");require(point.emplace(v.name,v.primal_value).second,"duplicate_primal");
        }
        c.selection=select(round146().block,round146().ratios,point);c.ready=c.selection.violation>1e-8;
    }
    std::ofstream f(path);f<<std::setprecision(17)<<"{\"qualified_input\":"<<(qualified?"true":"false")<<",\"ready\":"<<(c.ready?"true":"false")
        <<",\"source_call\":"<<out.native_evidence_call<<",\"source_model_SHA\":"<<std::quoted(request.canonical_model_fingerprint)
        <<",\"source_scope\":"<<std::quoted(request.canonical_model_scope)<<",\"gamma_L\":"<<request.gamma_L<<",\"gamma_U\":"<<request.gamma_U
        <<",\"cutoff\":"<<request.verified_cutoff<<",\"source_L\":"<<out.native_bound<<",\"kind\":"<<std::quoted(c.selection.kind)
        <<",\"generation_seconds\":"<<c.selection.seconds<<",\"violation\":"<<c.selection.violation<<",\"slopes\":[";
    for(std::size_t i=1;i<c.selection.slopes.size();++i){if(i>1)f<<',';f<<c.selection.slopes[i];}f<<"],\"row\":";emitRow(f,c.selection.row);
    f<<",\"point\":{";bool first=true;for(const auto& p:point){if(!first)f<<',';first=false;f<<std::quoted(p.first)<<':'<<p.second;}
    f<<"},\"states\":[";first=true;for(const auto& s:round146().block.states){if(!first)f<<',';first=false;
        f<<"{\"i\":"<<s.i<<",\"y\":"<<s.y<<",\"feasible\":"<<(s.feasible?"true":"false")<<",\"lower\":"<<s.lower<<",\"upper\":"<<s.upper<<'}';}
    f<<"],\"new_columns\":0,\"source_solves\":0,\"max_added_root_LP\":1}\n";f.close();require(bool(f),"selection_evidence_write");
}
inline CanonicalCompactModelArtifact embed(const Instance& instance,const CanonicalCompactModelArtifact& base,
                                         double cutoff,const std::filesystem::path& path){
    auto& c=round148();if(!c.ready)return base;
    require(round146().input_sha==fileSha256(instance.path)&&base.gamma_L>=c.gamma_L&&base.gamma_U<=c.gamma_U&&cutoff<=c.cutoff,"embedding_scope");
    const auto support=round141_detail::supports(round141_detail::material(base.path),instance.V);auto row=c.selection.row;
    for(int i=1;i<=instance.V;++i)require(std::includes(round146().support[i].begin(),round146().support[i].end(),support[i].begin(),support[i].end()),"support_expanded");
    for(auto it=row.coefficients.begin();it!=row.coefficients.end();){
        if(it->first=="G"){++it;continue;}const auto parts=round141_detail::split(it->first,'_');require(parts.size()==3,"selector_name");
        const int i=std::stoi(parts[1]),y=std::stoi(parts[2]);
        if(!std::binary_search(support.at(i).begin(),support.at(i).end(),y))it=row.coefficients.erase(it);else ++it;
    }
    const auto gd=round146().expected.find(base.sha256);require(gd!=round146().expected.end(),"GD_expected_base_missing");
    auto out=round144_detail::append(base,{row},{},path,"shared_S");
    out.model_scope=base.model_scope+"_round148_shared_S";out.row_signature=base.row_signature+"|round148:"+out.sha256;
    round146().expected.emplace(out.sha256,gd->second);c.expected.emplace(out.sha256,std::move(row));return out;
}
}
}
