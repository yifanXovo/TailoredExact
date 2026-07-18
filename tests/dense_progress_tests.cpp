#include "DenseProgress.hpp"

#include <cmath>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace {

void require(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}

ebrp::DenseProgressConfig config() {
    ebrp::DenseProgressConfig cfg;
    cfg.enabled = true;
    cfg.run_id = "mock";
    cfg.algorithm = "S0";
    cfg.flow_variant = "round20-current";
    cfg.executable_sha256 = std::string(64, 'a');
    cfg.model_rows = 10;
    cfg.model_columns = 20;
    cfg.model_nonzeros = 30;
    cfg.verified_upper_bound_available = true;
    cfg.verified_upper_bound = 1.0;
    cfg.material_node_delta = 100;
    return cfg;
}

ebrp::DenseProgressSnapshot snapshot(double time, double bound,
                                     long long nodes = 0) {
    ebrp::DenseProgressSnapshot point;
    point.observation_time_seconds = time;
    point.callback_invocation_sequence =
        static_cast<long long>(std::llround(time * 10.0)) + 1;
    point.phase = nodes == 0 ? "root_cuts" : "ordinary_tree";
    point.native_best_bound_available = true;
    point.native_best_bound = bound;
    point.native_incumbent_available = true;
    point.native_incumbent = 1.0;
    point.verified_upper_bound_available = true;
    point.verified_upper_bound = 1.0;
    point.processed_nodes_available = true;
    point.processed_nodes = nodes;
    point.open_nodes_available = true;
    point.open_nodes = nodes / 2;
    point.simplex_iterations_available = true;
    point.simplex_iterations = nodes * 2;
    return point;
}

void testReadOnlyContract() {
    const auto policy = ebrp::denseProgressReadOnlyPolicy();
    require(!policy.may_add_rows && !policy.may_branch &&
                !policy.may_reject_candidate && !policy.may_abort &&
                !policy.may_change_parameters &&
                !policy.may_call_auxiliary_optimizer,
            "dense callback policy is not read-only");
}

void testRequiredHeartbeatCadence() {
    require(ebrp::denseHeartbeatCadenceSeconds(0) == 1.0, "0-60 cadence");
    require(ebrp::denseHeartbeatCadenceSeconds(60) == 5.0, "60-300 cadence");
    require(ebrp::denseHeartbeatCadenceSeconds(300) == 10.0,
            "300-900 cadence");
    require(ebrp::denseHeartbeatCadenceSeconds(900) == 30.0,
            "post-900 cadence");
}

void testHeartbeatMockRetainsFreshObservations() {
    ebrp::DenseProgressRecorder recorder(config());
    for (int tick = 0; tick <= 240; ++tick) {
        recorder.observe(snapshot(tick * 0.25, 0.5));
        recorder.noteCallbackInvocation(1e-6);
    }
    const auto& events = recorder.events();
    require(events.size() >= 60, "one-second heartbeat too sparse");
    for (std::size_t i = 1; i < events.size(); ++i) {
        require(events[i].observation_time_seconds -
                    events[i - 1].observation_time_seconds <= 1.000001,
                "heartbeat gap exceeded one second");
    }
}

void testMaterialChangesAreRetained() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.0, 0.5, 0));
    recorder.observe(snapshot(0.1, 0.51, 1));
    require(recorder.events().size() == 2,
            "bound change not retained immediately");
    require(recorder.events().back().retention_trigger.find(
                "best_bound_change") != std::string::npos,
            "bound-change trigger hidden");
}

void testTimestampsBecomeStrict() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.0, 0.5));
    recorder.observe(snapshot(0.0, 0.6));
    require(recorder.events()[1].observation_time_seconds >
                recorder.events()[0].observation_time_seconds,
            "duplicate callback timestamp retained");
}

void testFinalRecordAlwaysAppendedOnce() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.0, 0.5));
    require(recorder.appendSolverFinal(snapshot(1.0, 0.7, 10)),
            "solver-final missing");
    require(!recorder.appendSolverFinal(snapshot(1.1, 0.7, 10)),
            "duplicate solver-final appended");
    require(recorder.events().back().retention_trigger == "solver_final",
            "solver-final trigger");
}

void testCheckpointGridExact() {
    const auto grid = ebrp::canonicalDenseCheckpointGrid(901.0);
    require(grid.size() == 18, "canonical grid size through 900");
    require(grid.front() == 1.0 && grid.back() == 900.0,
            "canonical grid endpoints");
}

void testCheckpointNeverUsesFutureEvent() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.5, 0.5));
    recorder.observe(snapshot(2.1, 0.8));
    const auto rows = ebrp::extractDenseProgressCheckpoints(
        recorder.events(), 5.0);
    require(rows[1].checkpoint_seconds == 2.0, "checkpoint index");
    require(rows[1].event.native_best_bound == 0.5,
            "future 2.1-second event used at 2 seconds");
}

