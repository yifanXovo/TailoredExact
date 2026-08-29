#include "CanonicalCompactModel.hpp"
#include "FileSha256.hpp"
#include "FixedIntervalMipBackend.hpp"
#include "InventoryRouteRootClosure.hpp"
#include "Parser.hpp"
#include "Round50IntervalMip.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

using Clock = std::chrono::steady_clock;

struct Arguments {
    std::string mode = "closure";
    std::string state_id;
    std::filesystem::path input;
    std::filesystem::path artifact_dir;
    std::string variant = "ir1";
    std::string gurobi_home;
    double gamma_lower = 0.0;
    double gamma_upper = 0.0;
    double cutoff = 0.0;
    double process_cap_seconds = 300.0;
    double route_time_limit = 2850.0;
    double pickup_time = 60.0;
    double drop_time = 60.0;
};

bool isF0Variant(const std::string& value) {
    std::string lowered = value;
    std::transform(lowered.begin(), lowered.end(), lowered.begin(),
        [](unsigned char ch) { return static_cast<char>(std::tolower(ch)); });
    return lowered == "f0" || lowered == "f0-clean" ||
        lowered == "interval-mip-core-no-exhaustive-subset-duration";
}

std::string jsonEscape(const std::string& value) {
    std::ostringstream out;
    for (unsigned char ch : value) {
        switch (ch) {
        case '\\': out << "\\\\"; break;
        case '"': out << "\\\""; break;
        case '\n': out << "\\n"; break;
        case '\r': out << "\\r"; break;
        case '\t': out << "\\t"; break;
        default: out << static_cast<char>(ch); break;
        }
    }
    return out.str();
}

std::string csvField(const std::string& value) {
    std::string out = "\"";
    for (char ch : value) {
        if (ch == '"') out.push_back('"');
        out.push_back(ch);
    }
    out.push_back('"');
    return out;
}

double elapsed(const Clock::time_point& start) {
    return std::chrono::duration<double>(Clock::now() - start).count();
}

Arguments parseArguments(int argc, char** argv) {
    Arguments out;
    auto value = [&](int& index) -> std::string {
        if (++index >= argc) throw std::runtime_error("missing option value");
        return argv[index];
    };
    for (int i = 1; i < argc; ++i) {
        const std::string arg = argv[i];
        if (arg == "--mode") out.mode = value(i);
        else if (arg == "--state-id") out.state_id = value(i);
        else if (arg == "--input") out.input = value(i);
        else if (arg == "--artifact-dir") out.artifact_dir = value(i);
        else if (arg == "--variant") out.variant = value(i);
        else if (arg == "--gurobi-home") out.gurobi_home = value(i);
        else if (arg == "--gamma-lower") out.gamma_lower = std::stod(value(i));
        else if (arg == "--gamma-upper") out.gamma_upper = std::stod(value(i));
        else if (arg == "--cutoff") out.cutoff = std::stod(value(i));
        else if (arg == "--process-cap") out.process_cap_seconds = std::stod(value(i));
        else if (arg == "--route-time-limit") out.route_time_limit = std::stod(value(i));
        else if (arg == "--pickup-time") out.pickup_time = std::stod(value(i));
        else if (arg == "--drop-time") out.drop_time = std::stod(value(i));
        else throw std::runtime_error("unknown option: " + arg);
    }
    if (out.state_id.empty() || out.input.empty() || out.artifact_dir.empty()) {
        throw std::runtime_error("--state-id, --input, and --artifact-dir are required");
    }
    if (out.mode != "closure" && out.mode != "solve") {
        throw std::runtime_error("--mode must be closure or solve");
    }
    if (!(out.process_cap_seconds > 0.0) ||
        !std::isfinite(out.process_cap_seconds) ||
        !std::isfinite(out.gamma_lower) || !std::isfinite(out.gamma_upper) ||
        out.gamma_lower < 0.0 || out.gamma_upper < out.gamma_lower ||
        !std::isfinite(out.cutoff)) {
        throw std::runtime_error("invalid numerical argument");
    }
    return out;
}

