// Fixed zero-Optimize native qualification. Injected finite-domain proof
// values below are explicitly analytic fixtures, never solver certificates.
#include "round120_qualification_support.hpp"
#include "Round120NativeProof.hpp"
#include <array>

namespace {
std::vector<std::vector<RoutePlan>> independent_fleets(const Instance& in) {
    require(in.M==1,"finite exhaustive single-vehicle qualification scope");
    std::vector<std::vector<RoutePlan>> all;std::vector<int> net(in.V+1);
    std::function<void(int)> enumerate_states=[&](int i) {
        if(i<=in.V) {
            for(int move=-in.initial[i];move<=in.capacity[i]-in.initial[i];++move){net[i]=move;enumerate_states(i+1);}return;
        }
        std::vector<int> order;for(int j=1;j<=in.V;++j)if(net[j])order.push_back(j);
        do {
            RoutePlan r;r.vehicle=0;r.nodes={0};int load=0,pickups=0;bool legal=true;double travel=0;int from=0;
            for(int station:order) {
                const int pickup=std::max(0,-net[station]),drop=std::max(0,net[station]);
                load+=pickup-drop;pickups+=pickup;
                if(load<0||load>in.Q[0])legal=false;
                travel+=std::hypot(in.points[from].first-in.points[station].first,in.points[from].second-in.points[station].second)/1.5;
                r.nodes.push_back(station);r.operations.push_back({station,pickup,drop});from=station;
            }
            travel+=std::hypot(in.points[from].first-in.points[0].first,in.points[from].second-in.points[0].second)/1.5;
            r.nodes.push_back(0);
            if(legal&&load>=0&&load<=in.Q[0]&&travel+(in.pickup_time+in.drop_time)*pickups<=in.total_time_limit)
                all.push_back({r});
        }while(std::next_permutation(order.begin(),order.end()));
    };enumerate_states(1);return all;
}
std::pair<double,double> independent_objective(const Instance& in,const std::vector<RoutePlan>& fleet) {
    std::vector<int> Y=in.initial;for(const auto& route:fleet)for(const auto& op:route.operations)Y[op.station]+=op.drop-op.pickup;
    std::vector<long double> r(in.V+1);long double S=0,H=0,P=0;
    for(int i=1;i<=in.V;++i){r[i]=static_cast<long double>(Y[i])/in.target[i];S+=r[i];P+=in.weights[i]*std::fabs(r[i]-1);}
    for(int i=1;i<=in.V;++i)for(int j=i+1;j<=in.V;++j)H+=std::fabs(r[i]-r[j]);
    const long double G=S>0?H/(in.V*S):0;return {double(G),double(G+.15L*P)};
}
std::array<Round119Certificate,2> proof_pair(double left,double right) {
    auto l=certificate(0,left),r=certificate(1,right);
    l.cutoff=r.cutoff=.65;return {l,r};
}
void type_start_lifecycle(const std::filesystem::path& path,const Native& data,
    const std::vector<double>& first,const std::vector<double>& second,const std::filesystem::path& dest) {
    HMODULE dll=LoadLibraryW(L"gurobi130.dll");require(dll!=nullptr,"DLL type/start lifecycle");
#define API(n) auto n=reinterpret_cast<decltype(&GRB##n)>(GetProcAddress(dll,"GRB" #n));require(n!=nullptr,"type/start API " #n)
    API(emptyenvinternal);API(setintparam);API(startenv);API(readmodel);API(getintattr);API(getcharattrarray);
    API(setcharattrarray);API(updatemodel);API(setintattr);API(setdblattrarray);API(getdblattrarray);API(freemodel);API(freeenv);
#undef API
    auto check=[](int rc){if(rc)throw std::runtime_error("type/start readback "+std::to_string(rc));};
    GRBenv* env=nullptr;GRBmodel* model=nullptr;
    try {
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"OutputFlag",0));check(startenv(env));check(readmodel(env,path.string().c_str(),&model));
        const int n=int(data.domain.names.size());const auto& original=data.domain.variable_types;
        std::vector<char> relaxed(n,'C'),readback(n);check(setcharattrarray(model,"VType",0,n,relaxed.data()));check(updatemodel(model));
        check(getcharattrarray(model,"VType",0,n,readback.data()));require(readback==relaxed,"LP types not continuous");
        check(setcharattrarray(model,"VType",0,n,const_cast<char*>(original.data())));check(updatemodel(model));
        check(getcharattrarray(model,"VType",0,n,readback.data()));require(readback==original,"all original types not restored");
        check(setintattr(model,"NumStart",1));check(setintparam(env,"StartNumber",0));check(updatemodel(model));
        std::vector<double> start(n);
        for(const auto* point:{&first,&second}) {
            check(setdblattrarray(model,"Start",0,n,const_cast<double*>(point->data())));check(updatemodel(model));
            check(getdblattrarray(model,"Start",0,n,start.data()));require(start==*point,"all-column Start readback");
        }
        require(first!=second,"same-SHA different-Start fixture not different");
        std::ofstream f(dest);f<<"{\"Optimize\":0,\"LP_to_MIP_all_types_restored\":true,\"same_SHA_two_distinct_Start_states\":true,\"all_column_readback_equal\":true}\n";
    }catch(...){if(model)freemodel(model);if(env)freeenv(env);FreeLibrary(dll);throw;}
    freemodel(model);freeenv(env);FreeLibrary(dll);
}
void logic(const std::filesystem::path& dir) {
    int cases=0;
    for(const auto& values:std::vector<std::pair<double,double>>{{.1,.4},{.4,.1},{.2,.2},{0,0}}) {
        const auto p=makeRound120Pair(proof_pair(values.first,values.second),"finite_fixture");
        for(bool conditional:{false,true})for(double constant:{0.,.25,-.25}) {
            const auto r=round120Rows(p,conditional,constant);require(round120Endpoints(r,p,conditional),"all beta orders/constant endpoints");
            require(p.a<=p.m&&p.m<=p.b,"midpoint overlap");++cases;
        }
    }
    auto c=proof_pair(1.,.4);c[0].cutoff=.2;
    auto p=makeRound120Pair(c,"cutoff_counterexample");require(p.beta0<=.2-1e-7,"cutoff complement omitted");++cases;
    require(round120Contains(p,0,.25)&&!round120Contains(p,-.1,.25)&&!round120Contains(p,0,.6),"parent/child direction");++cases;
    for(int kind=0;kind<5;++kind) {
        auto bad=proof_pair(.1,.2);
        if(kind==0)bad[1].status="UNKNOWN";
        if(kind==1)bad[1].model.clear();
        if(kind==2)bad[1].lower=.26;
        if(kind==3)bad[0].parent_upper=bad[1].parent_upper=0;
        if(kind==4)bad[1].bound=std::numeric_limits<double>::quiet_NaN();
        bool rejected=false;try{makeRound120Pair(bad,"bad");}catch(...){rejected=true;}
        require(rejected,"missing/degenerate/unreturned/nonfinite proof admitted");++cases;
    }
    std::ofstream f(dir/"finite_logic.json");f<<"{\"Optimize\":0,\"cases\":"<<cases<<",\"injected_values_not_native_evidence\":true}\n";
}
void embeddings(const std::filesystem::path& dir,const std::filesystem::path& fixture) {
    const auto in=parseInstanceFile(fixture.string(),1000,60,60);const auto fleets=independent_fleets(in);
    require(fleets.size()==3,"independent full physical enumeration changed");
    SolveOptions options;configurePaperK1AmSfOverrides(options);options.lambda=.15;options.round98_state_service="m-binary";
    CanonicalCompactModelSpec spec;spec.strengthened=true;spec.interval_restricted=true;spec.gamma_U=.5;
    spec.add_verified_incumbent_row=true;spec.verified_incumbent=.65;spec.station_state_formulation="vd-p";spec.round51_subset_duration_big_m="off";
    const auto base=writeCanonicalCompactModel(in,options,dir/"base.lp",spec);require(base.written,"base physical model");
    int embedded=0,models=0,midpoints=0;
    for(const auto& values:std::vector<std::pair<double,double>>{{.3,.65},{.29,.1},{.1,.1}}) {
        const auto p=makeRound120Pair(proof_pair(values.first,values.second),"analytic_complete_enumeration");
        for(bool conditional:{false,true}) {
            const auto path=dir/("extension_"+std::to_string(models++)+".lp");
            const auto artifact=extendRound120Artifact(base,p,conditional,path);const auto native=read_native(path);
            require(native.linear.rhs.size()==std::size_t(base.rows+3)&&native.domain.names.size()==std::size_t(base.columns+1),"one selector three rows census");
            require(std::count(native.domain.names.begin(),native.domain.names.end(),"r120_h")==1,"selector duplication");
            std::vector<std::vector<double>> starts;
            for(const auto& fleet:fleets) {
                const auto v=verifySolution(in,fleet,.15);
                const auto independent=independent_objective(in,fleet);
                require(v.feasible&&std::fabs(v.G-independent.first)<=1e-12&&std::fabs(v.objective-independent.second)<=1e-12,
                    "independent physical enumeration/objective disagrees with original evaluator");
                const auto start=mapVerifiedRoutesToCanonicalModel(in,options,fleet,"all_legal_physical",0,.5,.65,native.domain,&p);
                require(start.complete&&validateCandidateLinearResidual(native.linear,start.values,1e-7).valid,"complete native physical embedding");
                long double f=native.constant;for(std::size_t j=0;j<start.values.size();++j)f+=static_cast<long double>(native.objective[j])*start.values[j];
                require(std::fabs(double(f)-v.objective)<=1e-7,"original objective preserving physical embedding");
                starts.push_back(start.values);++embedded;
            }
            type_start_lifecycle(path,native,starts[0],starts[1],dir/("type_start_"+std::to_string(models)+".json"));
            bool rejected=false;try{extendRound120Artifact(artifact,p,conditional,dir/"duplicate.lp");}catch(...){rejected=true;}
            require(rejected,"duplicate extension admitted");
            // This is an auxiliary completion at model g=m, explicitly not a
            // physical G=m assertion. Increase deviations to satisfy either
            // side's scalar floor; the exact-G physical extensions above stay
            // objective preserving and are the projection qualification.
            const auto pickup=std::find_if(fleets.begin(),fleets.end(),[&](const auto& x){return verifySolution(in,x,.15).G==0;});
            auto middle=mapVerifiedRoutesToCanonicalModel(in,options,*pickup,"midpoint_auxiliary_completion",0,.5,.65,native.domain,&p).values;
            for(std::size_t j=0;j<middle.size();++j) {
                if(native.domain.names[j]=="G"||native.domain.names[j]=="state_g_1_0"||native.domain.names[j]=="state_g_2_0")middle[j]=p.m;
            }
            const auto hi=std::find(native.domain.names.begin(),native.domain.names.end(),"r120_h")-native.domain.names.begin();
            for(int h:{0,1}) {
                middle[hi]=h;
                for(std::size_t j=0;j<middle.size();++j)
                    require(middle[j]>=native.domain.lower_bounds[j]-1e-7&&middle[j]<=native.domain.upper_bounds[j]+1e-7,"midpoint full native bounds");
                const bool expected=!(conditional&&h==1&&p.beta1>.55+1e-7);
                require(validateCandidateLinearResidual(native.linear,middle,1e-7).valid==expected,
                    "full matrix midpoint/virtual-g auxiliary removal semantics");++midpoints;
            }
        }
    }
    // Actual native ObjCon fixture: an explicitly synthetic offset, separate
    // from original-BRP objective-preserving qualification (ObjCon=0).
    auto synthetic=base;synthetic.path=dir/"synthetic_constant.lp";
    std::ifstream source(base.path);std::ostringstream bytes;bytes<<source.rdbuf();auto text=bytes.str();
    text.insert(text.find("\nSubject To\n")," + 0.25");{std::ofstream f(synthetic.path);f<<text;}
    synthetic.sha256=fileSha256(synthetic.path);
    const auto pair=makeRound120Pair(proof_pair(.3,.65),"synthetic_offset_only");
    const auto constant=extendRound120Artifact(synthetic,pair,true,dir/"synthetic_constant_D1.lp");
    const auto data=read_native(constant.path);require(data.constant==.25,"actual objective constant lost");
    const auto emission=round120Rows(pair,true,.25);require(std::fabs(data.linear.rhs.back()-emission.objective_base)<1e-16,"full objective constant omitted from lower row");
    std::ofstream f(dir/"round120_physical_embedding.json");f<<"{\"Optimize\":0,\"physical_fleets\":3,\"complete_native_embeddings\":"<<embedded
        <<",\"D0_D1_models\":"<<models<<",\"actual_full_matrix_midpoint_auxiliary_checks\":"<<midpoints
        <<",\"midpoint_completion_not_physical_G_equality\":true,\"original_objective_constant\":0,\"synthetic_offset_checked\":0.25,\"passed\":true}\n";
}
void archive_lifecycle(const std::filesystem::path& dir,const std::filesystem::path& fixture) {
    const auto in=parseInstanceFile(fixture.string(),1000,60,60);SolveOptions opt;opt.lambda=.15;
    RoutePlan empty;empty.vehicle=0;empty.nodes={0,0};std::vector<RoutePlan> own{empty};
    const auto source=dir/"injected_proof_scope.txt";{std::ofstream f(source);f<<"analytic finite qualification only; not an LP certificate\n";}
    auto proofs=proof_pair(.3,.65);for(auto& c:proofs){c.path=source.string();c.model=fileSha256(source);}
    Round120NativeProof archive(in,opt,dir/"archive.jsonl",0,.5,own);archive.add(proofs[0]);archive.add(proofs[1]);
    require(archive.firstInteger("L0",0,.5,1)&&archive.firstInteger("L0",0,.5,1),"repeat original request lost sealed pair");
    Round120NativeProof late(in,opt,dir/"late.jsonl",0,.5,own);late.add(proofs[0]);
    require(!late.firstInteger("L0",0,.5,1),"missing pair installed");late.add(proofs[1]);require(!late.installed(),"late repair installed after integer request");
    Round120NativeProof split(in,opt,dir/"split.jsonl",0,.5,own);split.add(proofs[0]);split.add(proofs[1]);
    require(!split.firstInteger("L0.0",0,.25,1)&&!split.firstInteger("L0",0,.5,1),"AM split root forced exposure");
    Round120NativeProof deadline(in,opt,dir/"deadline.jsonl",0,.5,own);deadline.add(proofs[0]);deadline.add(proofs[1]);
    require(!deadline.firstInteger("L0",0,.5,0),"deadline installed");
    RoutePlan pickup;pickup.vehicle=0;pickup.nodes={0,1,0};pickup.operations.push_back({1,1,0});
    Round120NativeProof bad(in,opt,dir/"bad.jsonl",0,.5,own);proofs[0].bound=.4;bad.add(proofs[0]);bad.add(proofs[1]);
    require(bad.firstInteger("L0",0,.5,1),"bad-proof negative fixture not installed before contradiction");
    bool rejected=false;try{bad.observe({pickup},10);}catch(...){rejected=true;}
    require(rejected&&bad.failed(),"same-domain bad proof dependencies not revoked");
    require(verifySolution(in,{pickup},.15).feasible,"revocation lost legal physical witness");
    std::ofstream f(dir/"archive_lifecycle.json");f<<"{\"Optimize\":0,\"passed\":true,\"proofs_are_injected_negative_fixtures\":true,\"root_once_deadline_missing_late_split_and_revocation\":true}\n";
}
}
int main(int argc,char** argv){try{
    require(argc==4,"reference TSV, exclusive output, original micro fixture required");
    const std::filesystem::path dir(argv[2]);require(!std::filesystem::exists(dir),"qualification output exists");std::filesystem::create_directories(dir);
    logic(dir);embeddings(dir,argv[3]);archive_lifecycle(dir,argv[3]);
    // Reuse original four-profile complete matrix/Start checks, with frozen
    // reference files. No Optimize symbol is resolved by this executable.
    physical_embedding(dir,argv[3]);
    std::ifstream input(argv[1]);std::string line;int count=0;
    while(std::getline(input,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();if(line.empty())continue;
        std::istringstream row(line);std::vector<std::string> fields{"Round120Reference"};std::string field;
        while(std::getline(row,field,'\t'))fields.push_back(field);require(fields.size()==7,"reference row");
        std::vector<char*> args;for(auto& s:fields)args.push_back(s.data());
        require(round119_cold_reference_main(int(args.size()),args.data())==0,"cold full reference export");++count;
    }
    require(count==6,"exact six preregistered zero-Optimize reference exports");
    std::cout<<"Round120 finite logic, physical native embeddings/types/Starts and six references; Optimize=0\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
