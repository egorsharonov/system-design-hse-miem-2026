# System Design — HSE MIEM Course Fork (2026)

Historical educational reference fork of [Nikolay Savelev's course repository](https://github.com/nikolaysavelev/system-design-hse-miem-2026).

## Context

Course: System Design of Modern Applications, HSE MIEM, Moscow, 2026. Course author: Nikolay Savelev. The checked-out history has six commits attributed to the instructor and no commits unique to this fork relative to the fetched upstream branch (one upstream commit ahead at audit time).

## What is here

- Numbered directories: course materials.
- `HWs/`: homework materials.
- `code/`: demonstrations including cache, load balancing and PostgreSQL high availability.

## Technologies

The teaching examples include Python, Docker Compose and PostgreSQL; the vendored Patroni tree contains its own dependencies, tests and license. Those are upstream teaching and third-party artifacts, not evidence of my implementation experience.

## Attribution and license

Course content belongs to its respective authors. Preserve the license in `code/postgres-ha/patroni-master/LICENSE`. No top-level license was found; that nested license does not automatically license the entire course repository.

## Notes

This fork is retained as a learning reference, not a selected portfolio implementation. Local-demo credential fields and networking examples require review before running or redistributing them. No demos or tests were executed in this pass.
