#include "Parser.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <regex>
#include <sstream>
#include <stdexcept>

namespace ebrp {
namespace {

constexpr double kReadDistanceSpeed = 1.5;

std::string readAll(const std::filesystem::path& path) {
    std::ifstream in(path);
    if (!in) {
        throw std::runtime_error("Cannot open instance file: " + path.string());
    }
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

std::vector<double> extractNumbers(const std::string& text) {
    static const std::regex number_re(R"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)");
    std::vector<double> values;
    for (auto it = std::sregex_iterator(text.begin(), text.end(), number_re);
         it != std::sregex_iterator(); ++it) {
        values.push_back(std::stod(it->str()));
    }
    return values;
}

std::string firstLine(const std::string& text) {
    std::istringstream in(text);
    std::string line;
    std::getline(in, line);
    return line;
}

std::string namedBracketPayload(const std::string& text, const std::string& name) {
    const std::string pat = name + R"(\s*=\s*\[([\s\S]*?)\])";
    const std::regex re(pat);
    std::smatch m;
    if (!std::regex_search(text, m, re)) return {};
    return m[1].str();
}

std::vector<int> namedIntVector(const std::string& text, const std::string& name) {
    std::vector<int> out;
    for (double x : extractNumbers(namedBracketPayload(text, name))) {
        out.push_back(static_cast<int>(std::llround(x)));
    }
    return out;
}

std::vector<double> namedDoubleVector(const std::string& text, const std::string& name) {
    return extractNumbers(namedBracketPayload(text, name));
}

std::vector<std::pair<double, double>> parsePoints(const std::string& text) {
    std::string payload = namedBracketPayload(text, "points");
    std::vector<double> nums = extractNumbers(payload);
    std::vector<std::pair<double, double>> points;
    for (std::size_t i = 0; i + 1 < nums.size(); i += 2) {
        points.push_back({nums[i], nums[i + 1]});
    }
    return points;
}

std::vector<std::vector<double>> parseDistanceMatrix(const std::string& text) {
    std::vector<std::vector<double>> matrix;
    std::istringstream in(text);
    std::string line;
    bool in_matrix = false;
    while (std::getline(in, line)) {
        if (!in_matrix) {
            if (line.find("distances") != std::string::npos) {
                in_matrix = true;
            }
            continue;
        }
        if (line.find(']') != std::string::npos) break;
        std::vector<double> row = extractNumbers(line);
        if (!row.empty()) matrix.push_back(std::move(row));
    }
    return matrix;
}

std::vector<std::vector<double>> distancesFromPoints(
    const std::vector<std::pair<double, double>>& points) {
    const int n = static_cast<int>(points.size());
    std::vector<std::vector<double>> dist(n, std::vector<double>(n, 0.0));
    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            if (i == j) continue;
            const double dx = points[i].first - points[j].first;
            const double dy = points[i].second - points[j].second;
            dist[i][j] = std::sqrt(dx * dx + dy * dy) / kReadDistanceSpeed;
        }
    }
    return dist;
}

void ensureVectorSize(const std::string& label, std::size_t got, std::size_t expected) {
    if (got != expected) {
        std::ostringstream msg;
        msg << "Parsed " << label << " length " << got << ", expected " << expected;
        throw std::runtime_error(msg.str());
    }
}

void downgradeLegacyWeights(std::vector<double>& weights, std::string& convention) {
    if (weights.size() <= 1) return;
    double max_w = 0.0;
    for (std::size_t i = 1; i < weights.size(); ++i) max_w = std::max(max_w, weights[i]);
    if (std::fabs(max_w - 10.0) <= 1e-6) {
        for (std::size_t i = 1; i < weights.size(); ++i) weights[i] /= 10.0;
        convention += "; legacy weights with max 10 scaled by 0.1 to match Hybrid GA parser";
    }
}

} // namespace

Instance parseInstanceFile(const std::filesystem::path& path,
                           double total_time_limit,
                           double pickup_time,
                           double drop_time) {
    const std::string text = readAll(path);
    Instance instance;
    instance.path = std::filesystem::absolute(path).string();
    instance.name = path.filename().string();
    instance.total_time_limit = total_time_limit;
    instance.pickup_time = pickup_time;
    instance.drop_time = drop_time;

    std::string line = firstLine(text);
    std::vector<double> head = extractNumbers(line);
    if (head.size() < 2) {
        throw std::runtime_error("Invalid first line in instance: " + path.string());
    }
    instance.V = static_cast<int>(std::llround(head[0]));
    instance.M = static_cast<int>(std::llround(head[1]));

    const std::size_t q_open = line.find('[');
    const std::size_t q_close = line.find(']', q_open);
    if (q_open == std::string::npos || q_close == std::string::npos) {
        throw std::runtime_error("Missing vehicle capacity list in: " + path.string());
    }
    for (double q : extractNumbers(line.substr(q_open, q_close - q_open + 1))) {
        instance.Q.push_back(static_cast<int>(std::llround(q)));
    }
    ensureVectorSize("Q", instance.Q.size(), static_cast<std::size_t>(instance.M));

    instance.capacity = namedIntVector(text, "capacities");
    instance.initial = namedIntVector(text, "initial");
    instance.target = namedIntVector(text, "target");
    instance.weights = namedDoubleVector(text, "weights");
    instance.min_ratio = namedDoubleVector(text, "min_ratio");

    const std::size_t n_nodes = static_cast<std::size_t>(instance.V + 1);
    ensureVectorSize("capacities", instance.capacity.size(), n_nodes);
    ensureVectorSize("initial", instance.initial.size(), n_nodes);
    ensureVectorSize("target", instance.target.size(), n_nodes);
    if (instance.weights.empty()) {
        instance.weights.assign(n_nodes, 1.0);
        instance.weights[0] = 0.0;
    }
    ensureVectorSize("weights", instance.weights.size(), n_nodes);
    if (instance.min_ratio.empty()) instance.min_ratio.assign(n_nodes, 0.0);
    ensureVectorSize("min_ratio", instance.min_ratio.size(), n_nodes);

    instance.distance_convention = "parsed Hybrid GA text format";
    downgradeLegacyWeights(instance.weights, instance.distance_convention);

    instance.points = parsePoints(text);
    if (instance.points.size() == n_nodes) {
        instance.dist = distancesFromPoints(instance.points);
        instance.distance_convention += "; distances rebuilt from points at speed factor 1.5";
    } else {
        instance.dist = parseDistanceMatrix(text);
        instance.distance_convention += "; distances read from serialized matrix";
    }
    ensureVectorSize("distance rows", instance.dist.size(), n_nodes);
    for (const auto& row : instance.dist) ensureVectorSize("distance columns", row.size(), n_nodes);

    for (int i = 1; i <= instance.V; ++i) {
        if (instance.target[i] <= 0) {
            throw std::runtime_error("Station target must be positive at station " + std::to_string(i));
        }
    }

    return instance;
}

std::vector<std::filesystem::path> collectInputFiles(const std::filesystem::path& input) {
    std::vector<std::filesystem::path> files;
    if (std::filesystem::is_regular_file(input)) {
        files.push_back(input);
    } else if (std::filesystem::is_directory(input)) {
        for (const auto& entry : std::filesystem::directory_iterator(input)) {
            if (entry.is_regular_file() && entry.path().extension() == ".txt") {
                files.push_back(entry.path());
            }
        }
        std::sort(files.begin(), files.end());
    } else {
        throw std::runtime_error("Input path is neither a file nor a directory: " + input.string());
    }
    if (files.empty()) throw std::runtime_error("No .txt instance files found in: " + input.string());
    return files;
}

} // namespace ebrp