void writeCommand(const Arguments& args) {
    std::ofstream out(args.artifact_dir / "command.json");
    out << std::setprecision(17)
        << "{\n  \"schema\": \"round54-inventory-route-command-v1\",\n"
        << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
        << "  \"mode\": \"" << args.mode << "\",\n"
        << "  \"variant\": \"" << jsonEscape(args.variant) << "\",\n"
        << "  \"input\": \"" << jsonEscape(
               std::filesystem::absolute(args.input).string()) << "\",\n"
        << "  \"input_sha256\": \"" << ebrp::fileSha256(args.input) << "\",\n"
        << "  \"gamma_lower\": " << args.gamma_lower << ",\n"
        << "  \"gamma_upper\": " << args.gamma_upper << ",\n"
        << "  \"cutoff\": " << args.cutoff << ",\n"
        << "  \"process_cap_seconds\": " << args.process_cap_seconds << ",\n"
        << "  \"threads\": 1,\n  \"seed\": 0,\n"
        << "  \"presolve\": \"Auto\",\n"
        << "  \"mip_gap\": 0,\n  \"mip_gap_abs\": 0,\n"
        << "  \"callback\": \"off\",\n"
        << "  \"precrush\": \"default\",\n"
        << "  \"branching\": \"gurobi-default\"\n}\n";
}

void writeClosureLedgers(
    const Arguments& args,
    const ebrp::InventoryRouteRootClosureResult& closure) {
    std::ofstream rounds(args.artifact_dir / "external_root_closure_ledger.csv");
    rounds << "state_id,variant,round,lp_valid,lp_infeasible,lp_objective,lp_work,lp_time,lp_simplex_iterations,max_in_violation,in_subset,max_out_violation,out_subset,max_proj_in_violation,proj_in_subset,max_proj_out_violation,proj_out_subset,cuts_generated,cuts_added,duplicates,dominated,nonviolated,status\n";
    rounds << std::setprecision(17);
    for (const auto& round : closure.rounds) {
        auto subset = [](const ebrp::InventoryRouteCut& cut) {
            std::ostringstream value;
            for (std::size_t i = 0; i < cut.subset.size(); ++i) {
                if (i) value << ';';
                value << cut.subset[i];
            }
            return value.str();
        };
        rounds << csvField(args.state_id) << ',' << csvField(closure.variant)
               << ',' << round.round << ',' << round.lp_valid << ','
               << round.lp_infeasible << ',' << round.lp_objective << ','
               << round.lp_work << ',' << round.lp_runtime_seconds << ','
               << round.lp_simplex_iterations << ','
               << round.separation.mixed_inbound.raw_violation << ','
               << csvField(subset(round.separation.mixed_inbound)) << ','
               << round.separation.mixed_outbound.raw_violation << ','
               << csvField(subset(round.separation.mixed_outbound)) << ','
               << round.separation.projected_inbound.raw_violation << ','
               << csvField(subset(round.separation.projected_inbound)) << ','
               << round.separation.projected_outbound.raw_violation << ','
               << csvField(subset(round.separation.projected_outbound)) << ','
               << round.cuts_generated << ',' << round.cuts_added << ','
               << round.duplicate_rejections << ','
               << round.dominated_rejections << ','
               << round.nonviolated_rejections << ','
               << csvField(round.status) << '\n';
    }
    std::ofstream pool(args.artifact_dir / "root_cut_pool_ledger.csv");
    pool << "state_id,variant,ordinal,family,scope,subset,raw_violation,scaled_violation,mincut_objective,direct_objective,sense,rhs,term_count,canonical_signature\n";
    pool << std::setprecision(17);
    for (std::size_t i = 0; i < closure.accepted_cuts.size(); ++i) {
        const auto& cut = closure.accepted_cuts[i];
        std::ostringstream subset;
        for (std::size_t j = 0; j < cut.subset.size(); ++j) {
            if (j) subset << ';';
            subset << cut.subset[j];
        }
        pool << csvField(args.state_id) << ',' << csvField(closure.variant)
             << ',' << i << ',' << csvField(
                 ebrp::inventoryRouteCutKindName(cut.kind)) << ','
             << csvField(cut.scope) << ',' << csvField(subset.str()) << ','
             << cut.raw_violation << ',' << cut.scaled_violation << ','
             << cut.mincut_objective << ',' << cut.direct_recomputed_objective
             << ',' << cut.sense << ',' << cut.rhs << ','
             << cut.row_coefficients.size() << ','
             << csvField(cut.canonical_signature) << '\n';
    }
    std::ofstream overhead(args.artifact_dir / "root_closure_overhead_audit.csv");
    overhead << "state_id,variant,rounds,cuts_added,initial_lp_objective,final_lp_objective,lp_bound_gain,closure_work,closure_solver_time,model_read_time,simplex_iterations,valid,converged,infeasible,fallback_required,failure_reason\n"
             << csvField(args.state_id) << ',' << csvField(closure.variant)
             << ',' << closure.rounds.size() << ',' << closure.cuts_added
             << ',' << std::setprecision(17) << closure.initial_lp_objective
             << ',' << closure.final_lp_objective << ','
             << closure.final_lp_objective - closure.initial_lp_objective
             << ',' << closure.cumulative_lp_work << ','
             << closure.cumulative_lp_runtime_seconds << ','
             << closure.model_read_seconds << ','
             << closure.cumulative_lp_simplex_iterations << ','
             << closure.valid << ',' << closure.converged << ','
             << closure.infeasible << ',' << closure.fallback_required << ','
             << csvField(closure.failure_reason) << '\n';
}