void testObservationAgeAndStaleness() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.1, 0.5));
    const auto rows = ebrp::extractDenseProgressCheckpoints(
        recorder.events(), 5.0);
    require(rows.back().observation_age_seconds > 4.8,
            "observation age missing");
    require(rows.back().freshness == "stale", "stale row marked fresh");
}

void testMissingObservationNotFabricated() {
    const auto rows = ebrp::extractDenseProgressCheckpoints({}, 5.0);
    require(!rows.empty() && !rows.front().observation_available,
            "missing checkpoint fabricated");
    require(rows.front().freshness == "not_observed",
            "missing checkpoint label");
}

void testIntegrityAcceptsMonotoneTrajectory() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.0, 0.5, 0));
    recorder.observe(snapshot(1.0, 0.6, 100));
    recorder.appendSolverFinal(snapshot(2.0, 0.7, 200));
    const auto audit = ebrp::auditDenseProgressEvents(recorder.events());
    require(audit.timestamps_strictly_increasing &&
                audit.lower_bound_nondecreasing &&
                audit.incumbent_nonincreasing &&
                audit.node_counters_consistent &&
                audit.final_record_present,
            "valid dense trajectory failed integrity audit");
}

void testIntegrityReportsBoundRegressionWithoutInvalidatingEvidence() {
    ebrp::DenseProgressRecorder recorder(config());
    recorder.observe(snapshot(0.0, 0.7, 0));
    recorder.observe(snapshot(1.0, 0.6, 100));
    recorder.appendSolverFinal(snapshot(2.0, 0.6, 200));
    const auto audit = ebrp::auditDenseProgressEvents(recorder.events());
    require(!audit.lower_bound_nondecreasing,
            "lower-bound regression hidden");
    require(audit.native_monotonicity_is_diagnostic_only &&
                audit.lower_bound_negative_step_count == 1 &&
                audit.error_count == 0,
            "native bound diagnostic incorrectly invalidated evidence");
}

void testBufferBoundAndCounters() {
    auto cfg = config();
    cfg.maximum_retained_records = 2;
    ebrp::DenseProgressRecorder recorder(cfg);
    recorder.observe(snapshot(0.0, 0.5));
    recorder.observe(snapshot(0.1, 0.6));
    recorder.observe(snapshot(0.2, 0.7));
    recorder.noteCallbackInvocation(0.001);
    require(recorder.events().size() == 2, "buffer bound exceeded");
    require(recorder.stats().dropped_record_count == 1,
            "dropped record counter");
    require(recorder.stats().callback_invocation_count == 1,
            "callback invocation counter");
}

void testBufferedFlushPreservesRetainedEvents() {
    auto cfg = config();
    cfg.raw_event_path = std::filesystem::temp_directory_path() /
        "exact_ebrp_round22_dense_progress_test.csv";
    ebrp::DenseProgressRecorder recorder(cfg);
    recorder.observe(snapshot(0.0, 0.5));
    recorder.observe(snapshot(1.0, 0.6, 100));
    recorder.appendSolverFinal(snapshot(2.0, 0.7, 200));
    require(recorder.flush(), "buffered flush failed");
    std::ifstream input(cfg.raw_event_path);
    std::string line;
    long long lines = 0;
    while (std::getline(input, line)) ++lines;
    require(lines == static_cast<long long>(recorder.events().size()) + 1,
            "flush did not preserve every retained event");
    input.close();
    std::filesystem::remove(cfg.raw_event_path);
}

void testAlgorithmNeutralSchema() {
    auto plain_cfg = config();
    plain_cfg.algorithm = "plain";
    plain_cfg.flow_variant = "plain";
    ebrp::DenseProgressRecorder plain(plain_cfg);
    ebrp::DenseProgressRecorder tailored(config());
    plain.observe(snapshot(0.0, 0.5));
    tailored.observe(snapshot(0.0, 0.5));
    require(plain.events().front().phase == tailored.events().front().phase,
            "plain and Tailored recorder semantics diverged");
}

} // namespace

int main() {
    try {
        testReadOnlyContract();
        testRequiredHeartbeatCadence();
        testHeartbeatMockRetainsFreshObservations();
        testMaterialChangesAreRetained();
        testTimestampsBecomeStrict();
        testFinalRecordAlwaysAppendedOnce();
        testCheckpointGridExact();
        testCheckpointNeverUsesFutureEvent();
        testObservationAgeAndStaleness();
        testMissingObservationNotFabricated();
        testIntegrityAcceptsMonotoneTrajectory();
        testIntegrityReportsBoundRegressionWithoutInvalidatingEvidence();
        testBufferBoundAndCounters();
        testBufferedFlushPreservesRetainedEvents();
        testAlgorithmNeutralSchema();
        std::cout << "DenseProgressTests: 15 groups passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "DenseProgressTests failure: " << error.what() << '\n';
        return 1;
    }
}
