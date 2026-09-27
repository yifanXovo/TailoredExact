#include "CanonicalCompactModel.hpp"
#include "PaperK1AmSf.hpp"
#include "Round50IntervalMip.hpp"
#include "Evaluator.hpp"
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
void require(bool value, const char* message) {
    if (!value) throw std::runtime_error(message);
}
std::string read(const std::filesystem::path& path) {
    std::ifstream file(path);return {(std::istreambuf_iterator<char>(file)),{}};
}
void finiteDisjunction() {
    for (int lower : {0,3,7}) for (int size=1;size<=17;++size) {
        int bits=0;while ((1<<bits)<size) ++bits;
        for (int code=0;code<(1<<bits);++code) {
            int compatible=0;
            for (int value=lower;value<lower+size;++value) {
                bool agrees=true;
                for (int b=0;b<bits;++b)
                    agrees=agrees&&(((value-lower)>>b&1)==(code>>b&1));
                if (agrees) ++compatible;
            }
            require(compatible==(code<size?1:0),"used/unused code not uniquely represented");
        }
        // Every relaxed selector mixture defines valid relaxed code coordinates.
        for (int b=0;b<bits;++b) {
            double code=0;
            for (int value=0;value<size;++value) code+=double(value+1)*(value>>b&1);
            code/=size*(size+1)/2.0;
            require(code>=0&&code<=1,"LP projection bounds invalid");
        }
    }
    // Integral mean inventory is insufficient without code integrality.
    const double Y=.5*2+.5*4, G=.5*.2+.5*.4, Z=.5*2*.2+.5*4*.4;
    require(Y==3&&std::abs(Z-G*Y)>.09,"fractional-selector counterexample lost");
}
void generatedModel() {
    ebrp::Instance in;
    in.V=3;in.M=1;in.Q={3};in.initial={0,0,5,8};
    in.capacity={0,0,8,12};in.target={0,1,4,8};in.weights={0,1,1,1};
    in.min_ratio={0,0,0,0};in.pickup_time=0;in.drop_time=0;in.total_time_limit=10000;
    in.dist.assign(4,std::vector<double>(4,1));
    for (int i=0;i<=3;++i) in.dist[i][i]=0;
    require(ebrp::hasMetricTravelLowerBounds(in),"metric fixture rejected");
    auto nonmetric=in;nonmetric.dist[0][2]=nonmetric.dist[2][0]=10;
    require(!ebrp::hasMetricTravelLowerBounds(nonmetric),"unsafe direct travel bound accepted");
    require(ebrp::verifySolution(in,{{0,{0,2,0},{{2,3,0}}}},.15).feasible,
            "zero-handling loaded-return witness invalid");
    ebrp::SolveOptions options;ebrp::configurePaperK1AmSfOverrides(options);
    ebrp::CanonicalCompactModelSpec spec;
    spec.strengthened=true;spec.interval_restricted=true;spec.gamma_U=1;
    spec.round51_subset_duration_big_m="off";
    const auto dir=std::filesystem::temp_directory_path()/"round67_log_state_test";
    std::filesystem::create_directories(dir);
    spec.station_state_formulation="vd-p";
    const auto one=ebrp::writeCanonicalCompactModel(in,options,dir/"one.lp",spec);
    spec.station_state_formulation="log-vd-p";
    const auto log=ebrp::writeCanonicalCompactModel(in,options,dir/"log.lp",spec);
    require(one.written&&log.written,"inventory model construction failed");
    require(log.station_state_formulation=="log-vd-p","wrong model identity");
    require(log.station_state_selector_variables==15,"unexpected propagated domain size");
    require(log.station_state_code_variables==6,"singleton or nonpower-of-two code count wrong");
    require(log.rows-one.rows==6&&log.columns-one.columns==6,"unexpected encoding size change");
    const auto text=read(log.path);
    const auto binary=text.substr(text.find("Binaries"));
    require(binary.find("state_code_2_0")!=std::string::npos,"code is not binary");
    require(binary.find("state_2_2")==std::string::npos,"selector remains binary");
    require(text.find("state_code_1_")==std::string::npos,"singleton has unnecessary code");
    require(text.find("bit_")==std::string::npos,"old bit-product block remains");
    require(text.find("r64_q_")==std::string::npos,"arc-load mechanism inherited");
    require(text.find("load_0_2")!=std::string::npos,"original node-load formulation removed");
    require(text.find("- state_2_3 - state_2_5 - state_2_7 + state_code_2_0 = 0")
            !=std::string::npos,"offset-domain linking missing");
    require(text.find("- state_2_4 - state_2_5 - state_2_8 + state_code_2_1 = 0")
            !=std::string::npos,"second offset-domain code row missing");
    options.plain_baseline=true;
    require(!ebrp::writeCanonicalCompactModel(in,options,dir/"reject.lp",spec).written,
            "official plain baseline accepted LOG");
    options.plain_baseline=false;options.round65_budget=true;
    require(!ebrp::writeCanonicalCompactModel(in,options,dir/"reject-budget.lp",spec).written,
            "budgeted LOG accepted");
    options.round65_budget=false;spec.station_state_formulation="vd-p";
    const auto again=ebrp::writeCanonicalCompactModel(in,options,dir/"one-again.lp",spec);
    require(again.written&&read(again.path)==read(one.path),"legacy VD-P state leaked");
    const auto policy=ebrp::parseRound50IntervalMipPolicy("round67-log-vd-p");
    require(policy.valid&&policy.station_state_formulation=="log-vd-p"&&
            policy.subset_duration_big_m=="off","LOG policy did not bind to isolated F0");
    std::filesystem::remove_all(dir);
}
}
int main() {
    try {finiteDisjunction();generatedModel();std::cout<<"Round67 log-state mappings and model isolation passed\n";return 0;}
    catch (const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
}
