#include "Round65Projection.hpp"
#include "FileSha256.hpp"
#include <sstream>
#include <stdexcept>
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <gurobi_c.h>
#endif
namespace ebrp {
namespace {
std::string arc(const char* p,int k,int i,int j) {return std::string(p)+std::to_string(k)+"_"+std::to_string(i)+"_"+std::to_string(j);}
std::string node(const char* p,int k,int i) {return std::string(p)+std::to_string(k)+"_"+std::to_string(i);}
double down(double x) {return std::nextafter(x,-std::numeric_limits<double>::infinity());}
double up(double x) {return std::nextafter(x,std::numeric_limits<double>::infinity());}
struct Enclosure {
    double lo=0,hi=0;
    void product(double x,double y) {
        if (x==0 || y==0) return;
        const double p=x*y;lo=down(lo+down(p));hi=up(hi+up(p));
    }
};
}
Round65VehicleMatrix makeRound65VehicleMatrix(const Instance& in,const Round63TimeData& d,int k,bool joint,bool release_load) {
    if(k<0||k>=in.M)throw std::runtime_error("vehicle index");
    Round65VehicleMatrix m;m.vehicle=k;m.identity=d.identity;
    std::map<std::string,int> index;
    for(int i=1;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)for(int type=0;type<2;++type) {
        const auto name=arc(type?"f_":"q_",k,i,j);index[name]=int(m.names.size());m.names.push_back(name);
        m.upper.push_back(type?d.upper[i][j]:in.Q[k]);
    }
    for(int i=0;i<=in.V;++i)for(int j=0;j<=in.V;++j)if(i!=j)m.original_upper[arc("x_",k,i,j)]=1;
    for(int i=1;i<=in.V;++i) {
        m.original_upper[node("p_",k,i)]=in.capacity[i];
        m.original_upper[node("d_",k,i)]=in.capacity[i];
        if(!release_load)m.original_upper[node("load_",k,i)]=in.Q[k];
        Round65ResourceRow qb{node("q_balance_",k,i),true,{},{{node("p_",k,i),1},{node("d_",k,i),-1}}};
        Round65ResourceRow ql{node("q_load_",k,i),true,{},{{node("load_",k,i),1}}};
        Round65ResourceRow fb{node("f_balance_",k,i),true,{},{{node("p_",k,i),d.handling}}};
        Round65ResourceRow b4{node("B4_",k,i),false,{},{{node("load_",k,i),-d.handling}}};
        for(int j=0;j<=in.V;++j)if(i!=j) {
            int q=index.at(arc("q_",k,i,j)),f=index.at(arc("f_",k,i,j));auto x=arc("x_",k,i,j);
            qb.auxiliary[q]=ql.auxiliary[q]=1;fb.auxiliary[f]=1;b4.auxiliary[f]=-1;
            m.rows.push_back({arc("q_cap_",k,i,j),false,{{q,1}},{{x,double(in.Q[k])}}});
            m.rows.push_back({arc("f_cap_",k,i,j),false,{{f,1}},{{x,d.upper[i][j]}}});
            if(joint&&d.handling>0)m.rows.push_back({arc("shared_",k,i,j),false,{{q,d.handling},{f,-1}},{}});
        }
        for(int h=1;h<=in.V;++h)if(h!=i){qb.auxiliary[index.at(arc("q_",k,h,i))]=-1;fb.auxiliary[index.at(arc("f_",k,h,i))]=-1;}
        for(int h=0;h<=in.V;++h)if(h!=i)fb.rhs[arc("x_",k,h,i)]+=d.travel[h][i];
        m.rows.push_back(qb);if(!release_load)m.rows.push_back(ql);m.rows.push_back(fb);
        if(d.handling>0 && !release_load)m.rows.push_back(b4);
    }
    return m;
}
Round65ProjectionRow verifyRound65Combination(const Round65VehicleMatrix& m,const std::vector<double>& ray,const std::map<std::string,double>& point) {
    Round65ProjectionRow cut;cut.identity=m.identity;cut.vehicle=m.vehicle;
    if(ray.size()!=m.rows.size())return cut;
    double norm=0;
    for(double y:ray){if(!std::isfinite(y))return cut;norm=std::max(norm,std::abs(y));}
    if(norm==0)return cut;
    std::vector<Enclosure> columns(m.names.size());std::map<std::string,Enclosure> coefficients;
    for(std::size_t i=0;i<ray.size();++i){
        double y=ray[i]/norm;if(!m.rows[i].equality)y=std::max(0.,y);
        cut.multipliers.push_back(y);
        for(const auto& [z,a]:m.rows[i].auxiliary)columns.at(z).product(y,a);
        for(const auto& [v,b]:m.rows[i].rhs)coefficients[v].product(y,b);
    }
    double rhs=0;
    for(std::size_t j=0;j<columns.size();++j){
        if(!std::isfinite(m.upper[j])||m.upper[j]<0)return cut;
        if(columns[j].lo<0)rhs=down(rhs+down(columns[j].lo*m.upper[j]));
    }
    for(const auto& [v,b]:coefficients){
        const auto p=point.find(v);const auto u=m.original_upper.find(v);
        if(p==point.end()||u==m.original_upper.end()||!std::isfinite(p->second)||!std::isfinite(b.lo)||!std::isfinite(b.hi))return cut;
        // Rows are globally valid for 0<=v<=physical upper; do not use a
        // point's tiny negative numerical value to narrow that legal scope.
        double c=b.lo+(b.hi-b.lo)*.5;
        if(c!=0)cut.coefficients[v]=c;
        const double error=down(c-b.hi);
        if(error<0)rhs=down(rhs+down(error*u->second));
    }
    long double activity=0;for(const auto& [v,c]:cut.coefficients)activity+=static_cast<long double>(c)*point.at(v);
    // A small extra outward margin is numerical safety, not coefficient pruning.
    cut.rhs=down(rhs);cut.activity=double(activity);cut.violation=cut.rhs-cut.activity;
    if(!std::isfinite(cut.rhs)||!std::isfinite(cut.activity)||cut.coefficients.empty()||cut.violation<=1e-7)return cut;
    std::ostringstream key;key<<std::setprecision(17)<<m.identity<<'|'<<m.vehicle<<'|'<<cut.rhs;
    for(const auto& [v,c]:cut.coefficients)key<<'|'<<v<<':'<<c;
    cut.signature=textSha256(key.str());cut.valid=true;return cut;
}

struct Round65ProjectionService::Impl {
    Instance in;Round63TimeData data;std::filesystem::path evidence;
    std::vector<Round65VehicleMatrix> matrices;long long queries=0;
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
    HMODULE dll=nullptr;GRBenv* env=nullptr;std::vector<GRBmodel*> models;
#define DECL(n) decltype(&GRB##n) n=nullptr
    DECL(emptyenvinternal);DECL(startenv);DECL(freeenv);DECL(newmodel);DECL(freemodel);DECL(getenv);
    DECL(setintparam);DECL(setdblparam);DECL(getintparam);DECL(getdblparam);DECL(setstrparam);
    DECL(addconstr);DECL(updatemodel);DECL(setdblattrarray);DECL(getdblattrarray);DECL(getintattr);DECL(getdblattr);DECL(optimize);
#undef DECL
    void check(int rc) {if(rc)throw std::runtime_error("Round65 auxiliary API "+std::to_string(rc));}
#endif
    Impl(const Instance& instance,const std::filesystem::path& path,bool release_load):in(instance),data(prepareRound63Time(instance)),evidence(path) {
        std::filesystem::create_directories(path);writeRound63TimeData(data,path/"physical.json");
        for(int k=0;k<in.M;++k)matrices.push_back(makeRound65VehicleMatrix(in,data,k,true,release_load));
        std::ofstream representation(path/"representation.json");representation<<"{\"release_load\":"<<(release_load?"true":"false")<<",\"matrix_reuse\":\"affine_rhs_only\"}\n";
        if(!representation)throw std::runtime_error("representation persistence");
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
        dll=LoadLibraryW((L"gurobi"+std::to_wstring(GRB_VERSION_MAJOR)+std::to_wstring(GRB_VERSION_MINOR)+L".dll").c_str());
        if(!dll)throw std::runtime_error("Round65 auxiliary DLL");
        try {
#define LOAD(n) n=reinterpret_cast<decltype(n)>(GetProcAddress(dll,"GRB" #n));if(!n)throw std::runtime_error("Round65 missing " #n)
        LOAD(emptyenvinternal);LOAD(startenv);LOAD(freeenv);LOAD(newmodel);LOAD(freemodel);LOAD(getenv);
        LOAD(setintparam);LOAD(setdblparam);LOAD(getintparam);LOAD(getdblparam);LOAD(setstrparam);
        LOAD(addconstr);LOAD(updatemodel);LOAD(setdblattrarray);LOAD(getdblattrarray);LOAD(getintattr);LOAD(getdblattr);LOAD(optimize);
#undef LOAD
        check(emptyenvinternal(&env,GRB_VERSION_MAJOR,GRB_VERSION_MINOR,GRB_VERSION_TECHNICAL));
        check(setintparam(env,"LogToConsole",0));check(startenv(env));models.resize(in.M,nullptr);
        } catch(...) {if(env&&freeenv)freeenv(env);FreeLibrary(dll);throw;}
#endif
    }
    ~Impl(){
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
        for(auto model:models)if(model)freemodel(model);
        if(env)freeenv(env);
        if(dll)FreeLibrary(dll);
#endif
    }
};
Round65ProjectionService::Round65ProjectionService(const Instance& in,const std::filesystem::path& path,bool release_load):impl_(std::make_unique<Impl>(in,path,release_load)){}
Round65ProjectionService::~Round65ProjectionService()=default;
const std::string& Round65ProjectionService::identity()const{return impl_->data.identity;}
Round65ProjectionReply Round65ProjectionService::query(int k,const std::map<std::string,double>& point,double remaining,Round65Budget& budget) {
    Round65ProjectionReply reply;auto& s=*impl_;auto grant=budget.grant(remaining);
    if(!grant.allowed())return reply;
    const auto start=std::chrono::steady_clock::now();double work=0;const auto sequence=s.queries++;
    auto elapsed=[&](){return std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();};
    try {
        const auto& m=s.matrices.at(k);
#if defined(_WIN32) && EXACT_EBRP_ENABLE_GUROBI
        auto& model=s.models.at(k);reply.reused=model!=nullptr;
        if(!model){
            std::vector<double> obj(m.names.size(),0),lb(m.names.size(),0),ub=m.upper;
            std::vector<char*> names;for(const auto& n:m.names)names.push_back(const_cast<char*>(n.c_str()));
            s.check(s.newmodel(s.env,&model,("vehicle_"+std::to_string(k)).c_str(),int(m.names.size()),obj.data(),lb.data(),ub.data(),nullptr,names.data()));
            for(const auto& r:m.rows){std::vector<int> ix;std::vector<double> a;for(const auto& [i,v]:r.auxiliary){ix.push_back(i);a.push_back(v);}
                s.check(s.addconstr(model,int(ix.size()),ix.data(),a.data(),r.equality?'=':'<',0,r.name.c_str()));}
            s.check(s.updatemodel(model));
        }
        auto env=s.getenv(model);
        for(auto [name,value]:{std::pair<const char*,int>{"Threads",1},{"Seed",0},{"Presolve",-1},{"DualReductions",0},{"InfUnbdInfo",1}}){
            int actual=-2;s.check(s.setintparam(env,name,value));s.check(s.getintparam(env,name,&actual));if(actual!=value)throw std::runtime_error("parameter readback");}
        for(const char* p:{"MIPGap","MIPGapAbs"}){double actual=-1;s.check(s.setdblparam(env,p,0));s.check(s.getdblparam(env,p,&actual));if(actual!=0)throw std::runtime_error("gap readback");}
        std::vector<double> rhs;for(const auto& r:m.rows){long double v=0;for(const auto& [n,c]:r.rhs)v+=static_cast<long double>(c)*point.at(n);rhs.push_back(double(v));}
        s.check(s.setdblattrarray(model,"RHS",0,int(rhs.size()),rhs.data()));s.check(s.updatemodel(model));
        const double seconds=std::min(grant.seconds,remaining)-elapsed();
        if(seconds<=0)throw std::runtime_error("construction exhausted optional grant");
        s.check(s.setdblparam(env,"TimeLimit",seconds));s.check(s.setdblparam(env,"WorkLimit",grant.work));
        double actual=0;s.check(s.getdblparam(env,"WorkLimit",&actual));if(actual!=grant.work)throw std::runtime_error("work readback");
        std::ofstream calls(s.evidence/"calls.csv",std::ios::app);
        if(std::filesystem::file_size(s.evidence/"calls.csv")==0)calls<<"query,vehicle,model_reused,work_limit,time_limit,columns,rows\n";
        calls<<std::setprecision(17)<<sequence<<','<<k<<','<<reply.reused<<','<<grant.work<<','<<seconds<<','<<m.names.size()<<','<<m.rows.size()<<'\n';calls.flush();
        s.check(s.setstrparam(env,"LogFile",(s.evidence/("aux_"+std::to_string(sequence)+".log")).string().c_str()));
        const int rc=s.optimize(model);s.getdblattr(model,"Work",&work);s.check(rc);
        int status=0;s.check(s.getintattr(model,"Status",&status));
        if(status==GRB_OPTIMAL){
            std::vector<double> x(m.names.size());s.check(s.getdblattrarray(model,"X",0,int(x.size()),x.data()));
            for(std::size_t j=0;j<x.size();++j)if(!std::isfinite(x[j])||x[j]<-1e-7||x[j]>m.upper[j]+1e-7)throw std::runtime_error("auxiliary bound residual");
            for(const auto& r:m.rows){long double a=0,b=0;for(const auto& [j,c]:r.auxiliary)a+=static_cast<long double>(c)*x[j];
                for(const auto& [n,c]:r.rhs)b+=static_cast<long double>(c)*point.at(n);
                if((r.equality?std::abs(a-b):a-b)>1e-7)throw std::runtime_error("auxiliary row residual");}
            reply.status="auxiliary_feasible";
        }
        else if(status==GRB_INFEASIBLE){
            std::vector<double> ray(m.rows.size());s.check(s.getdblattrarray(model,"FarkasDual",0,int(ray.size()),ray.data()));
            reply.row=verifyRound65Combination(m,ray,point);
            if(reply.row.valid){reply.status="verified_projection_row";
                std::ofstream proof(s.evidence/("row_"+std::to_string(sequence)+".json"));
                proof<<std::setprecision(17)<<"{\"identity\":"<<std::quoted(m.identity)<<",\"vehicle\":"<<k<<",\"scope\":\"physical_global\",\"rhs\":"<<reply.row.rhs
                    <<",\"activity\":"<<reply.row.activity<<",\"violation\":"<<reply.row.violation<<",\"signature\":"<<std::quoted(reply.row.signature)<<",\"multipliers\":{";
                bool first=true;for(std::size_t i=0;i<ray.size();++i)if(reply.row.multipliers[i]!=0){if(!first)proof<<',';first=false;proof<<std::quoted(m.rows[i].name)<<':'<<reply.row.multipliers[i];}proof<<"},\"coefficients\":{";
                first=true;for(const auto& [v,c]:reply.row.coefficients){if(!first)proof<<',';first=false;proof<<std::quoted(v)<<':'<<c;}proof<<"},\"point\":{";
                first=true;for(const auto& [v,u]:m.original_upper){(void)u;if(!first)proof<<',';first=false;proof<<std::quoted(v)<<':'<<point.at(v);}proof<<"}}\n";
                if(!proof)throw std::runtime_error("projection evidence persistence");
            }
        }
#else
        (void)m;(void)point;throw std::runtime_error("native backend unavailable");
#endif
    } catch(const std::exception& e) {reply.row=Round65ProjectionRow{};reply.status="unknown";
        std::ofstream f(s.evidence/"failures.txt",std::ios::app);f<<sequence<<' '<<e.what()<<'\n';}
    budget.charge(true,work,elapsed(),"vehicle_"+std::to_string(k),reply.status,grant);
    return reply;
}
} // namespace ebrp
