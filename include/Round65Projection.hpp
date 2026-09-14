#pragma once
#include "Round63TimeResource.hpp"
#include "Round65Proof.hpp"
#include <map>
#include <memory>
#include <vector>

namespace ebrp {
struct Round65ResourceRow {
    std::string name;
    bool equality = false;
    std::map<int,double> auxiliary;
    std::map<std::string,double> rhs;
};
struct Round65VehicleMatrix {
    int vehicle = -1;
    std::string identity;
    std::vector<std::string> names;
    std::vector<double> upper;
    std::map<std::string,double> original_upper;
    std::vector<Round65ResourceRow> rows;
};
Round65VehicleMatrix makeRound65VehicleMatrix(const Instance&, const Round63TimeData&, int vehicle, bool joint=true);
struct Round65ProjectionRow {
    bool valid = false;
    std::string identity, signature;
    int vehicle = -1;
    std::map<std::string,double> coefficients;
    std::vector<double> multipliers;
    double rhs = 0, activity = 0, violation = 0;
};
// Arbitrary legal multipliers give a valid row. Infeasibility status is never
// sufficient. Outward arithmetic covers column residuals and row rounding.
Round65ProjectionRow verifyRound65Combination(const Round65VehicleMatrix&,
    const std::vector<double>& ray, const std::map<std::string,double>& point);
struct Round65ProjectionReply {
    std::string status = "unknown";
    Round65ProjectionRow row;
    bool reused = false;
};
class Round65ProjectionService {
public:
    Round65ProjectionService(const Instance&, const std::filesystem::path& evidence);
    ~Round65ProjectionService();
    Round65ProjectionReply query(int vehicle, const std::map<std::string,double>& point,
                                double remaining, Round65Budget&);
    const std::string& identity() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace ebrp
