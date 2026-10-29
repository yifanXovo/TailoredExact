#pragma once

namespace ebrp {
// Research-only shared inventory-product coupling. No SolveOptions ABI change.
struct Round138Controls {
    bool stock_rlt = false;
};
inline Round138Controls& round138() { static Round138Controls c; return c; }
}
