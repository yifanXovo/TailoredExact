#pragma once

#include "Round138Research.hpp"
#include <stdexcept>
#include <string>

namespace ebrp {
// Run-local research controls; no public SolveOptions/canonical ABI change.
struct Round139Controls {
    std::string placement = "legacy";
    bool enabled() const { return placement != "legacy"; }
    bool asymmetric() const { return placement == "lp-only" || placement == "mip-only"; }
    bool stock(bool native_mip) const {
        if (!enabled()) return round138().stock_rlt;
        return placement == "both" || placement == (native_mip ? "mip-only" : "lp-only");
    }
    void set(const std::string& value) {
        if (value != "base" && value != "both" && value != "lp-only" && value != "mip-only")
            throw std::runtime_error("Round139 stock placement must be base, both, lp-only or mip-only");
        placement = value;
    }
};
inline Round139Controls& round139() { static Round139Controls c; return c; }

// Scope only the existing V2 writer. Historical flag semantics are unchanged,
// including exception paths. Every solver call consumes immutable file bytes.
class Round139StockWriterScope {
    bool saved_;
public:
    explicit Round139StockWriterScope(bool stock) : saved_(round138().stock_rlt) {
        round138().stock_rlt = stock;
    }
    ~Round139StockWriterScope() { round138().stock_rlt = saved_; }
};
}
