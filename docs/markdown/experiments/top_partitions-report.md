# Top Partitions Report

Data origin: **simulated** (simulated workload - replace with observed ScyllaDB logs for real measurements)

## Schema A

- partitions: 20
- total requests: 15,000
- mean / median / std per partition: 750.0 / 327.0 / 1197.4
- max partition load: 5,313 (35.4% of all traffic)
- max/mean ratio: 7.08

Top 10 partitions:

| partition | reads | writes | total | share |
|---|---|---|---|---|
| health | 4784 | 529 | 5313 | 35.42% |
| home-garden | 2060 | 244 | 2304 | 15.36% |
| pets | 1230 | 146 | 1376 | 9.17% |
| movies | 941 | 100 | 1041 | 6.94% |
| music | 647 | 74 | 721 | 4.81% |
| toys | 548 | 64 | 612 | 4.08% |
| automotive | 412 | 52 | 464 | 3.09% |
| grocery | 367 | 43 | 410 | 2.73% |
| fashion | 325 | 33 | 358 | 2.39% |
| electronics | 318 | 37 | 355 | 2.37% |

## Schema B

- partitions: 318
- total requests: 15,000
- mean / median / std per partition: 47.2 / 19.0 / 76.9
- max partition load: 445 (3.0% of all traffic)
- max/mean ratio: 9.43

Top 10 partitions:

| partition | reads | writes | total | share |
|---|---|---|---|---|
| health/b3 | 401 | 44 | 445 | 2.97% |
| health/b4 | 376 | 48 | 424 | 2.83% |
| health/b5 | 385 | 37 | 422 | 2.81% |
| health/b0 | 373 | 34 | 407 | 2.71% |
| health/b12 | 350 | 40 | 390 | 2.60% |
| health/b9 | 338 | 25 | 363 | 2.42% |
| health/b1 | 315 | 34 | 349 | 2.33% |
| health/b11 | 289 | 35 | 324 | 2.16% |
| health/b15 | 292 | 32 | 324 | 2.16% |
| health/b2 | 275 | 33 | 308 | 2.05% |
