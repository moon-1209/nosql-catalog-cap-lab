# Top Partitions Report

Data origin: **synthetic** 
run_id: `20261120054801_0bdd8fba` (log/manifest consistency: ok)
status mode: ok

## Schema A

- partitions: 2
- total requests: 200 (of which 1 failed)
- mean / median / std per partition: 100.0 / 100.0 / 84.9
- max partition load: 160 (80.0% of all traffic)
- max/mean ratio: 1.60

Top 10 partitions:

| partition | reads | writes | total | share |
|---|---|---|---|---|
| gaming | 80 | 80 | 160 | 80.00% |
| pets | 20 | 20 | 40 | 20.00% |

## Schema B

- partitions: 32
- total requests: 200 (of which 1 failed)
- mean / median / std per partition: 6.2 / 4.5 / 4.1
- max partition load: 12 (6.0% of all traffic)
- max/mean ratio: 1.92

Top 10 partitions:

| partition | reads | writes | total | share |
|---|---|---|---|---|
| gaming/b2 | 7 | 5 | 12 | 6.00% |
| gaming/b6 | 6 | 6 | 12 | 6.00% |
| gaming/b7 | 7 | 5 | 12 | 6.00% |
| gaming/b1 | 6 | 6 | 12 | 6.00% |
| gaming/b0 | 6 | 5 | 11 | 5.50% |
| gaming/b3 | 7 | 4 | 11 | 5.50% |
| gaming/b4 | 7 | 4 | 11 | 5.50% |
| gaming/b5 | 6 | 5 | 11 | 5.50% |
| gaming/b13 | 4 | 7 | 11 | 5.50% |
| gaming/b11 | 4 | 6 | 10 | 5.00% |
