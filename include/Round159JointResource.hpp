#pragma once
#include <string>

// Standalone, opt-in research interface. No proof-ledger or incumbent mutation.
// RN is the unchanged, qualified original-J R153/R157 model exported offline.
// Newly constructed service/resource/neighborhood rows and completion are C++.
namespace round159 {
int run(const std::string& mode, const std::string& data,
        const std::string& rn, const std::string& out,
        const std::string& start = "");
}
