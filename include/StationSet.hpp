#pragma once

#include <algorithm>
#include <cstdint>
#include <functional>
#include <sstream>
#include <string>
#include <vector>

namespace ebrp {

class StationSet {
public:
    StationSet() = default;
    explicit StationSet(int station_count) { reset(station_count); }

    void reset(int station_count) {
        station_count_ = std::max(0, station_count);
        words_.assign(static_cast<std::size_t>((station_count_ + 63) / 64), 0ULL);
    }

    static StationSet fromMask(int station_count, int mask) {
        StationSet set(station_count);
        for (int station = 1; station <= station_count; ++station) {
            if (station <= 31 && (mask & (1 << (station - 1)))) set.add(station);
        }
        return set;
    }

    bool empty() const {
        for (std::uint64_t word : words_) {
            if (word != 0ULL) return false;
        }
        return true;
    }

    int stationCount() const { return station_count_; }

    bool contains(int station) const {
        if (station < 1 || station > station_count_) return false;
        const int bit = station - 1;
        return (words_[static_cast<std::size_t>(bit / 64)] &
                (1ULL << (bit % 64))) != 0ULL;
    }

    void add(int station) {
        if (station < 1 || station > station_count_) return;
        const int bit = station - 1;
        words_[static_cast<std::size_t>(bit / 64)] |= (1ULL << (bit % 64));
    }

    void remove(int station) {
        if (station < 1 || station > station_count_) return;
        const int bit = station - 1;
        words_[static_cast<std::size_t>(bit / 64)] &= ~(1ULL << (bit % 64));
    }

    bool intersects(const StationSet& other) const {
        const std::size_t n = std::min(words_.size(), other.words_.size());
        for (std::size_t i = 0; i < n; ++i) {
            if ((words_[i] & other.words_[i]) != 0ULL) return true;
        }
        return false;
    }

    bool isSubsetOf(const StationSet& other) const {
        const std::size_t n = std::max(words_.size(), other.words_.size());
        for (std::size_t i = 0; i < n; ++i) {
            const std::uint64_t lhs = i < words_.size() ? words_[i] : 0ULL;
            const std::uint64_t rhs = i < other.words_.size() ? other.words_[i] : 0ULL;
            if ((lhs & ~rhs) != 0ULL) return false;
        }
        return true;
    }

    bool isSupersetOf(const StationSet& other) const {
        return other.isSubsetOf(*this);
    }

    int popcount() const {
        int count = 0;
        for (std::uint64_t word : words_) {
#if defined(__GNUG__) || defined(__clang__)
            count += __builtin_popcountll(word);
#else
            while (word != 0ULL) {
                word &= (word - 1ULL);
                ++count;
            }
#endif
        }
        return count;
    }

    std::vector<int> stations() const {
        std::vector<int> out;
        for (int station = 1; station <= station_count_; ++station) {
            if (contains(station)) out.push_back(station);
        }
        return out;
    }

    std::string toKey() const {
        std::ostringstream out;
        bool first = true;
        for (int station = 1; station <= station_count_; ++station) {
            if (!contains(station)) continue;
            if (!first) out << ".";
            out << station;
            first = false;
        }
        return first ? "-" : out.str();
    }

    std::size_t hash() const {
        std::size_t seed = std::hash<int>{}(station_count_);
        for (std::uint64_t word : words_) {
            seed ^= std::hash<std::uint64_t>{}(word) + 0x9e3779b97f4a7c15ULL +
                (seed << 6) + (seed >> 2);
        }
        return seed;
    }

    bool operator==(const StationSet& other) const {
        return station_count_ == other.station_count_ && words_ == other.words_;
    }

    bool operator!=(const StationSet& other) const { return !(*this == other); }

private:
    int station_count_ = 0;
    std::vector<std::uint64_t> words_;
};

inline std::string stationSetBackendName(int station_count) {
    return station_count <= 63 ? "uint64" : "dynamic";
}

} // namespace ebrp
