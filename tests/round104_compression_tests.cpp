#include "ObjectiveResourceCompression.hpp"
#include <cassert>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>
int main(){using namespace ebrp;
    assert(resourceMultiplier(-2,'<',1)==2);assert(resourceMultiplier(-0.,'<',1)==0);
    for(auto bad:std::vector<int>{0,1,2}){bool rejected=false;try{
        resourceMultiplier(bad==0?1:-1,bad==1?'>':'<',bad==2?-1:1);
    }catch(const std::runtime_error&){rejected=true;}assert(rejected);}
    ObjectiveResourceRow a{"scope",0,{0,1},{-.1,.3},.2,.7};
    ObjectiveResourceRow b{"scope",0,{0,1},{.3,-.1},.1,.9};
    auto out=compressObjectiveResources({a,b},{-9,-8},{7,6});assert(out.size()==1);
    // Signed corners include negative lower bounds and both conversion signs.
    for(double x:{-9.,7.})for(double y:{-8.,6.}){
        const long double original=(long double)a.multiplier*(a.coefficients[0]* (long double)x+a.coefficients[1]*(long double)y-a.rhs)
            +(long double)b.multiplier*(b.coefficients[0]*(long double)x+b.coefficients[1]*(long double)y-b.rhs);
        const long double actual=(long double)out[0].coefficients[0]*x+(long double)out[0].coefficients[1]*y-out[0].rhs;
        assert(actual<=original);}
    a.multiplier=std::numeric_limits<double>::denorm_min();
    assert(activeResourceRows({a}).size()==1); // no epsilon pruning
    a.multiplier=0;assert(compressObjectiveResources({a},{0,0},{1,1}).empty());
    a.multiplier=-1;bool rejected=false;try{compressObjectiveResources({a},{0,0},{1,1});}catch(...){rejected=true;}assert(rejected);
    a.multiplier=1;b.scope="other";rejected=false;try{compressObjectiveResources({a,b},{0,0},{1,1});}catch(...){rejected=true;}assert(rejected);
    b.scope="scope";b.vehicle=1;assert(compressObjectiveResources({a,b},{0,0},{1,1}).size()==2);
    assert(compressObjectiveResources({a,b},{0,0},{1,1},true).size()==1);
    std::cout<<"R104 dual sign, zero/tiny multipliers, signed bounds, scope, groups passed\n";
}
