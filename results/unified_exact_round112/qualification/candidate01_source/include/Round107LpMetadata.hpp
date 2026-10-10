#pragma once
#include <cmath>
#include <cstdlib>
#include <istream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>

namespace ebrp {
// Evidence only: the original LP backend has already read and solved these bytes.
// Compare the canonical objective and cutoff semantically, not by term order.
inline std::string round107Trim(const std::string& s) {
    const auto a=s.find_first_not_of(" \t\r\n");
    return a==std::string::npos?"":s.substr(a,s.find_last_not_of(" \t\r\n")-a+1);
}
inline bool round107FiniteNumber(const std::string& s,double& x) {
    if(s.empty())return false;
    char* end=nullptr;x=std::strtod(s.c_str(),&end);
    return end!=s.c_str()&&*end=='\0'&&std::isfinite(x);
}
inline std::map<std::string,double> round107LinearTerms(const std::string& expression) {
    std::map<std::string,double> terms;std::istringstream input(expression);std::string token;
    bool first=true;double sign=1;
    while(input>>token) {
        if(token=="+"||token=="-") {
            sign=token=="-"?-1:1;
            if(!(input>>token)||token=="+"||token=="-")throw std::runtime_error("round107_LP_malformed_sign");
        } else if(!first)throw std::runtime_error("round107_LP_missing_term_separator");
        double coefficient=1,parsed=0;std::string name=token;
        if(round107FiniteNumber(token,parsed)) {
            coefficient=parsed;
            if(!(input>>name)) {
                if(parsed==0&&first){first=false;break;}
                throw std::runtime_error("round107_LP_unexpected_constant");
            }
        }
        if(name.empty()||!((name[0]>='A'&&name[0]<='Z')||(name[0]>='a'&&name[0]<='z')||name[0]=='_'))
            throw std::runtime_error("round107_LP_invalid_variable");
        for(char c:name)if(!((c>='A'&&c<='Z')||(c>='a'&&c<='z')||(c>='0'&&c<='9')||c=='_'))
            throw std::runtime_error("round107_LP_invalid_variable");
        terms[name]+=sign*coefficient;
        if(!std::isfinite(terms[name]))throw std::runtime_error("round107_LP_nonfinite_coefficient");
        sign=1;first=false;
    }
    if(first)throw std::runtime_error("round107_LP_empty_expression");
    for(auto it=terms.begin();it!=terms.end();)if(it->second==0)it=terms.erase(it);else ++it;
    return terms;
}
inline bool round107SameTerms(const std::map<std::string,double>& a,const std::map<std::string,double>& b) {
    if(a.size()!=b.size())return false;
    auto x=a.begin(),y=b.begin();
    for(;x!=a.end();++x,++y)if(x->first!=y->first||x->second!=y->second)return false;
    return true;
}
struct Round107LpCutoffMetadata {bool present=false;double rhs=0;};
inline Round107LpCutoffMetadata round107ReadLpCutoff(std::istream& input,double verified_cutoff) {
    Round107LpCutoffMetadata result;result.rhs=verified_cutoff;
    std::string line,objective,row;bool minimizing=false,in_rows=false,objective_seen=false;
    std::map<std::string,double> terms;
    auto finishRow=[&]() {
        if(row.empty())return;
        const auto at=row.find("<=");
        if(at!=std::string::npos) {
            double rhs=0;
            if(!round107FiniteNumber(round107Trim(row.substr(at+2)),rhs))throw std::runtime_error("round107_LP_invalid_rhs");
            if(round107SameTerms(round107LinearTerms(row.substr(0,at)),terms)) {
                if(!result.present||rhs<result.rhs)result.rhs=rhs;
                result.present=true;
            }
        }
        row.clear();
    };
    while(std::getline(input,line)) {
        const auto s=round107Trim(line);if(s.empty()||s[0]=='\\')continue;
        if(s=="Minimize"){minimizing=true;continue;}
        if(s=="Subject To"||s=="Subject to"||s=="Such That") {
            if(!minimizing||objective.empty())throw std::runtime_error("round107_LP_objective_metadata_missing");
            terms=round107LinearTerms(objective);objective_seen=true;in_rows=true;continue;
        }
        if(in_rows&&(s=="Bounds"||s=="Binaries"||s=="Generals"||s=="End")){finishRow();break;}
        const auto colon=s.find(':');
        if(!in_rows&&minimizing) {
            objective+=' '+(colon==std::string::npos?s:s.substr(colon+1));
        } else if(in_rows) {
            if(colon!=std::string::npos){finishRow();row=s.substr(colon+1);}
            else {if(row.empty())throw std::runtime_error("round107_LP_constraint_label_missing");row+=' '+s;}
        }
    }
    finishRow();
    if(!objective_seen)throw std::runtime_error("round107_LP_objective_metadata_missing");
    if(!result.present)throw std::runtime_error("round107_LP_cutoff_metadata_row_missing");
    return result;
}
}