void writeMipProgress(
    const Arguments& args,
    const ebrp::FixedIntervalMipOutcome& terminal) {
    std::ofstream progress(args.artifact_dir / "mip_progress.csv");
    progress << "time_seconds,work,bound_available,best_bound,incumbent_available,incumbent,processed_nodes,open_nodes,native_phase,bound_improved\n"
             << std::setprecision(17);
    for (const auto& event : terminal.native_bound_events) {
        progress << event.solver_runtime_seconds << ',' << event.work << ','
                 << event.native_bound_available << ',' << event.native_bound
                 << ',' << event.native_incumbent_available << ','
                 << event.native_incumbent << ',' << event.processed_nodes
                 << ',' << event.open_nodes << ',' << event.native_phase << ','
                 << event.bound_improved << '\n';
    }
}

} // namespace

int main(int argc, char** argv) {
    const Clock::time_point started = Clock::now();
    try {
        const Arguments args = parseArguments(argc, argv);
        std::filesystem::create_directories(args.artifact_dir);
        writeCommand(args);
        const bool f0_reference = isF0Variant(args.variant);
        const ebrp::InventoryRouteClosureVariant variant = f0_reference
            ? ebrp::InventoryRouteClosureVariant::Invalid
            : ebrp::parseInventoryRouteClosureVariant(args.variant);
        if (!f0_reference &&
            variant == ebrp::InventoryRouteClosureVariant::Invalid) {
            throw std::runtime_error("invalid inventory-route variant");
        }
        const ebrp::Instance instance = ebrp::parseInstanceFile(
            args.input, args.route_time_limit, args.pickup_time, args.drop_time);
        ebrp::SolveOptions options;
        ebrp::configureRound50IntervalMipV0(options);
        options.gurobi_home = args.gurobi_home;
        options.gurobi_presolve = -1;
        options.log_path = (args.artifact_dir / "environment.log").string();
        ebrp::CanonicalCompactModelSpec spec;
        spec.strengthened = true;
        spec.interval_restricted = true;
        spec.gamma_L = args.gamma_lower;
        spec.gamma_U = args.gamma_upper;
        spec.add_verified_incumbent_row = true;
        spec.verified_incumbent = args.cutoff;
        spec.round51_subset_duration_big_m = "off";
        const auto artifact = ebrp::writeCanonicalCompactModel(
            instance, options, args.artifact_dir / "canonical_f0_model.lp", spec);
        if (!artifact.written) {
            throw std::runtime_error(artifact.failure_reason);
        }
        std::unique_ptr<ebrp::FixedIntervalMipBackend> backend =
            ebrp::makeGurobiFixedIntervalBackend(instance, options);
        if (!backend || !backend->capabilities().available) {
            throw std::runtime_error(backend
                ? backend->capabilities().failure_reason : "backend unavailable");
        }
        ebrp::FixedIntervalMipRequest request;
        request.leaf_id = args.state_id;
        request.gamma_L = args.gamma_lower;
        request.gamma_U = args.gamma_upper;
        request.verified_cutoff = args.cutoff;
        request.global_deadline_remaining_seconds = std::max(
            0.001, args.process_cap_seconds - elapsed(started) - 2.0);
        request.canonical_model_path = artifact.path;
        request.canonical_model_fingerprint = artifact.sha256;
        request.canonical_model_scope = artifact.model_scope;
        request.canonical_row_signature = artifact.row_signature;
        request.native_log_path = args.artifact_dir / "root_lp.log";
        request.interval_mip_policy = f0_reference
            ? "interval-mip-core-no-exhaustive-subset-duration"
            : args.variant;
        ebrp::InventoryRouteRootClosureResult closure;
        if (f0_reference) {
            closure.attempted = true;
            closure.variant = "F0-CLEAN";
            ebrp::FixedIntervalMipRequest root_request = request;
            root_request.solve_kind =
                ebrp::FixedIntervalSolveKind::PaperLpRelaxation;
            root_request.leaf_id = args.state_id + "__f0_reference_root_lp";
            root_request.capture_lp_primal_dual_evidence = false;
            root_request.native_log_path = args.artifact_dir / "root_lp.log";
            const ebrp::FixedIntervalMipOutcome root = backend->solve(root_request);
            ebrp::InventoryRouteClosureRound round;
            round.round = 0;
            round.lp_work = root.work;
            round.lp_runtime_seconds = root.solver_runtime_seconds;
            round.lp_simplex_iterations = root.simplex_iterations;
            round.lp_infeasible = root.lp_terminal_valid && root.infeasible;
            round.lp_valid = round.lp_infeasible ||
                (root.lp_terminal_valid && root.optimal &&
                 root.lp_objective_value_available &&
                 root.model_fingerprint_matches_request &&
                 root.additional_linear_rows_valid);
            round.lp_objective = root.lp_objective_value;
            round.status = round.lp_valid
                ? "f0_reference_root_lp_complete"
                : "f0_reference_root_lp_invalid";
            closure.rounds.push_back(round);
            closure.initial_lp_objective = root.lp_objective_value;
            closure.final_lp_objective = root.lp_objective_value;
            closure.cumulative_lp_work = root.work;
            closure.cumulative_lp_runtime_seconds =
                root.solver_runtime_seconds;
            closure.cumulative_lp_simplex_iterations =
                root.simplex_iterations;
            closure.model_read_seconds = root.model_read_seconds;
            closure.infeasible = round.lp_infeasible;
            closure.converged = round.lp_valid;
            closure.valid = round.lp_valid;
            closure.fallback_required = !round.lp_valid;
            closure.failure_reason = round.lp_valid
                ? "none" : (root.failure_reason.empty()
                    ? "invalid_f0_reference_root_lp" : root.failure_reason);
        } else {
            closure = ebrp::runInventoryRouteRootClosure(
                *backend, instance, request, variant, 1e-7);
        }
        writeClosureLedgers(args, closure);

        ebrp::FixedIntervalMipOutcome terminal;
        bool fallback_used = false;
        if (args.mode == "solve") {
            ebrp::FixedIntervalMipRequest terminal_request = request;
            terminal_request.solve_kind =
                ebrp::FixedIntervalSolveKind::PaperTerminalMip;
            terminal_request.leaf_id = args.state_id + "__terminal";
            terminal_request.native_log_path =
                args.artifact_dir / "terminal_mip.log";
            terminal_request.capture_native_bound_events = true;
            terminal_request.global_deadline_remaining_seconds = std::max(
                0.001, args.process_cap_seconds - elapsed(started) - 2.0);
            if (closure.valid && !closure.fallback_required) {
                for (std::size_t index = 0;
                     index < closure.accepted_cuts.size(); ++index) {
                    terminal_request.additional_linear_rows.push_back(
                        ebrp::inventoryRouteBackendRow(
                            closure.accepted_cuts[index],
                            static_cast<int>(index)));
                }
            } else {
                fallback_used = true;
                terminal_request.interval_mip_policy =
                    "interval-mip-core-no-exhaustive-subset-duration";
            }
            terminal = backend->solve(terminal_request);
            writeMipProgress(args, terminal);
        }
        backend->release();
        const auto stats = backend->stats();
        const double process_seconds = elapsed(started);
        const bool terminal_engineering = args.mode != "solve" ||
            (terminal.attempted && terminal.available &&
             terminal.solver_finalization_reached &&
             terminal.model_fingerprint_matches_request &&
             terminal.exact_zero_gap_roundtrip &&
             terminal.feasibility_consistency_gate &&
             terminal.additional_linear_rows_valid &&
             !terminal.tailored_cut_callback_active &&
             terminal.gurobi_precrush_requested == -1 &&
             terminal.branch_priority_assignment_status ==
                "default_no_assignment");
        const bool exact = args.mode == "solve" && terminal_engineering &&
            (terminal.infeasible ||
             (terminal.native_exact_optimal && terminal.native_bound_available &&
              terminal.incumbent_available &&
              terminal.incumbent_independently_verified &&
              std::fabs(terminal.native_bound - terminal.incumbent_objective) <=
                  1e-7 * std::max(1.0,
                      std::fabs(terminal.incumbent_objective))));
        const bool verified_upper_bound_available =
            terminal.incumbent_available &&
            terminal.incumbent_independently_verified;
        const double verified_upper_bound = verified_upper_bound_available
            ? terminal.incumbent_objective : args.cutoff;
        const double lower_bound = terminal.native_bound_available
            ? terminal.native_bound : closure.final_lp_objective;
        const double final_gap = std::max(0.0,
            (verified_upper_bound - lower_bound) /
                std::max(1e-12, std::fabs(verified_upper_bound)));
        const ebrp::InventoryRouteSeparationResult* initial_separation =
            closure.rounds.empty() ? nullptr : &closure.rounds.front().separation;
        auto subsetJson = [](const ebrp::InventoryRouteCut* cut) {
            std::ostringstream value;
            value << '[';
            if (cut) {
                for (std::size_t i = 0; i < cut->subset.size(); ++i) {
                    if (i) value << ',';
                    value << cut->subset[i];
                }
            }
            value << ']';
            return value.str();
        };
        std::ofstream result(args.artifact_dir / "result.json");
        result << std::setprecision(17)
            << "{\n  \"schema\": \"round54-inventory-route-result-v1\",\n"
            << "  \"state_id\": \"" << jsonEscape(args.state_id) << "\",\n"
            << "  \"variant\": \"" << jsonEscape(closure.variant) << "\",\n"
            << "  \"closure_valid\": " << closure.valid << ",\n"
            << "  \"closure_converged\": " << closure.converged << ",\n"
            << "  \"closure_infeasible\": " << closure.infeasible << ",\n"
            << "  \"fallback_required\": " << closure.fallback_required << ",\n"
            << "  \"fallback_used\": " << fallback_used << ",\n"
            << "  \"closure_failure_reason\": \""
            << jsonEscape(closure.failure_reason) << "\",\n"
            << "  \"initial_root_lp_objective\": "
            << closure.initial_lp_objective << ",\n"
            << "  \"initial_max_inbound_violation\": "
            << (initial_separation
                ? initial_separation->mixed_inbound.raw_violation : 0.0)
            << ",\n  \"initial_inbound_subset\": "
            << subsetJson(initial_separation
                ? &initial_separation->mixed_inbound : nullptr) << ",\n"
            << "  \"initial_max_outbound_violation\": "
            << (initial_separation
                ? initial_separation->mixed_outbound.raw_violation : 0.0)
            << ",\n  \"initial_outbound_subset\": "
            << subsetJson(initial_separation
                ? &initial_separation->mixed_outbound : nullptr) << ",\n"
            << "  \"initial_max_projected_inbound_violation\": "
            << (initial_separation
                ? initial_separation->projected_inbound.raw_violation : 0.0)
            << ",\n  \"initial_projected_inbound_subset\": "
            << subsetJson(initial_separation
                ? &initial_separation->projected_inbound : nullptr) << ",\n"
            << "  \"initial_max_projected_outbound_violation\": "
            << (initial_separation
                ? initial_separation->projected_outbound.raw_violation : 0.0)
            << ",\n  \"initial_projected_outbound_subset\": "
            << subsetJson(initial_separation
                ? &initial_separation->projected_outbound : nullptr) << ",\n"
            << "  \"final_root_closure_objective\": "
            << closure.final_lp_objective << ",\n"
            << "  \"root_bound_gain\": "
            << closure.final_lp_objective - closure.initial_lp_objective << ",\n"
            << "  \"closure_rounds\": " << closure.rounds.size() << ",\n"
            << "  \"cuts_generated\": " << closure.cuts_generated << ",\n"
            << "  \"cuts_added\": " << closure.cuts_added << ",\n"
            << "  \"duplicate_rejections\": "
            << closure.duplicate_rejections << ",\n"
            << "  \"dominated_rejections\": "
            << closure.dominated_rejections << ",\n"
            << "  \"nonviolated_rejections\": "
            << closure.nonviolated_rejections << ",\n"
            << "  \"closure_work\": " << closure.cumulative_lp_work << ",\n"
            << "  \"closure_solver_time_seconds\": "
            << closure.cumulative_lp_runtime_seconds << ",\n"
            << "  \"closure_simplex_iterations\": "
            << closure.cumulative_lp_simplex_iterations << ",\n"
            << "  \"terminal_attempted\": " << terminal.attempted << ",\n"
            << "  \"terminal_engineering_gate\": "
            << terminal_engineering << ",\n"
            << "  \"certificate\": " << exact << ",\n"
            << "  \"false_certificate\": false,\n"
            << "  \"terminal_native_status\": \""
            << jsonEscape(terminal.native_status) << "\",\n"
            << "  \"lower_bound\": " << lower_bound << ",\n"
            << "  \"verified_upper_bound_available\": "
            << verified_upper_bound_available << ",\n"
            << "  \"verified_upper_bound\": "
            << verified_upper_bound << ",\n"
            << "  \"final_gap\": " << final_gap << ",\n"
            << "  \"terminal_work\": " << terminal.work << ",\n"
            << "  \"total_work\": "
            << closure.cumulative_lp_work + terminal.work << ",\n"
            << "  \"terminal_solver_time_seconds\": "
            << terminal.solver_runtime_seconds << ",\n"
            << "  \"terminal_nodes\": " << terminal.nodes << ",\n"
            << "  \"terminal_simplex_iterations\": "
            << terminal.simplex_iterations << ",\n"
            << "  \"terminal_peak_memory_gb\": "
            << terminal.memory_gb << ",\n"
            << "  \"first_incumbent_work\": "
            << terminal.first_incumbent_work << ",\n"
            << "  \"first_incumbent_time_seconds\": "
            << terminal.first_incumbent_runtime_seconds << ",\n"
            << "  \"terminal_root_relaxation_bound_available\": "
            << terminal.root_relaxation_bound_available << ",\n"
            << "  \"terminal_root_relaxation_bound\": "
            << terminal.root_relaxation_bound << ",\n"
            << "  \"terminal_final_root_cut_bound_available\": "
            << terminal.final_root_cut_bound_available << ",\n"
            << "  \"terminal_final_root_cut_bound\": "
            << terminal.final_root_cut_bound << ",\n"
            << "  \"terminal_root_work\": " << terminal.root_work << ",\n"
            << "  \"terminal_root_time_seconds\": "
            << terminal.root_runtime_seconds << ",\n"
            << "  \"terminal_callback_active\": "
            << terminal.tailored_cut_callback_active << ",\n"
            << "  \"terminal_precrush_requested\": "
            << terminal.gurobi_precrush_requested << ",\n"
            << "  \"terminal_branching_status\": \""
            << jsonEscape(terminal.branch_priority_assignment_status) << "\",\n"
            << "  \"terminal_rows_added\": "
            << terminal.additional_linear_rows_added << ",\n"
            << "  \"process_time_seconds\": " << process_seconds << ",\n"
            << "  \"process_cap_seconds\": " << args.process_cap_seconds << ",\n"
            << "  \"cap_respected\": "
            << (process_seconds <= args.process_cap_seconds + 0.05) << ",\n"
            << "  \"model_sha256\": \"" << artifact.sha256 << "\",\n"
            << "  \"model_rows\": " << artifact.rows << ",\n"
            << "  \"model_columns\": " << artifact.columns << ",\n"
            << "  \"model_nonzeros\": " << artifact.nonzeros << ",\n"
            << "  \"subset_duration_rows\": "
            << artifact.round51_subset_duration_rows << ",\n"
            << "  \"backend_optimize_count\": " << stats.optimize_count << "\n}\n";
        std::ofstream completion(args.artifact_dir / "completion_marker.json");
        completion << "{\n  \"completed\": true,\n  \"closure_valid\": "
                   << closure.valid << ",\n  \"candidate_evidence_valid\": "
                   << (closure.valid && !closure.fallback_required &&
                       terminal_engineering)
                   << ",\n  \"process_seconds\": " << std::setprecision(17)
                   << process_seconds << "\n}\n";
        return closure.valid && terminal_engineering ? 0 : 5;
    } catch (const std::exception& ex) {
        std::cerr << "Round54InventoryRouteExperiment: " << ex.what() << '\n';
        return 2;
    }
}
