# Round127 finite packaging scanner and recovery review

Final disposition: **public-option false positive independently confirmed; corrected scanner/recovery/checker source PASS; compact-receipt review of actual carrier recovery, v2 compaction and five-source carrier check PASS**. Public science-A commit/recovery and cleanup have not yet started at this closeout. The scientific experiments, numerical reports, maintained manuscript/PDF and frozen E0/E1 remain outside this administrative correction. The actual receipt inspection is documented at the end; it does not add a second ZIP/raw scan by this reviewer.

## Failure and narrowly inspected evidence

The retained `finite_carrier_pack_01` fee receipt records exit1, observed exit and **2617.5073867999017 seconds** outer time, with no nested time added. Its receipt SHA256 is `8ee8c27a285f1af1209a4e837b2956728b76a7d43682f3d3f177c548e4d26cc8`. The failure is not erased or relabeled as a complete pack. The parent's four completed stage ZIPs and failed partial support ZIP are to be retained; this reviewer has not opened or hashed those carriers.

Independent work here was confined to the known frozen `source_E0/src/main.cpp`, small scanner/recovery/checker source, compact source-manifest metadata and the closed failed-fee receipt. I did not run a build, Optimize, solver, compression, archive recovery, full raw scan, network action or cleanup. No possible credential value was printed. The two scanner candidates were reported only through offsets, lengths, hashes and redacted source context.

The inspected old main.cpp bytes have SHA256 **38aa9744ded25d494748a6dbb371db3d266b42081f173ef6f5bb723e1f758b5d**. Applying the old BAD[4] pattern to that one source gives exactly two matches:

| Source line | Byte offset | Match length | Match SHA256 |
| --- | ---: | ---: | --- |
| 109 | 7034 | 27 | `b2eeb1715c36296231973c7a8bb40b418b440d96a790badeec98c5c18fecf612` |
| 999 | 64771 | 27 | `b2eeb1715c36296231973c7a8bb40b418b440d96a790badeec98c5c18fecf612` |

Both complete matches are the suffix within the exact public CLI option `--route-mask-support-duration-pruning`. The first occurs in help text and the second in that argument's parse branch. Both preceding bytes are ASCII 0x61, inside the word “mask”. Thus these two candidates are public-option substrings, not credentials; this conclusion does not clear unrelated files or patterns.

## Scanner correction

The applied release source is SHA256 **7b0cf7b2dea9bace1147f3b4cf33ef4599011de023773f8923fa7e441d36c15c**. Its BAD[4] is now `(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{24,}`. The fixed-width negative left boundary rejects an occurrence embedded in an ASCII identifier/CLI option while retaining the existing token body and minimum length. File/line start and independent tokens after quotes, whitespace, equals and other non-identifier delimiters remain eligible. This neither removes the detector nor exempts main.cpp or a whole archive. The other credential patterns and forbidden extension policy remain present.

The bounded source comparison finds no corrected-pattern match in this known main.cpp. The recovery implementation also contains six synthetic positive-delimiter checks and one public-option negative check without printing candidate material; these belong to the later metered recovery's checked path and were not rerun by this reviewer. This is a finite false-positive repair, not a claim that a regex proves universal absence of secrets.

## Reviewed recovery source

Final reviewed `scripts/round127_pack_recovery.py` SHA256 is **8ccaba3643b19022fc2d1c606ab74cd1ae91d02b1c72a3166364912c719b8a27**. It first requires native/build idle, no completed raw manifest and the retained original exit1 receipt. It pins the known main.cpp and the two candidate hashes/locations before recording the scanner finding.

The four stage ZIP size/SHA identities are explicit source constants. Before reuse, the script checks those constants, validates the existing public piece names and every piece's exact size/SHA against the unchanged complete ZIP stream, then decompresses every ZIP member for SHA256, corrected credential scanning and the ZIP reader's complete CRC verification. It does not recreate the four stage ZIPs or their public pieces. The source constants have not been checked against carrier bytes by this reviewer; the actual execution's compact receipt is reviewed below instead.

The failed support ZIP is separately fixed at 24933358 bytes and SHA256 `49e493223aa48c15eca0e72b8895269d8fa29013a9559f87acdb7bd408689e66`. The script retains that exact object, copies it into fresh `TEMP/archives/recovery01/` with the canonical support basename, rejects duplicate/unexpected existing member names and appends only missing support paths. Expected support is qualification, already-closed fees (including the original failed pack) and original E0 source copies. Final member names must equal that set exactly. New entries are scanned and checked against authoritative files, and the entire final support ZIP is also streamed through CRC/SHA/scanner checks. The original failed partial SHA is checked again afterward. The active recovery fee and future receipts remain excluded by the already-closed-fee rule.

One source-scope suggestion was incorporated before execution: the rebuilt index now explicitly requires **90 entries, 36 training, 54 formal and 90 unique raw roots**. The original full v1 member index is rebuilt only after these carrier/index gates; the separately reviewed v2 compactor remains a later representation step. No production seal, result, experiment, model or manuscript is rewritten by the recovery source.

## Reviewed five-source carrier gate

Final reviewed `scripts/round127_source_carrier_check.py` SHA256 is **515a34a5e5c481af6bccaf9810f43f9e9477f29679efa40e7251a824ea4dce74**. It executes after v2 compaction and before removing only the five source copies from the Git index; physical originals remain in place.

