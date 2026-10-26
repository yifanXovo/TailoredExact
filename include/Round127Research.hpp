#pragma once
#include "Instance.hpp"
#include "Round137Research.hpp"
#include <filesystem>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace ebrp {
// Process-local, explicitly selected diagnostics. No SolveOptions ABI change:
// the frozen production archive can be linked with replaced translation units.
// Nothing chooses a mode from an instance, filename, size, Seed or elapsed time.
struct Round127Controls {
    std::string mode = "off"; // off|p|mb|md|mr|mg|ms2|md-r|s2-root
    std::string parameter_file;
    int mip_focus = 0;
    int cuts = -1;
};
inline Round127Controls& round127() { static Round127Controls c; return c; }
inline bool round127Mb() {
    const auto& m=round127().mode;
    return m=="mb" || m=="md" || m=="mr" || m=="mg" || m=="ms2" || m=="md-r" || m=="s2-root";
}
inline bool round128InclusiveRoot() {
    return round127().mode=="md-r" || round127().mode=="s2-root";
}
inline bool round127Md() { return round127().mode=="md" || round128InclusiveRoot(); }
// This named proof shortcut is not an inequality valid for the inclusive
// F<=U0 physical set. Preserve the penalty bound and all genuine domain rows.
// Historical predicate retained for source compatibility. Since R133 neither
// shared nor fallback emitter inserts this artificial infeasibility marker.
inline bool round128EmitIntervalNoImproverDomainClosure() {
    return !round128InclusiveRoot();
}
inline bool round127EmitCR() { return round127().mode!="mr" && !round137().delete_cr; }
inline bool round127EmitCG() { return round127().mode!="mg" && !round137().delete_cg; }
inline bool round127EmitTriple() {
    return round127().mode!="ms2" && round127().mode!="s2-root";
}
inline void round127Validate(const SolveOptions& opt) {
    auto& c=round127();
    if(c.mode!="off" && c.mode!="p" && !round127Mb())
        throw std::runtime_error("Invalid Round127 mode");
    if(round127Mb() && (opt.method!="gcap-frontier" ||
       opt.algorithm_preset!="research-round83-vds-equal-net-exchange" ||
       opt.round98_state_service!="m-binary" || !opt.k1_am_sf_controller_enabled ||
       !opt.round68_verified_start || opt.round120_native_proof!="off" ||
       opt.round119_proof_contraction || opt.round90_lp_g_split ||
       opt.round112_ens_start_compact || opt.round65_budget ||
       opt.round43_envelope_refinement!="off" ||
       opt.round44_envelope_tail_repair!="off" ||
       opt.round45_adaptive_parametric_partition!="off"))
        throw std::runtime_error("Round127 requires isolated frozen M-B");
    if(c.mode=="p" && (opt.method!="gurobi" || !opt.plain_baseline ||
       opt.algorithm_preset!="custom" || opt.gurobi_hga_start ||
       opt.round112_ens_start_compact))
        throw std::runtime_error("Round127 P requires original cold compact");
    if(c.parameter_file.empty())return;
    if(c.mode!="p")throw std::runtime_error("Round127 parameters are P-only");
    std::ifstream in(c.parameter_file);
    if(!in)throw std::runtime_error("Round127 parameter file unavailable");
    std::string line;bool focus=false,cuts=false;
    while(std::getline(in,line)) {
        const auto comment=line.find('#');if(comment!=std::string::npos)line.resize(comment);
        std::istringstream row(line);std::string key,extra;int value=0;
        if(!(row>>key))continue;
        if(!(row>>value) || (row>>extra))throw std::runtime_error("Malformed Round127 parameter");
        if(key=="MIPFocus" && !focus && value>=0 && value<=3) { c.mip_focus=value;focus=true; }
        else if(key=="Cuts" && !cuts && (value==-1 || value==2)) { c.cuts=value;cuts=true; }
        else throw std::runtime_error("Round127 permits only one MIPFocus and Cuts entry");
    }
}
}
