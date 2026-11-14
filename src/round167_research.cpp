// Offline research only. The frozen B/C166 writer, backend and controller
// are unchanged. This C++ entry owns every new model mutation and Optimize.
#include "Round167ConditionalState.hpp"
#include "Round166Research.hpp"
#include "CanonicalCompactModel.hpp"
#include "MipStartMapping.hpp"
#include "PaperK1AmSf.hpp"
#include "Round127Research.hpp"
#include "Parser.hpp"
#include "Evaluator.hpp"
#include "FileSha256.hpp"
#include "gurobi_c.h"
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <numeric>
#include <set>
#include <sstream>
using namespace ebrp;
namespace {
void require(bool p,const std::string& why){if(!p)throw std::runtime_error(why);}
void ck(int e){if(e)throw std::runtime_error("Gurobi API error "+std::to_string(e));}
using Terms=std::map<int,double>;
using Clock=std::chrono::steady_clock;
double seconds(Clock::time_point t){return std::chrono::duration<double>(Clock::now()-t).count();}
struct Model {
    GRBenv* env=nullptr;GRBmodel* model=nullptr;
    int n=0;std::map<std::string,int> index;
    Model(){ck(GRBemptyenv(&env));ck(GRBsetintparam(env,"OutputFlag",0));ck(GRBstartenv(env));
        ck(GRBnewmodel(env,&model,"D167_offline",0,nullptr,nullptr,nullptr,nullptr,nullptr));}
    ~Model(){if(model)GRBfreemodel(model);if(env)GRBfreeenv(env);}
    void load(const std::filesystem::path& p){GRBfreemodel(model);model=nullptr;ck(GRBreadmodel(env,p.string().c_str(),&model));refresh();}
    void refresh(){ck(GRBupdatemodel(model));ck(GRBgetintattr(model,"NumVars",&n));index.clear();
        for(int j=0;j<n;++j){char* name=nullptr;ck(GRBgetstrattrelement(model,"VarName",j,&name));index[name]=j;}}
    int col(const std::string& name)const {auto f=index.find(name);require(f!=index.end(),"missing column "+name);return f->second;}
    int var(const std::string& name,double lo,double hi,char type='C',double obj=0) {
        require(!index.count(name),"duplicate column "+name);
        ck(GRBaddvar(model,0,nullptr,nullptr,obj,lo,hi,type,name.c_str()));index[name]=n;return n++;
    }
    void row(const Terms& terms,char sense,double rhs,const std::string& name) {
        std::vector<int> ix;std::vector<double>a;
        for(auto t:terms)if(t.second!=0){ix.push_back(t.first);a.push_back(t.second);}
        ck(GRBaddconstr(model,static_cast<int>(ix.size()),ix.data(),a.data(),sense,rhs,name.c_str()));
    }
    double attr(const char* name,int j){double v=0;ck(GRBgetdblattrelement(model,name,j,&v));return v;}
    SolverNeutralModelDomain domain(){refresh();SolverNeutralModelDomain d;d.names.resize(n);d.lower_bounds.resize(n);d.upper_bounds.resize(n);d.variable_types.resize(n);
        for(auto it:index)d.names[it.second]=it.first;
        ck(GRBgetdblattrarray(model,"LB",0,n,d.lower_bounds.data()));ck(GRBgetdblattrarray(model,"UB",0,n,d.upper_bounds.data()));
        ck(GRBgetcharattrarray(model,"VType",0,n,d.variable_types.data()));return d;}
};
std::string bit(int i,int h){return "bit_"+std::to_string(i)+"_"+std::to_string(h);}
std::string prod(int i,int h){return "prod_"+std::to_string(i)+"_"+std::to_string(h);}
std::string state(int i,int y){return "state_"+std::to_string(i)+"_"+std::to_string(y);}
std::string stateG(int i,int y){return "state_g_"+std::to_string(i)+"_"+std::to_string(y);}
std::string indexed(const std::string& prefix,int i){return prefix+std::to_string(i);}
bool auxiliary(const std::string& name){for(const auto& p:{"state_","r166_","bit_","prod_","d167_"})if(name.rfind(p,0)==0)return true;return false;}
std::string common(Model& m,const std::filesystem::path& target) {
    auto dom=m.domain();std::vector<std::string> lines;
    for(int j=0;j<m.n;++j)if(!auxiliary(dom.names[j])) {
        std::ostringstream f;f<<std::setprecision(17)<<"COL "<<dom.names[j]<<' '<<dom.lower_bounds[j]<<' '<<dom.upper_bounds[j]<<' '<<dom.variable_types[j]<<' '<<m.attr("Obj",j);lines.push_back(f.str());
    }
    int rows=0;ck(GRBgetintattr(m.model,"NumConstrs",&rows));
    for(int r=0;r<rows;++r) {
        char* rowName=nullptr;ck(GRBgetstrattrelement(m.model,"ConstrName",r,&rowName));
        if(std::string(rowName).rfind("d167_",0)==0)continue;
        int nz=0,beg=0;ck(GRBgetconstrs(m.model,&nz,nullptr,nullptr,nullptr,r,1));
        std::vector<int> ix(nz);std::vector<double>a(nz);ck(GRBgetconstrs(m.model,&nz,&beg,ix.data(),a.data(),r,1));
        bool external=true;std::map<std::string,double> terms;
        for(int t=0;t<nz;++t){if(auxiliary(dom.names[ix[t]]))external=false;terms[dom.names[ix[t]]]=a[t];}
        if(!external)continue;
        char sense;ck(GRBgetcharattrelement(m.model,"Sense",r,&sense));
        std::ostringstream f;f<<std::setprecision(17)<<"ROW "<<sense<<' '<<m.attr("RHS",r);
        for(auto t:terms)f<<' '<<t.first<<':'<<t.second;lines.push_back(f.str());
    }
    std::sort(lines.begin(),lines.end());std::ofstream f(target);for(auto& line:lines)f<<line<<'\n';f.close();return fileSha256(target);
}
void absoluteColumns(Model& m,int i,int C,double hi) {
    for(int h=0;h<round167Bits(C);++h){m.var(bit(i,h),0,1,'B');m.var(prod(i,h),0,hi);}
}
void addReferenceCodes(Model& m,int i,int l,int u,int C,double hi) {
    absoluteColumns(m,i,C,hi);
    for(int y=l;y<=u;++y)ck(GRBsetcharattrelement(m.model,"VType",m.col(state(i,y)),'C'));
    for(int h=0;h<round167Bits(C);++h) {
        Terms delta{{m.col(bit(i,h)),1}},w{{m.col(prod(i,h)),1}};
        for(int y=l;y<=u;++y)if((y>>h)&1){delta[m.col(state(i,y))]=-1;w[m.col(stateG(i,y))]=-1;}
        m.row(delta,'=',0,"rabs_delta_"+std::to_string(i)+"_"+std::to_string(h));
        m.row(w,'=',0,"rabs_w_"+std::to_string(i)+"_"+std::to_string(h));
    }
}
struct Interface {int Y,Z,G;Terms M,V;};
void addDAG(Model& m,int i,const Round167DAG& dag,double lo,double hi,const Interface& at) {
    absoluteColumns(m,i,dag.capacity,hi);
    std::vector<int> f,q;
    std::vector<Terms> af(dag.nodes),aq(dag.nodes);
    Terms yy{{at.Y,-1}},zz{{at.Z,-1}},mm=at.M,vv=at.V;
    std::vector<Terms> dd(dag.bits),ww(dag.bits);
    for(int h=0;h<dag.bits;++h){dd[h][m.col(bit(i,h))]=-1;ww[h][m.col(prod(i,h))]=-1;}
    for(int e=0;e<static_cast<int>(dag.arcs.size());++e) {
        const auto& arc=dag.arcs[e];int fj=m.var(round167F(i,e),0,1),qj=m.var(round167Q(i,e),0,hi);
        f.push_back(fj);q.push_back(qj);af[arc.tail][fj]=1;af[arc.head][fj]=-1;aq[arc.tail][qj]=1;aq[arc.head][qj]=-1;
        m.row({{qj,1},{fj,-lo}},'>',0,"d167_lo_"+std::to_string(i)+"_"+std::to_string(e));
        m.row({{qj,1},{fj,-hi}},'<',0,"d167_hi_"+std::to_string(i)+"_"+std::to_string(e));
        yy[fj]+=arc.Y;zz[qj]+=arc.Y;mm[fj]-=arc.M;vv[fj]-=arc.V;
        if(arc.bit>=0&&arc.value==1){dd[arc.bit][fj]+=1;ww[arc.bit][qj]+=1;}
    }
    // Only the sink balance is omitted: summing all node balances is zero
    // separately for f and q, hence both omitted equations are implied.
    aq[0][at.G]-=1;
    for(int node=0;node<dag.nodes;++node)if(node!=1) {
        const auto label=std::to_string(i)+"_"+std::to_string(node);
        m.row(af[node],'=',node==0?1:0,"d167_mass_"+label);
        m.row(aq[node],'=',0,"d167_weight_"+label);
    }
    for(auto row:std::vector<std::pair<std::string,Terms>>{{"Y",yy},{"M",mm},{"V",vv},{"Z",zz}})
        m.row(row.second,'=',0,"d167_link_"+row.first+"_"+std::to_string(i));
    for(int h=0;h<dag.bits;++h){m.row(dd[h],'=',0,"d167_delta_"+std::to_string(i)+"_"+std::to_string(h));m.row(ww[h],'=',0,"d167_w_"+std::to_string(i)+"_"+std::to_string(h));}
}
void deleteStates(Model& m) {
    auto dom=m.domain();std::vector<int> cols,rows;std::set<int> indices;
    for(int j=0;j<m.n;++j)if(dom.names[j].rfind("state_",0)==0){cols.push_back(j);indices.insert(j);}
    int nr=0;ck(GRBgetintattr(m.model,"NumConstrs",&nr));
    for(int r=0;r<nr;++r){int nz=0,beg=0;ck(GRBgetconstrs(m.model,&nz,nullptr,nullptr,nullptr,r,1));
        std::vector<int> ix(nz);std::vector<double>a(nz);ck(GRBgetconstrs(m.model,&nz,&beg,ix.data(),a.data(),r,1));
        if(std::any_of(ix.begin(),ix.end(),[&](int j){return indices.count(j);}))rows.push_back(r);
    }
    ck(GRBdelconstrs(m.model,static_cast<int>(rows.size()),rows.data()));ck(GRBdelvars(m.model,static_cast<int>(cols.size()),cols.data()));m.refresh();
}
std::vector<RoutePlan> parent(const std::string& path) {
    std::ifstream f(path);int count=0;f>>count;std::vector<RoutePlan> routes;
    for(int k=0;k<count;++k){RoutePlan r;int n=0;f>>r.vehicle>>n;require(n>=2,"parent route length");r.nodes.resize(n);for(int& a:r.nodes)f>>a;
        for(int j=1;j+1<n;++j){int d=0;f>>d;r.operations.push_back({r.nodes[j],std::max(0,d),std::max(0,-d)});}routes.push_back(r);}
    require(bool(f),"parent input");return routes;
}
std::vector<std::map<int,int>> masks(const Round167DAG& dag) {
    std::vector<std::map<int,int>> result(3);
    for(int level=1;level<=2;++level){result[level]=result[level-1];
        for(int h=0;h<dag.bits;++h)if(!result[level].count(h)) {
            auto zero=result[level],one=zero;zero[h]=0;one[h]=1;
            if(!dag.count(zero)||!dag.count(one))continue;
            bool initial=dag.lower<=dag.initial&&dag.initial<=dag.upper;
            for(auto fixed:result[level])initial=initial&&((dag.initial>>fixed.first)&1)==fixed.second;
            result[level][h]=initial?1-((dag.initial>>h)&1):0;break;
        }
    }
    return result;
}
void writeMasks(std::ostream& f,const std::map<int,int>& mask){f<<'[';bool first=true;for(auto t:mask){if(!first)f<<',';first=false;f<<'['<<t.first<<','<<t.second<<']';}f<<']';}
void auditStart(Model& m,const std::vector<double>& x,double expected,const std::filesystem::path& dir) {
    const auto dom=m.domain();require(x.size()==static_cast<size_t>(m.n),"Start size");
    double residual=0,objective=0;int nr=0;ck(GRBgetintattr(m.model,"NumConstrs",&nr));
    for(int j=0;j<m.n;++j){residual=std::max({residual,dom.lower_bounds[j]-x[j],x[j]-dom.upper_bounds[j]});
        if(dom.variable_types[j]!='C')residual=std::max(residual,std::abs(x[j]-std::round(x[j])));objective+=x[j]*m.attr("Obj",j);}
    for(int r=0;r<nr;++r){int nz=0,beg=0;ck(GRBgetconstrs(m.model,&nz,nullptr,nullptr,nullptr,r,1));
        std::vector<int>ix(nz);std::vector<double>a(nz);ck(GRBgetconstrs(m.model,&nz,&beg,ix.data(),a.data(),r,1));
        char sense;ck(GRBgetcharattrelement(m.model,"Sense",r,&sense));double lhs=0,rhs=m.attr("RHS",r);
        for(int t=0;t<nz;++t)lhs+=a[t]*x[ix[t]];residual=std::max(residual,sense=='='?std::abs(lhs-rhs):sense=='<'?lhs-rhs:rhs-lhs);
    }
    std::ofstream f(dir/"start_check.json");f<<std::setprecision(17)<<"{\"complete\":true,\"columns\":"<<m.n<<",\"rows\":"<<nr<<",\"max_residual\":"<<residual<<",\"mapped_objective\":"<<objective<<",\"physical_objective\":"<<expected<<"}\n";f.close();
    require(residual<=1e-7&&std::abs(expected-objective)<=1e-7,"Start actual rows/bounds/types/objective");
    std::ofstream v(dir/"start.csv");v<<"name,value\n"<<std::setprecision(17);for(int j=0;j<m.n;++j)v<<dom.names[j]<<','<<x[j]<<'\n';
    ck(GRBsetdblattrarray(m.model,"Start",0,m.n,const_cast<double*>(x.data())));ck(GRBwrite(m.model,(dir/"start.mst").string().c_str()));
}
void prepare(int argc,char** argv) {
    // prepare input T lambda parent out B|C166|R_abs|D167 lo hi cutoff F_level S0
    require(argc==13,"prepare input T lambda parent out rep lo hi cutoff level S0");const auto begin=Clock::now();
    const auto in=parseInstanceFile(argv[2],std::stod(argv[3]),60,60);auto routes=parent(argv[5]);
    const std::filesystem::path dir(argv[6]);require(std::filesystem::create_directories(dir),"exclusive output directory");
    const std::string rep=argv[7];require(rep=="B"||rep=="C166"||rep=="R_abs"||rep=="D167","unsupported representation");
    const double lo=std::stod(argv[8]),hi=std::stod(argv[9]),cutoff=std::stod(argv[10]);const int level=std::stoi(argv[11]);
    require(lo>=0&&hi<=1&&lo<=hi&&level>=0&&level<=2,"invalid scope");
    SolveOptions opt;configurePaperK1AmSfOverrides(opt);opt.lambda=std::stod(argv[4]);opt.round98_state_service="m-binary";
    opt.algorithm_preset="research-round83-vds-equal-net-exchange";opt.method="gcap-frontier";
    round127().mode="ms2";round137Apply(opt,"ms2");
    // This isolated entry accepts no extension flags. Hence AP/count/RN/CDF/
    // theta/linked-direction/VD-J cannot be silently requested or deleted.
    const auto pv=verifySolution(in,routes,opt.lambda);require(pv.feasible,"physical parent");
    CanonicalCompactModelSpec spec;spec.strengthened=spec.interval_restricted=spec.add_verified_incumbent_row=true;
    spec.gamma_L=lo;spec.gamma_U=hi;spec.verified_incumbent=cutoff;spec.incumbent_epsilon=0;
    spec.station_state_formulation=rep=="C166"?"breakpoint-bit":"vd-p";spec.round51_subset_duration_big_m="off";
    auto art=writeCanonicalCompactModel(in,opt,dir/"base.lp",spec);require(art.written,art.failure_reason);
    Model m;m.load(dir/"base.lp");auto original=m.domain();
    auto mapped=mapVerifiedRoutesToCanonicalModel(in,opt,routes,"Round167_offline",lo,hi,cutoff,original);
    std::map<std::string,double> starts;if(mapped.complete)for(int j=0;j<m.n;++j)starts[original.names[j]]=mapped.values[j];
    std::vector<Round167DAG> graphs;int selected=1;std::int64_t maximum=-1;
    for(int i=1;i<=in.V;++i){const int l=std::lround(m.attr("LB",m.col(indexed("Y_",i)))),u=std::lround(m.attr("UB",m.col(indexed("Y_",i))));
        graphs.emplace_back(l,u,in.initial[i],in.capacity[i]);if(graphs.back().count()>maximum){maximum=graphs.back().count();selected=i;}}
    const auto conditions=masks(graphs[selected-1]);const auto& mask=conditions[level];
    std::string commonBefore=common(m,dir/"common_before.txt");
    if(rep=="D167")deleteStates(m);
    for(int i=1;i<=in.V;++i) {
        const auto& dag=graphs[i-1];
        if(rep=="R_abs")addReferenceCodes(m,i,dag.lower,dag.upper,dag.capacity,hi);
        if(rep=="D167") {
            Interface at{m.col(indexed("Y_",i)),m.col(indexed("zprod_",i)),m.col("G"),{}, {}};
            for(int k=0;k<in.M;++k){at.M[m.col("p_"+std::to_string(k)+"_"+std::to_string(i))]=1;at.M[m.col("d_"+std::to_string(k)+"_"+std::to_string(i))]=1;at.V[m.col("z_"+std::to_string(k)+"_"+std::to_string(i))]=1;}
            addDAG(m,i,dag,lo,hi,at);
        }
    }
    m.refresh();const auto commonAfter=common(m,dir/"common_after.txt");
    require(commonBefore==commonAfter,"physical rows/bounds/types/objective changed");
    if(rep!="B")for(auto fixed:mask){const int j=m.col(bit(selected,fixed.first));m.row({{j,1}},'=',fixed.second,"fixed_absolute_"+std::to_string(fixed.first));}
    if(std::stoi(argv[12]))for(int i=1;i<=in.V;++i){int j=m.col(indexed("Y_",i));ck(GRBsetdblattrelement(m.model,"LB",j,0));ck(GRBsetdblattrelement(m.model,"UB",j,0));}
    bool startCompatible=mapped.complete;
    if(startCompatible){for(auto fixed:mask)startCompatible=startCompatible&&((pv.final_inventory[selected]>>fixed.first)&1)==fixed.second;
        if(std::stoi(argv[12]))for(int i=1;i<=in.V;++i)startCompatible=startCompatible&&pv.final_inventory[i]==0;}
    if(startCompatible) {
        if(rep=="R_abs"||rep=="D167")for(int i=1;i<=in.V;++i) {
            const int y=pv.final_inventory[i];const auto& dag=graphs[i-1];
            for(int h=0;h<dag.bits;++h){starts[bit(i,h)]=(y>>h)&1;starts[prod(i,h)]=pv.G*((y>>h)&1);}
            if(rep=="D167")for(int e:dag.path(y)){starts[round167F(i,e)]=1;starts[round167Q(i,e)]=pv.G;}
        }
        const auto final=m.domain();std::vector<double>x(m.n);
        for(int j=0;j<m.n;++j){auto it=starts.find(final.names[j]);require(it!=starts.end()||final.names[j].rfind("d167_",0)==0,"unmapped column "+final.names[j]);x[j]=it==starts.end()?0:it->second;}
        auditStart(m,x,pv.objective,dir);
    }
    m.refresh();ck(GRBwrite(m.model,(dir/"model.lp").string().c_str()));
    int rows=0,nz=0,binaries=0,integers=0;ck(GRBgetintattr(m.model,"NumConstrs",&rows));ck(GRBgetintattr(m.model,"NumNZs",&nz));ck(GRBgetintattr(m.model,"NumBinVars",&binaries));ck(GRBgetintattr(m.model,"NumIntVars",&integers));
    std::ofstream f(dir/"prepare.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"representation\":"<<std::quoted(rep)<<",\"model_SHA256\":"<<std::quoted(fileSha256(dir/"model.lp"))<<",\"base_SHA256\":"<<std::quoted(art.sha256)<<",\"common_SHA256\":"<<std::quoted(commonAfter)<<",\"selected_station\":"<<selected<<",\"level\":"<<level<<",\"mask\":";writeMasks(f,mask);
    f<<",\"conditional_stocks\":"<<graphs[selected-1].count(mask)<<",\"degenerate\":"<<(level>0&&conditions[level]==conditions[level-1])<<",\"all_masks\":[";
    for(int k=0;k<3;++k){if(k)f<<',';writeMasks(f,conditions[k]);}f<<"],\"start_complete\":"<<startCompatible<<",\"start_outside_scope\":"<<!startCompatible<<",\"rows\":"<<rows<<",\"columns\":"<<m.n<<",\"nonzeros\":"<<nz<<",\"binaries\":"<<binaries<<",\"integers_including_binary\":"<<integers<<",\"build_seconds\":"<<seconds(begin)<<",\"stations\":[";
    for(int i=1;i<=in.V;++i){if(i>1)f<<',';const auto& d=graphs[i-1];f<<"{\"i\":"<<i<<",\"l\":"<<d.lower<<",\"u\":"<<d.upper<<",\"b\":"<<d.initial<<",\"C\":"<<d.capacity<<",\"d\":"<<d.bits<<",\"nodes\":"<<d.nodes<<",\"edges\":"<<d.arcs.size()<<",\"parts\":"<<d.parts.size()<<'}';}
    f<<"]}\n";
}
void solve(int argc,char** argv) {
    require(argc==5,"solve directory LP|MIP timelimit");const auto begin=Clock::now();const std::filesystem::path dir(argv[2]);const bool lp=std::string(argv[3])=="LP";
    require(lp||std::string(argv[3])=="MIP","solve type");require(!std::filesystem::exists(dir/"Optimize.jsonl"),"no duplicate solve");
    Model m;m.load(dir/"model.lp");auto original=m.domain();GRBenv* env=GRBgetenv(m.model);
    ck(GRBsetintparam(env,"OutputFlag",1));ck(GRBsetintparam(env,"LogToConsole",0));ck(GRBsetstrparam(env,"LogFile",(dir/"native.log").string().c_str()));
    ck(GRBsetintparam(env,"Threads",1));ck(GRBsetintparam(env,"Seed",0));ck(GRBsetdblparam(env,"MIPGap",0));ck(GRBsetdblparam(env,"MIPGapAbs",0));ck(GRBsetdblparam(env,"NodeLimit",GRB_INFINITY));
    ck(GRBsetdblparam(env,"TimeLimit",std::stod(argv[4])));
    {std::ofstream p(dir/"parameters.json");p<<std::setprecision(17)<<'{';bool first=true;
        for(const char* name:{"Threads","Seed","Method","Presolve","MIPFocus","Cuts"}){int v=0;ck(GRBgetintparam(env,name,&v));if(!first)p<<',';first=false;p<<std::quoted(name)<<':'<<v;}
        for(const char* name:{"MIPGap","MIPGapAbs","NodeLimit","TimeLimit","FeasibilityTol","OptimalityTol","IntFeasTol"}){double v=0;ck(GRBgetdblparam(env,name,&v));p<<','<<std::quoted(name)<<':'<<v;}p<<"}\n";}
    std::vector<char> continuous(m.n,'C');ck(GRBsetcharattrarray(m.model,"VType",0,m.n,continuous.data()));ck(GRBupdatemodel(m.model));
    int nint=0;ck(GRBgetintattr(m.model,"NumIntVars",&nint));require(nint==0,"LP relaxation retains integer types");
    if(!lp){ck(GRBsetcharattrarray(m.model,"VType",0,m.n,original.variable_types.data()));ck(GRBupdatemodel(m.model));if(std::filesystem::exists(dir/"start.mst"))ck(GRBread(m.model,(dir/"start.mst").string().c_str()));}
    bool restored=true;if(!lp){auto now=m.domain();restored=now.variable_types==original.variable_types;require(restored,"LP to MIP restoration");}
    std::ofstream ledger(dir/"Optimize.jsonl");ledger<<"{\"phase\":\"begin\",\"call\":1,\"kind\":"<<std::quoted(lp?"raw_LP":"tiny_MIP")<<"}\n";ledger.flush();
    int api=GRBoptimize(m.model);ledger<<"{\"phase\":\"end\",\"call\":1,\"return\":"<<api<<"}\n";ledger.flush();ck(api);
    int status=0,count=0;double runtime=0,work=0,objective=0,bound=0,cv=0,bv=0,dv=0,iv=0;
    ck(GRBgetintattr(m.model,"Status",&status));ck(GRBgetintattr(m.model,"SolCount",&count));ck(GRBgetdblattr(m.model,"Runtime",&runtime));ck(GRBgetdblattr(m.model,"Work",&work));
    bool qualified=false;
    if(count){ck(GRBgetdblattr(m.model,"ObjVal",&objective));ck(GRBgetdblattr(m.model,"ConstrVio",&cv));ck(GRBgetdblattr(m.model,"BoundVio",&bv));
        if(lp)ck(GRBgetdblattr(m.model,"DualVio",&dv));else ck(GRBgetdblattr(m.model,"IntVio",&iv));
        if(lp)bound=objective;else ck(GRBgetdblattr(m.model,"ObjBound",&bound));
        qualified=status==GRB_OPTIMAL&&std::max({cv,bv,dv,iv})<=1e-7&&std::abs(bound-objective)<=1e-7;
        ck(GRBwrite(m.model,(dir/"solution.sol").string().c_str()));
        if(lp){int nr=0;ck(GRBgetintattr(m.model,"NumConstrs",&nr));std::vector<double> pi(nr),rc(m.n),x(m.n);
            ck(GRBgetdblattrarray(m.model,"Pi",0,nr,pi.data()));ck(GRBgetdblattrarray(m.model,"RC",0,m.n,rc.data()));ck(GRBgetdblattrarray(m.model,"X",0,m.n,x.data()));
            std::ofstream rows(dir/"dual_rows.csv"),cols(dir/"primal_reduced_cost.csv");rows<<"row,Pi,RHS\n"<<std::setprecision(17);cols<<"name,X,RC,LB,UB,Obj\n"<<std::setprecision(17);
            for(int r=0;r<nr;++r)rows<<r<<','<<pi[r]<<','<<m.attr("RHS",r)<<'\n';
            for(int j=0;j<m.n;++j)cols<<original.names[j]<<','<<x[j]<<','<<rc[j]<<','<<original.lower_bounds[j]<<','<<original.upper_bounds[j]<<','<<m.attr("Obj",j)<<'\n';
        }
    }
    if(lp){ck(GRBsetcharattrarray(m.model,"VType",0,m.n,original.variable_types.data()));ck(GRBupdatemodel(m.model));restored=m.domain().variable_types==original.variable_types;require(restored,"restore after LP");}
    std::ofstream f(dir/"solve.json");f<<std::setprecision(17)<<std::boolalpha<<"{\"native_status\":"<<status<<",\"Optimize\":1,\"raw_LP\":"<<lp<<",\"solutions\":"<<count<<",\"qualified_optimum\":"<<qualified<<",\"infeasible\":"<<(status==GRB_INFEASIBLE)<<",\"objective\":";
    if(count)f<<objective;else f<<"null";f<<",\"lower\":";if(count)f<<bound;else f<<"null";
    f<<",\"ConstrVio\":"<<cv<<",\"BoundVio\":"<<bv<<",\"DualVio\":"<<dv<<",\"IntVio\":"<<iv<<",\"runtime\":"<<runtime<<",\"work\":"<<work<<",\"outer_seconds\":"<<seconds(begin)<<",\"original_types_restored\":"<<restored<<",\"fingerprint\":"<<std::quoted(fileSha256(dir/"model.lp"))<<"}\n";
}
void localPrepare(int argc,char** argv) {
    require(argc==5,"local-prepare L1|L2|L3|L4 R_abs|C166|D167 out");const auto begin=Clock::now();std::string id=argv[2],rep=argv[3];const std::filesystem::path dir(argv[4]);require(std::filesystem::create_directories(dir),"exclusive local directory");
    require(id=="L1"||id=="L2"||id=="L3"||id=="L4","local id");require(rep=="R_abs"||rep=="C166"||rep=="D167","local rep");
    const int C=id=="L3"?8:4,b=id=="L3"?4:2;const double lo=id=="L3"?.125:id=="L4"?.25:0,hi=id=="L4"?.25:.5;
    Model m;int y=m.var("Y",0,C),move=m.var("M",0,C,'C',id=="L2"?0:1),visit=m.var("V",0,1,'C',id=="L2"?1:0),g=m.var("G",lo,hi),z=m.var("Z",0,C*hi);Round167DAG dag(0,C,b,C);
    if(rep=="D167")addDAG(m,1,dag,lo,hi,{y,z,g,{{move,1}},{{visit,1}}});
    else {
        Terms mass,yl{{y,-1}},ml{{move,-1}},vl{{visit,-1}},gl{{g,-1}},zl{{z,-1}};
        std::vector<int> supports;if(rep=="C166")supports=round166Support(0,C,b);else for(int a=0;a<=C;++a)supports.push_back(a);
        for(int a:supports){int s=m.var(state(1,a),0,1),q=m.var(stateG(1,a),0,hi);mass[s]=1;yl[s]=a;ml[s]=std::abs(b-a);vl[s]=a!=b;gl[q]=1;zl[q]=a;
            m.row({{q,1},{s,-lo}},'>',0,"persp_lo_"+std::to_string(a));m.row({{q,1},{s,-hi}},'<',0,"persp_hi_"+std::to_string(a));}
        int n=0;for(const auto& row:{mass,yl,ml,vl,gl,zl})m.row(row,'=',n++==0?1:0,"joint_"+std::to_string(n));
        if(rep=="R_abs")addReferenceCodes(m,1,0,C,C,hi);
        else {
            absoluteColumns(m,1,C,hi);Terms yl2{{y,1}},zl2{{z,1}};
            for(int h=0;h<dag.bits;++h){int d=m.col(bit(1,h)),w=m.col(prod(1,h));yl2[d]=-(std::int64_t(1)<<h);zl2[w]=-(std::int64_t(1)<<h);
                std::vector<std::pair<Terms,std::pair<char,double>>> rows{{{{w,1},{g,-1}},{'<',0}},{{{w,1},{d,-1}},{'<',0}},{{{w,1},{g,-1},{d,-1}},{'>',-1}},{{{w,1},{d,-lo}},{'>',0}},{{{w,1},{d,-hi}},{'<',0}},{{{w,1},{g,-1},{d,-hi}},{'>',-hi}},{{{w,1},{g,-1},{d,-lo}},{'<',-lo}}};
                int r=0;for(auto row:rows)m.row(row.first,row.second.first,row.second.second,"bit_envelope_"+std::to_string(h)+"_"+std::to_string(r++));
            }m.row(yl2,'=',0,"Y_bits");m.row(zl2,'=',0,"Z_bits");
        }
    }
    m.row({{m.col(bit(1,0)),1}},'=',1,"fix_bit0");if(id=="L3")m.row({{m.col(bit(1,1)),1}},'=',0,"fix_bit1");if(id=="L2")m.row({{g,1}},'=',.25,"fix_G");
    m.refresh();ck(GRBwrite(m.model,(dir/"model.lp").string().c_str()));
    std::ofstream f(dir/"prepare.json");f<<std::setprecision(17)<<"{\"id\":"<<std::quoted(id)<<",\"representation\":"<<std::quoted(rep)<<",\"build_seconds\":"<<seconds(begin)<<",\"model_SHA256\":"<<std::quoted(fileSha256(dir/"model.lp"))<<"}\n";
}
void algebra(const std::filesystem::path& out) {
    const auto begin=Clock::now();std::int64_t domains=0,paths=0,conditions=0,maps=0;
    for(auto cfg:std::vector<std::array<int,4>>{{0,0,0,0},{2,2,2,4},{1,7,0,8},{0,3,6,8},{0,6,0,8},{0,6,6,8},{0,8,4,8},{0,4,2,4},{3,2,1,4}}) {
        Round167DAG d(cfg[0],cfg[1],cfg[2],cfg[3]);++domains;auto all=d.inventories();
        require(d.count()==cfg[1]-cfg[0]+1,"path count");require(all.size()==static_cast<size_t>(d.count()),"path enumeration size");
        for(int y=cfg[0];y<=cfg[1];++y) {
            require(all[y-cfg[0]]==y,"legal path bijection");auto path=d.path(y);++paths;
            std::int64_t yy=0,mm=0,vv=0;std::vector<int> balance(d.nodes),levels(d.bits);
            for(int e:path){const auto a=d.arcs[e];yy+=a.Y;mm+=a.M;vv+=a.V;balance[a.tail]++;balance[a.head]--;if(a.bit>=0)levels[a.bit]++;}
            require(yy==y&&mm==std::abs(cfg[2]-y)&&vv==(cfg[2]!=y),"path service costs");
            require(balance[0]==1&&balance[1]==-1,"source/sink");for(int n=2;n<d.nodes;++n)require(balance[n]==0,"node conservation");for(int v:levels)require(v==1,"complete bit levels");
            for(auto interval:std::vector<std::pair<double,double>>{{0,0},{.25,.25},{.125,.5},{.25,.250000000001}}) {
                const double g=(interval.first+interval.second)/2;
                // Exact path mapping never divides by interval width.
                double z=0;for(int e:path)z+=d.arcs[e].Y*g;require(std::abs(z-g*y)<1e-12,"weighted path map");++maps;
            }
        }
        int ternary=1;for(int h=0;h<d.bits;++h)ternary*=3;
        for(int code=0;code<ternary;++code){std::map<int,int> mask;int a=code;for(int h=0;h<d.bits;++h){int t=a%3;a/=3;if(t)mask[h]=t-1;}
            std::vector<int> expected;for(int y=cfg[0];y<=cfg[1];++y){bool ok=true;for(auto t:mask)ok=ok&&((y>>t.first)&1)==t.second;if(ok)expected.push_back(y);}
            require(d.inventories(mask)==expected&&d.count(mask)==static_cast<std::int64_t>(expected.size()),"partial mask/empty condition");++conditions;
        }
        require(d.nodes<=2+static_cast<int>(d.parts.size())*(1+4*d.bits),"node bound");
        require(d.arcs.size()<=d.parts.size()*static_cast<size_t>(8*d.bits+5),"edge bound");
    }
    for(int C:{1,2,4,8,16,1024,1073741824,2147483647}) {Round167DAG d(0,C,C/2,C);require(d.count()==std::int64_t(C)+1,"large capacity, no enumeration");}
    {Round167DAG d(2147483647,2147483647,2147483647,2147483647);require(d.count()==1&&d.path(2147483647).size()==33,"maximum singleton without overflow");}
    std::filesystem::create_directories(out.parent_path());std::ofstream f(out);f<<"{\"PASS\":true,\"Optimize\":0,\"domains\":"<<domains<<",\"paths\":"<<paths<<",\"partial_conditions\":"<<conditions<<",\"path_g_maps\":"<<maps<<",\"large_capacity_no_enumeration\":true,\"seconds\":"<<seconds(begin)<<"}\n";
}
void tinyOracle(const std::filesystem::path& out) {
    std::ofstream f(out);f<<"Y1,Y2,G,P,F,return_load,handling\n"<<std::setprecision(17);double best=1e100;
    for(int y1=0;y1<=4;++y1)for(int y2=0;y2<=4;++y2){std::vector<int> stops;if(y1!=3)stops.push_back(1);if(y2!=0)stops.push_back(2);
        bool feasible=false;int R=0,time=0;do {int load=0,t=0;bool ok=true;for(int i:stops){int delta=i==1?3-y1:-y2;load+=delta;t+=60*std::abs(delta);if(load<0||load>3)ok=false;}t+=60*load;if(ok&&t<=360){feasible=true;R=load;time=t;}}while(std::next_permutation(stops.begin(),stops.end()));
        if(!feasible)continue;double G=y1+y2?std::abs(y1-y2)/(2.*(y1+y2)):0,P=std::abs(y1/2.-1)+std::abs(y2/2.-1),F=G+.15*P;best=std::min(best,F);f<<y1<<','<<y2<<','<<G<<','<<P<<','<<F<<','<<R<<','<<time<<'\n';}
    require(std::abs(best-.15)<1e-14,"independent finite physical optimum");
}
}
int main(int argc,char** argv){try {require(argc>=3,"Round167Research command arguments");const std::string mode=argv[1];
    if(mode=="prepare")prepare(argc,argv);else if(mode=="solve")solve(argc,argv);else if(mode=="local-prepare")localPrepare(argc,argv);
    else if(mode=="algebra")algebra(argv[2]);else if(mode=="tiny-oracle")tinyOracle(argv[2]);else throw std::invalid_argument("unsupported command/extension");return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
