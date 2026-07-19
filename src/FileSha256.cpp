#include "FileSha256.hpp"

#include <array>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <vector>

namespace ebrp {
namespace {
constexpr std::array<std::uint32_t, 64> k = {
    0x428a2f98u,0x71374491u,0xb5c0fbcfu,0xe9b5dba5u,0x3956c25bu,0x59f111f1u,0x923f82a4u,0xab1c5ed5u,
    0xd807aa98u,0x12835b01u,0x243185beu,0x550c7dc3u,0x72be5d74u,0x80deb1feu,0x9bdc06a7u,0xc19bf174u,
    0xe49b69c1u,0xefbe4786u,0x0fc19dc6u,0x240ca1ccu,0x2de92c6fu,0x4a7484aau,0x5cb0a9dcu,0x76f988dau,
    0x983e5152u,0xa831c66du,0xb00327c8u,0xbf597fc7u,0xc6e00bf3u,0xd5a79147u,0x06ca6351u,0x14292967u,
    0x27b70a85u,0x2e1b2138u,0x4d2c6dfcu,0x53380d13u,0x650a7354u,0x766a0abbu,0x81c2c92eu,0x92722c85u,
    0xa2bfe8a1u,0xa81a664bu,0xc24b8b70u,0xc76c51a3u,0xd192e819u,0xd6990624u,0xf40e3585u,0x106aa070u,
    0x19a4c116u,0x1e376c08u,0x2748774cu,0x34b0bcb5u,0x391c0cb3u,0x4ed8aa4au,0x5b9cca4fu,0x682e6ff3u,
    0x748f82eeu,0x78a5636fu,0x84c87814u,0x8cc70208u,0x90befffau,0xa4506cebu,0xbef9a3f7u,0xc67178f2u
};
std::uint32_t rr(std::uint32_t v, unsigned n) {
    return (v >> n) | (v << (32u - n));
}
} // namespace

std::string fileSha256(const std::filesystem::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return {};
    std::vector<std::uint8_t> bytes;
    std::array<char, 65536> buffer{};
    while (in) {
        in.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
        for (std::streamsize i = 0; i < in.gcount(); ++i) {
            bytes.push_back(static_cast<std::uint8_t>(buffer[static_cast<std::size_t>(i)]));
        }
    }
    const std::uint64_t bits = static_cast<std::uint64_t>(bytes.size()) * 8u;
    bytes.push_back(0x80u);
    while (bytes.size() % 64u != 56u) bytes.push_back(0u);
    for (int shift = 56; shift >= 0; shift -= 8) {
        bytes.push_back(static_cast<std::uint8_t>(bits >> shift));
    }
    std::array<std::uint32_t, 8> h = {
        0x6a09e667u,0xbb67ae85u,0x3c6ef372u,0xa54ff53au,
        0x510e527fu,0x9b05688cu,0x1f83d9abu,0x5be0cd19u
    };
    for (std::size_t off = 0; off < bytes.size(); off += 64u) {
        std::array<std::uint32_t, 64> w{};
        for (std::size_t i = 0; i < 16; ++i) {
            const std::size_t p = off + 4u * i;
            w[i] = (static_cast<std::uint32_t>(bytes[p]) << 24u) |
                   (static_cast<std::uint32_t>(bytes[p+1]) << 16u) |
                   (static_cast<std::uint32_t>(bytes[p+2]) << 8u) |
                   static_cast<std::uint32_t>(bytes[p+3]);
        }
        for (std::size_t i = 16; i < 64; ++i) {
            const auto s0 = rr(w[i-15],7)^rr(w[i-15],18)^(w[i-15]>>3u);
            const auto s1 = rr(w[i-2],17)^rr(w[i-2],19)^(w[i-2]>>10u);
            w[i] = w[i-16] + s0 + w[i-7] + s1;
        }
        std::uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],z=h[7];
        for (std::size_t i = 0; i < 64; ++i) {
            const auto s1=rr(e,6)^rr(e,11)^rr(e,25);
            const auto ch=(e&f)^((~e)&g);
            const auto t1=z+s1+ch+k[i]+w[i];
            const auto s0=rr(a,2)^rr(a,13)^rr(a,22);
            const auto maj=(a&b)^(a&c)^(b&c);
            const auto t2=s0+maj;
            z=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
        }
        h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=z;
    }
    std::ostringstream out;
    out << std::hex << std::setfill('0');
    for (auto word : h) out << std::setw(8) << word;
    return out.str();
}
} // namespace ebrp
