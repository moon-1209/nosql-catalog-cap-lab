# Q&A - anticipated questions for the defence

**Q: Why is max/mean ratio higher for Schema B (9.43) than A (7.08)
if B is supposed to fix hot partitions?**
A: Bucketing uniformly splits each category's load by ~16, so the
*ratio* is roughly scale-invariant - but the mean collapses because many
category-bucket partitions are near-empty. The operationally meaningful
metrics - absolute max load (5,313 vs 445) and top-partition share
(35.4% vs 3.0%) - show B clearly bounding the hotspot. Max/mean is
reported for completeness, not as the decision metric.

**Q: Isn't the bucket fan-out just moving the bottleneck to the
coordinator?**
A: Partly - a category read becomes 16 range reads plus an app-side
merge. Each of those reads is small and parallelisable across nodes,
though, whereas a hot partition serialises load onto one replica set.
The latency trade-off is exactly what the cluster benchmark (pending)
must measure; we flag it, we don't claim it away.

**Q: Your stale-read numbers are simulated. What do they prove?**
A: They prove the *pipeline*: staleness is derived, not pre-labelled -
a read is stale iff `version < latest committed version at read.ts`.
On real data the module runs unchanged; only the input CSV swaps.
Simulated rates match the probabilities we injected (ONE normal ~2%,
partitioned ~30%), which validates the measurement code.

**Q: Why a moving-block bootstrap for latency but iid elsewhere?**
A: Consecutive latencies in a benchmark run are autocorrelated
(warm-up, GC, compaction), so iid resampling would understate the
interval. Blocks of 50 preserve short-range dependence. Request-level
stale flags and category shares are treated as exchangeable, so iid
there. Both are percentile-method CIs.

**Q: Can the bootstrap CI show Schema B *causes* lower load?**
A: No - and we don't claim it does. A CI describes sampling uncertainty
of the statistic on this workload. The mechanism (hash bucketing
spreads load) is argued from the key design; the numbers quantify it.

**Q: How do you know a read is stale without knowing ground truth?**
A: The log keeps WRITE commit versions; the latest version committed
before `read.ts` is the ground truth for that key at that instant.
Reads with no prior write are unverifiable and excluded from the rate
denominator - they cannot be proven fresh or stale.

**Q: Why Zipf alpha = 1.2 for category traffic?**
A: It's a mid-range assumption for e-commerce category skew (a few head
categories dominate). It's configurable in `config/seeder.yaml`; the
pipeline supports an alpha sweep to test sensitivity.

**Q: What happens to reads before the first write of a key?**
A: They are `unverifiable` - reported separately, never counted as
fresh or stale. In the sample they are ~0% of reads.

**Q: Why UUID5 product ids instead of random UUID4?**
A: UUID5(seed, index) is deterministic - identical seed + config gives
byte-identical datasets, which is what makes the whole benchmark
reproducible and the tests hermetic.

**Q: Schema B needs bucket = f(product_id). What if you change
num_buckets later?**
A: Resharding is a real migration cost: all rows must be rewritten to
new buckets. That's a documented limitation of hash bucketing; a
lab follow-up could evaluate consistent-hashing alternatives.
