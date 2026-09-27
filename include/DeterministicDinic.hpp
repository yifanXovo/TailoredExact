#pragma once
#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <stdexcept>
#include <vector>
namespace ebrp {
constexpr double kResidualTolerance = 1e-12;

struct FlowEdge {
    int to = 0;
    int reverse = 0;
    double capacity = 0.0;
};

class DeterministicDinic {
public:
    explicit DeterministicDinic(int nodes)
        : graph_(static_cast<std::size_t>(nodes)),
          level_(static_cast<std::size_t>(nodes)),
          next_(static_cast<std::size_t>(nodes)) {}

    void addArc(int from, int to, double capacity) {
        if (!(capacity >= 0.0) || !std::isfinite(capacity)) {
            throw std::runtime_error("invalid_mincut_capacity");
        }
        FlowEdge forward{to,
            static_cast<int>(graph_[static_cast<std::size_t>(to)].size()),
            capacity};
        FlowEdge reverse{from,
            static_cast<int>(graph_[static_cast<std::size_t>(from)].size()),
            0.0};
        graph_[static_cast<std::size_t>(from)].push_back(forward);
        graph_[static_cast<std::size_t>(to)].push_back(reverse);
    }

    double maxFlow(int source, int sink) {
        double total = 0.0;
        while (buildLevels(source, sink)) {
            std::fill(next_.begin(), next_.end(), 0);
            while (true) {
                const double sent = send(source, sink,
                    std::numeric_limits<double>::max() / 16.0);
                if (sent <= kResidualTolerance) break;
                total += sent;
            }
        }
        return total;
    }

    std::vector<bool> sourceSide(int source) const {
        std::vector<bool> seen(graph_.size(), false);
        std::queue<int> queue;
        seen[static_cast<std::size_t>(source)] = true;
        queue.push(source);
        while (!queue.empty()) {
            const int node = queue.front();
            queue.pop();
            for (const FlowEdge& edge : graph_[static_cast<std::size_t>(node)]) {
                if (edge.capacity <= kResidualTolerance ||
                    seen[static_cast<std::size_t>(edge.to)]) {
                    continue;
                }
                seen[static_cast<std::size_t>(edge.to)] = true;
                queue.push(edge.to);
            }
        }
        return seen;
    }

private:
    bool buildLevels(int source, int sink) {
        std::fill(level_.begin(), level_.end(), -1);
        std::queue<int> queue;
        level_[static_cast<std::size_t>(source)] = 0;
        queue.push(source);
        while (!queue.empty()) {
            const int node = queue.front();
            queue.pop();
            for (const FlowEdge& edge : graph_[static_cast<std::size_t>(node)]) {
                if (edge.capacity <= kResidualTolerance ||
                    level_[static_cast<std::size_t>(edge.to)] >= 0) {
                    continue;
                }
                level_[static_cast<std::size_t>(edge.to)] =
                    level_[static_cast<std::size_t>(node)] + 1;
                queue.push(edge.to);
            }
        }
        return level_[static_cast<std::size_t>(sink)] >= 0;
    }

    double send(int node, int sink, double available) {
        if (node == sink) return available;
        int& offset = next_[static_cast<std::size_t>(node)];
        while (offset < static_cast<int>(
                graph_[static_cast<std::size_t>(node)].size())) {
            FlowEdge& edge = graph_[static_cast<std::size_t>(node)][
                static_cast<std::size_t>(offset)];
            if (edge.capacity > kResidualTolerance &&
                level_[static_cast<std::size_t>(edge.to)] ==
                    level_[static_cast<std::size_t>(node)] + 1) {
                const double sent = send(
                    edge.to, sink, std::min(available, edge.capacity));
                if (sent > kResidualTolerance) {
                    edge.capacity -= sent;
                    graph_[static_cast<std::size_t>(edge.to)][
                        static_cast<std::size_t>(edge.reverse)].capacity += sent;
                    return sent;
                }
            }
            ++offset;
        }
        return 0.0;
    }

    std::vector<std::vector<FlowEdge>> graph_;
    std::vector<int> level_;
    std::vector<int> next_;
};

}
