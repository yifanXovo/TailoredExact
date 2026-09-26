#include "Round61Candidates.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>

int main(int argc,char** argv) {
    try {
        std::string input,mode="batch";
        std::filesystem::path out;
        double T=3600,pickup=60,drop=60,lambda=.15;
        for(int i=1;i<argc;++i) {
            std::string a=argv[i];
            auto value=[&]() { if(++i>=argc) throw std::runtime_error("missing value"); return std::string(argv[i]); };
            if(a=="--input") input=value(); else if(a=="--out") out=value();
            else if(a=="--T") T=std::stod(value());
            else if(a=="--pickup-time") pickup=std::stod(value());
            else if(a=="--drop-time") drop=std::stod(value());
            else if(a=="--lambda") lambda=std::stod(value());
            else if(a=="--mode") mode=value(); else throw std::runtime_error("unknown argument "+a);
        }
        if(input.empty() || out.empty() || (mode!="batch" && mode!="prefix-off" && mode!="prefix-on"))
            throw std::runtime_error("invalid candidate command");
        std::filesystem::create_directories(out);
        auto in=ebrp::parseInstanceFile(input,T,pickup,drop);
        std::ofstream identity(out/"parsed.json");
        identity<<std::setprecision(17)<<"{\"V\":"<<in.V<<",\"M\":"<<in.M<<",\"T\":"<<in.total_time_limit
                <<",\"pickup\":"<<in.pickup_time<<",\"drop\":"<<in.drop_time<<",\"lambda\":"<<lambda
                <<",\"input_sha256\":\""<<ebrp::fileSha256(input)<<"\",\"Q\":[";
        for(size_t k=0;k<in.Q.size();++k) identity<<(k?",":"")<<in.Q[k];
        identity<<"]}\n";
        std::ofstream summary(out/"quality.csv"); summary<<std::setprecision(17);
        summary<<"method,F,G,P,seconds,stations,pickup,drop,maximum_duration,quantity_evaluations,pairs,blocks,stop,verified,first_nonempty_seconds\n";
        auto report=[&](const std::string& label,const ebrp::VerifiedBrpCandidate& c,double seconds,
                        long long eval,long long pairs,int blocks,const std::string& stop,double first=-1.0) {
            auto v=ebrp::verifySolution(in,c.routes,lambda);
            int ns=0,np=0,nd=0; double maxd=0;
            for(const auto& r:c.routes) for(const auto& o:r.operations) { ++ns; np+=o.pickup; nd+=o.drop; }
            for(double d:v.route_duration) maxd=std::max(maxd,d);
            summary<<label<<','<<v.objective<<','<<v.G<<','<<v.P<<','<<seconds<<','<<ns<<','<<np<<','<<nd<<','
                   <<maxd<<','<<eval<<','<<pairs<<','<<blocks<<','<<stop<<','<<v.feasible<<','<<first<<'\n';
            ebrp::writeRound61Witness(out/(label+"_witness.json"),in,lambda,c);
        };
        if(mode=="batch") {
            ebrp::Round60ConstructionInput o; o.desired_inventory=in.target;
            const auto legacy=ebrp::constructRound60BrpCandidate(in,lambda,o);
            ebrp::VerifiedCandidateStore fallback;
            fallback.consider(in,lambda,{},"LEGACY60-empty","original_problem");
            report("LEGACY60",legacy.generated?legacy.candidate:fallback.best(),
                   legacy.generation_seconds,legacy.objective_evaluations,0,0,legacy.termination_reason,legacy.first_nonempty_seconds);
            const auto block=ebrp::constructRound61Block(in,lambda);
            report("BLOCK",block.candidate,block.seconds,block.quantity_evaluations,
                   block.evaluated_pairs,block.completed_blocks,block.stop_reason,
                   block.trajectory.size()>1?block.trajectory[1].seconds:-1);
            const auto repaired=ebrp::repairRound61Block(in,lambda,block.candidate);
            report("BLOCK-R",repaired.candidate,block.seconds+repaired.seconds,
                   block.quantity_evaluations+repaired.quantity_evaluations,
                   block.evaluated_pairs+repaired.evaluated_pairs,
                   block.completed_blocks+repaired.completed_blocks,repaired.stop_reason,
                   block.trajectory.size()>1?block.trajectory[1].seconds:-1);
            std::ofstream repair_trace(out/"block_repair_trajectory.csv"); repair_trace<<std::setprecision(17);
            repair_trace<<"round,evaluations,seconds,F,G,P,stations,pickup,drop,blocks,maximum_duration\n";
            for(const auto& t:repaired.trajectory) repair_trace<<t.round<<','<<t.evaluations<<','<<t.seconds<<','
                <<t.F<<','<<t.G<<','<<t.P<<','<<t.stations<<','<<t.pickup<<','<<t.drop<<','<<t.blocks<<','<<t.maximum_duration<<'\n';
            std::ofstream trace(out/"block_trajectory.csv"); trace<<std::setprecision(17);
            trace<<"round,evaluations,seconds,F,G,P,stations,pickup,drop,blocks,maximum_duration\n";
            for(const auto& t:block.trajectory) trace<<t.round<<','<<t.evaluations<<','<<t.seconds<<','
                <<t.F<<','<<t.G<<','<<t.P<<','<<t.stations<<','<<t.pickup<<','<<t.drop<<','<<t.blocks<<','<<t.maximum_duration<<'\n';
            std::ofstream costs(out/"block_costs.json"); costs<<std::setprecision(17)
                <<"{\"cheap_pairs\":"<<block.cheap_pairs<<",\"scan_seconds\":"<<block.scan_seconds
                <<",\"evaluation_seconds\":"<<block.evaluation_seconds<<",\"accept_seconds\":"<<block.accept_seconds
                <<",\"verification_seconds\":"<<block.verification_seconds<<"}\n";
        }
        const auto hga=ebrp::constructRound61Prefix(in,lambda,nullptr,mode!="prefix-off",out);
        ebrp::VerifiedCandidateStore hs;
        hs.consider(in,lambda,ebrp::normalizeRound61Routes(in,lambda,hga.routes),"PREFIX","original_problem");
        if(!hga.found || !hs.hasBest()) throw std::runtime_error("PREFIX failed to return legal snapshot");
        report("PREFIX",hs.best(),hga.wall_time_seconds,0,0,0,
               hga.global_deadline_reached?"safety_deadline":"initialization_plus_16_generations",hga.first_nonempty_seconds);
        if(mode=="batch") {
            const auto repaired=ebrp::repairRound61Block(in,lambda,hs.best());
            report("PREFIX-R",repaired.candidate,hga.wall_time_seconds+repaired.seconds,
                   repaired.quantity_evaluations,repaired.evaluated_pairs,
                   repaired.completed_blocks,repaired.stop_reason,hga.first_nonempty_seconds);
        }
        std::ofstream cost(out/"prefix_costs.json"); cost<<std::setprecision(17)
            <<"{\"generations\":"<<hga.total_generations<<",\"decoder_calls\":"<<hga.decoder_calls
            <<",\"initialization_seconds\":"<<hga.initialization_seconds<<",\"decoder_seconds\":"<<hga.decoder_seconds
            <<",\"observer_seconds\":"<<hga.observer_seconds<<",\"conversion_seconds\":"<<hga.conversion_seconds
            <<",\"hash_seconds\":"<<hga.hash_seconds<<",\"copy_seconds\":"<<hga.copy_seconds
            <<",\"verification_seconds\":"<<hga.candidate_verification_seconds<<",\"ledger_seconds\":"<<hga.ledger_seconds
            <<",\"total_seconds\":"<<hga.wall_time_seconds<<",\"evidence_persisted\":"<<hga.candidate_evidence_persisted
            <<",\"published\":"<<hga.published_candidate_count<<"}\n";
        std::cout<<"Round61 candidate "<<mode<<" complete\n";
        return 0;
    } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
