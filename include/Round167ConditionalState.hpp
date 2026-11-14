#pragma once
// A single fixed MSB-first interval construction. No stock enumeration,
// variable-order search, or independent product block is used by the DAG.
#include <algorithm>
#include <array>
#include <cstdint>
#include <functional>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace ebrp {
inline int round167Bits(int capacity) {
    if(capacity<0)throw std::invalid_argument("negative capacity");
    int d=0;for(unsigned int c=static_cast<unsigned int>(capacity);c;c>>=1)++d;
    return std::max(1,d);
}
struct Round167Arc {
    int tail,head,part,bit,value;
    std::int64_t Y,M,V;
};
struct Round167Part {int lower,upper,direction,entry;};
struct Round167DAG {
    int lower,upper,initial,capacity,bits,nodes=2;
    std::vector<Round167Arc> arcs;
    std::vector<Round167Part> parts;
    Round167DAG(int l,int u,int b,int C):lower(l),upper(u),initial(b),capacity(C),bits(round167Bits(C)) {
        if(l<0||u>C||b<0||b>C)throw std::invalid_argument("invalid stock domain");
        if(l>u)return; // Explicit disconnected source/sink: unit flow infeasible.
        addPart(l,std::min(u,b-1),-1);
        if(l<=b&&b<=u)addPart(b,b,0);
        if(b<u)addPart(std::max(l,b+1),u,1); // Avoid b+1 overflow at INT_MAX.
    }
    void addPart(int l,int u,int direction) {
        if(l>u)return;
        const int part=static_cast<int>(parts.size());
        const int root=nodes++,entry=static_cast<int>(arcs.size());
        arcs.push_back({0,root,part,-1,-1,0,direction<0?initial:direction>0?-initial:0,direction!=0});
        parts.push_back({l,u,direction,entry});
        // The two tightness bits are the complete suffix feasibility state.
        std::map<int,int> layer{{3,root}};
        for(int h=bits-1;h>=0;--h) {
            std::map<int,int> next;
            const int lb=(l>>h)&1,ub=(u>>h)&1;
            for(const auto& item:layer)for(int value=0;value<=1;++value) {
                const bool tl=(item.first&1)!=0,tu=(item.first&2)!=0;
                if((tl&&value<lb)||(tu&&value>ub))continue;
                const int state=(tl&&value==lb?1:0)|(tu&&value==ub?2:0);
                auto found=next.find(state);
                const int head=found==next.end()?(next[state]=nodes++):found->second;
                const std::int64_t y=value?(std::int64_t(1)<<h):0;
                arcs.push_back({item.second,head,part,h,value,y,direction*y,0});
            }
            layer=std::move(next);
        }
        for(const auto& item:layer)arcs.push_back({item.second,1,part,-1,-1,0,0,0});
    }
    std::vector<int> path(int y) const {
        if(y<lower||y>upper)throw std::invalid_argument("start stock outside domain");
        int part=-1;
        for(int p=0;p<static_cast<int>(parts.size());++p)
            if(parts[p].lower<=y&&y<=parts[p].upper)part=p;
        if(part<0)throw std::logic_error("no service part");
        std::vector<int> result{parts[part].entry};int at=arcs[result.back()].head;
        for(int h=bits-1;h>=0;--h) {
            int chosen=-1;
            for(int j=0;j<static_cast<int>(arcs.size());++j)
                if(arcs[j].tail==at&&arcs[j].bit==h&&arcs[j].value==((y>>h)&1)) {
                    if(chosen>=0)throw std::logic_error("nondeterministic path");chosen=j;
                }
            if(chosen<0)throw std::logic_error("missing bit edge");
            result.push_back(chosen);at=arcs[chosen].head;
        }
        for(int j=0;j<static_cast<int>(arcs.size());++j)
            if(arcs[j].tail==at&&arcs[j].head==1){result.push_back(j);return result;}
        throw std::logic_error("missing terminal edge");
    }
    // Used only by finite independent path checks, never graph construction.
    std::vector<int> inventories(const std::map<int,int>& mask={}) const {
        std::vector<std::vector<int>> outgoing(nodes);
        for(int e=0;e<static_cast<int>(arcs.size());++e)outgoing[arcs[e].tail].push_back(e);
        std::vector<int> result;
        std::function<void(int,std::int64_t)> visit=[&](int at,std::int64_t y) {
            if(at==1){result.push_back(static_cast<int>(y));return;}
            for(int e:outgoing[at]) {
                auto bit=mask.find(arcs[e].bit);
                if(arcs[e].bit>=0&&bit!=mask.end()&&bit->second!=arcs[e].value)continue;
                visit(arcs[e].head,y+arcs[e].Y);
            }
        };
        visit(0,0);std::sort(result.begin(),result.end());return result;
    }
    std::int64_t count(const std::map<int,int>& mask={}) const {
        std::vector<std::vector<int>> outgoing(nodes);
        for(int e=0;e<static_cast<int>(arcs.size());++e)outgoing[arcs[e].tail].push_back(e);
        std::vector<std::int64_t> memo(nodes,-1);memo[1]=1;
        std::function<std::int64_t(int)> visit=[&](int at) {
            if(memo[at]>=0)return memo[at];
            std::int64_t total=0;
            for(int e:outgoing[at]) {
                auto bit=mask.find(arcs[e].bit);
                if(arcs[e].bit>=0&&bit!=mask.end()&&bit->second!=arcs[e].value)continue;
                total+=visit(arcs[e].head);
            }
            return memo[at]=total;
        };
        return visit(0);
    }
};
inline std::string round167F(int i,int e){return "d167_f_"+std::to_string(i)+"_"+std::to_string(e);}
inline std::string round167Q(int i,int e){return "d167_q_"+std::to_string(i)+"_"+std::to_string(e);}
} // namespace ebrp
