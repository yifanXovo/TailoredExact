// Zero-Optimize export through the actual production canonical writer.
#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Parser.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
int main(int argc, char** argv) { try {
    if (argc != 10) throw std::runtime_error("input T pickup drop lambda gL gU cutoff directory");
    auto in=ebrp::parseInstanceFile(argv[1],std::stod(argv[2]),std::stod(argv[3]),std::stod(argv[4]));
    ebrp::SolveOptions opt; ebrp::configurePaperK1AmSfOverrides(opt);
    opt.lambda=std::stod(argv[5]);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened=true;spec.interval_restricted=true;
    spec.gamma_L=std::stod(argv[6]);spec.gamma_U=std::stod(argv[7]);
    spec.add_verified_incumbent_row=true;spec.verified_incumbent=std::stod(argv[8]);
    spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    const std::filesystem::path dir(argv[9]);std::filesystem::create_directories(dir);
    for (const auto& mode : {"off","aggregate","projected"}) {
        opt.round98_state_service=mode;
        const auto a=ebrp::writeCanonicalCompactModel(in,opt,dir/(std::string(mode)+".lp"),spec);
        if (!a.written) throw std::runtime_error(a.failure_reason);
        std::ofstream f(dir/(std::string(mode)+".json"));
        f<<"{\"optimizer_calls\":0,\"mode\":\""<<mode<<"\",\"sha256\":\""<<a.sha256
         <<"\",\"rows\":"<<a.rows<<",\"columns\":"<<a.columns<<",\"nonzeros\":"<<a.nonzeros<<"}\n";
        if(!f)throw std::runtime_error("export receipt write failed");
    }
    return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;} }
