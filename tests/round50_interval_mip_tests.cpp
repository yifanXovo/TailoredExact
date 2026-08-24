#include "Round50IntervalMip.hpp"

#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

} // namespace

int main() {
    try {
        using namespace ebrp;
        const auto v0 = parseRound50IntervalMipPolicy("interval-mip-v0");
        const auto b1 = parseRound50IntervalMipPolicy("B1");
        const auto b2 = parseRound50IntervalMipPolicy("b2-route-first");
        const auto b3 = parseRound50IntervalMipPolicy("b3");
        const auto c1 = parseRound50IntervalMipPolicy("c1-exact-dedup");
        const auto s1 = parseRound50IntervalMipPolicy("s1-route-start-order");
        require(v0.valid && b1.valid && b2.valid && b3.valid && c1.valid &&
                    s1.valid,
                "all frozen branching and C1 policies parse");
        require(c1.branching == Round50BranchingPolicy::Default &&
                    c1.cut_formulation == "exact-duplicate-elimination",
                "C1 changes only cut/formulation policy");
        require(s1.branching == Round50BranchingPolicy::Default &&
                    s1.cut_formulation == "v0" &&
                    s1.symmetry_numerical == "route-start-order",
                "S1 changes only the symmetry policy");
        require(!parseRound50IntervalMipPolicy("instance-special").valid,
                "unknown policies fail closed");
        require(classifyRound50Variable("x_0_1_2") ==
                    Round50VariableFamily::RoutingArc,
                "routing family");
        require(classifyRound50Variable("z_0_1") ==
                    Round50VariableFamily::VisitSelection,
                "visit family");
        require(classifyRound50Variable("mode_0_1") ==
                    Round50VariableFamily::OperationMode,
                "mode family");
        require(classifyRound50Variable("p_0_1") ==
                    Round50VariableFamily::PickupQuantity,
                "pickup family");
        require(classifyRound50Variable("d_0_1") ==
                    Round50VariableFamily::DropQuantity,
                "drop family");
        require(classifyRound50Variable("load_0_1") ==
                    Round50VariableFamily::VehicleLoad,
                "load family");
        require(classifyRound50Variable("Y_1") ==
                    Round50VariableFamily::FinalInventory,
                "canonical inventory family");
        require(classifyRound50Variable("y_1") ==
                    Round50VariableFamily::FinalInventory,
                "legacy lowercase inventory family");
        for (const std::string auxiliary : {
                 "conn_0_1_2", "ord_0_1", "bit_1_2", "prod_1_2",
                 "h_1_2", "r_1", "e_1", "zprod_1", "W", "G"}) {
            require(classifyRound50Variable(auxiliary) ==
                        Round50VariableFamily::Auxiliary,
                    "canonical auxiliary family: " + auxiliary);
        }
        require(round50BranchPriority(
                    Round50BranchingPolicy::PrimitiveFirst,
                    Round50VariableFamily::RoutingArc) >
                round50BranchPriority(
                    Round50BranchingPolicy::PrimitiveFirst,
                    Round50VariableFamily::Auxiliary),
                "B1 primitive above auxiliary");
        require(round50BranchPriority(
                    Round50BranchingPolicy::RouteFirst,
                    Round50VariableFamily::RoutingArc) >
                round50BranchPriority(
                    Round50BranchingPolicy::RouteFirst,
                    Round50VariableFamily::VisitSelection),
                "B2 route hierarchy");
        require(round50BranchPriority(
                    Round50BranchingPolicy::OperationFirst,
                    Round50VariableFamily::VisitSelection) >
                round50BranchPriority(
                    Round50BranchingPolicy::OperationFirst,
                    Round50VariableFamily::RoutingArc),
                "B3 operation hierarchy");
        require(round50BranchPriority(
                    Round50BranchingPolicy::Default,
                    Round50VariableFamily::RoutingArc) == 0,
                "default-off equivalence uses no priority assignment");
        require(round50OmitDuplicateModeLink(0, true),
                "C1 omits the second zero-bound mode link");
        require(!round50OmitDuplicateModeLink(1, true) &&
                    !round50OmitDuplicateModeLink(0, false),
                "C1 preserves nonduplicates and default-off rows");
        SolveOptions options;
        configureRound50IntervalMipV0(options);
        require(options.gurobi_seed == 0 && options.gurobi_presolve == -1 &&
                    options.threads == 1 && options.mip_threads == 1,
                "solver contract options");
        require(options.round47_c6_adaptive_mass == "off" &&
                    options.round48_k1_amf == "off" &&
                    options.round49_k1_am_rc == "off",
                "split mechanisms remain off in fixed-state driver");
        std::cout << "Round50IntervalMipTests passed\n";
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "Round50IntervalMipTests failed: " << ex.what() << '\n';
        return 1;
    }
}