The helper requires exactly one canonical support archive, its complete size/SHA, compressed and decoded member-index size/SHA, and a duplicate-free member list whose count equals both archive and index counts. It then requires a source manifest with exactly five fixed original/path pairs: CplexBaseline.cpp, GurobiBaseline.cpp, IntervalRowFactory.cpp, main.cpp and PaperExternalGiniTree.cpp under the original `src/` and `source_E0/src/` locations. For each actual ZIP member it links length/SHA to the v2 member list, source_E0_manifest, frozen E0_identity.source_bindings and current physical source copy. The earlier unconditional “five” PASS range is therefore replaced by an exact checked scope. The actual five metadata records inspected here have the expected paths; their carrier bodies have not been read by this reviewer.

## Actual compact-receipt closeout

I subsequently read only the three small result receipts, their three closed outer fee receipts and the current four small script files for SHA equality. I did not reopen a ZIP, decompress an index, enumerate or rehash raw, reread the old source bodies or rerun any check. This is independent inspection of actual success records plus their previously reviewed code paths, not a second independent scan of 519614 members.

| Actual result | Result receipt SHA256 | Closed outer fee | Exit |
| --- | --- | ---: | ---: |
| `review/packaging_recovery_receipt.json` PASS | `6b1a59d60638f0ae89f81dc8f0ceb40ec313d5426bef4cffd79705051b3a0438` | finite_carrier_recovery_01:127.74832519993652 s | 0 |
| `review/member_index_compaction.json` PASS | `4d5d1027181a98fab3258cdb62e16232313c012bd5a9a95d644961f2c819a0e9` | member_index_compaction_01:3.115792299970053 s | 0 |
| `review/source_E0_carrier_check.json` PASS | `5b18ff783ad625682aef41f3634504f0473a1043c586b8263a0e8bf477bba7ed` | source_E0_carrier_check_01:0.24371339997742325 s | 0 |

The outer fee receipt SHAs are respectively `2362b8cd997ebe611e93a12bee8be911f2b8b3f367d6cfcaa3897d13dacb8e53`, `e1894f80410a8a5d7f1598fe92bdc88283b491c1e74164661205d36881629b3b` and `4f49d292e5ae2b37f5a8a971c847d6cf39b13fd4e6504d67e6616f0e8079b230`. All record observed exit 0 and nested_seconds_added=false. The original exit 1/2617.5073867999017 s failure remains included in the recovery receipt and its five fee files are among the seven appended support entries.

The recovery result records **five archives, 519614 members and 2648964647 plaintext bytes** fully streamed through CRC/SHA and the corrected scanner, with executed recovery source SHA exactly `8ccaba3643b19022fc2d1c606ab74cd1ae91d02b1c72a3166364912c719b8a27`. Its four original stage SHA values equal the reviewed fixed constants. The reviewed success path validates their existing public pieces without rewriting them. The only seven appended support paths are the five original failed-fee files plus frozen `main.cpp` and `PaperExternalGiniTree.cpp`. The failed partial remains 24933358 bytes with SHA `49e493223aa48c15eca0e72b8895269d8fa29013a9559f87acdb7bd408689e66`. Native starts and Optimize are zero. The 90/36/54/unique-root assertions are on this source's success path; I did not separately recount the rebuilt arm index in this receipt-only closeout.

Compaction records preservation of the 133315114-byte original full manifest (SHA `2983acb10f46d93d11f6de2e5782481528b0e65786ce2efb627f1fbaf155d4fc`) and a 6508-byte compact v2 manifest (SHA **2fa8338221a9b8e46f6cbb95bfedcb1d473a33a3021bff6e7bc9538f39426993**). The five complete-list indexes retain 168998 training, 133818 main, 15296 tiny, 174369 core and 27133 support members, summing exactly 519614. Each has compressed and decoded size/SHA fields and the canonical per-archive path. The reviewed compactor's round-trip equality check is on its successful execution path; the receipt records raw_or_carrier_bytes_changed=false. I did not independently decompress these large indexes.

The five-source result uses that same compact raw-manifest SHA and support archive SHA **355090fec7bb4d9d645c224c6b2a89f156704f7dedf3cf406e4d9c52a6c12428**. It records exactly the five fixed original/path pairs and their unchanged lengths/SHA values, matching the earlier source-manifest metadata; their total is 2380264 source bytes. Its checked code links the actual ZIP member, decoded index, source_E0_manifest, frozen E0 source bindings and physical copy, and the actual receipt is PASS with originals_retained_locally=true. This supports removing only those five Git-index entries while preserving physical source copies; this review does not itself perform that index operation.

Current source hashes still equal all reviewed values: release `7b0cf7b2dea9bace1147f3b4cf33ef4599011de023773f8923fa7e441d36c15c`, recovery `8ccaba3643b19022fc2d1c606ab74cd1ae91d02b1c72a3166364912c719b8a27`, source checker `515a34a5e5c481af6bccaf9810f43f9e9477f29679efa40e7251a824ea4dce74`, and the earlier reviewed v2 compactor `8cb99c46970d83a13caae22faca68b289bee9277ba1e1c9f9f19ebf10424cbb0`. No unresolved issue was found in this bounded packaging closeout. Public availability, anonymous restoration and any later owned-duplicate cleanup still require their own actual receipts; this packaging PASS does not stand in for them.
