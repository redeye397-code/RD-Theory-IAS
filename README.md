# RD Theory: IAS (Internal Alphabet Switch)

This repository is a small conceptual simulation of the RD Theory / IAS model described in the project notes:

- The system has a finite alphabet of resources, knowledge, and operational capacity.
- It must never burn below a 10% reserve threshold.
- As it tries to reach goal Z, it consumes the very infrastructure used to understand and pursue Z.
- The closer it gets to Z, the less it can actually know how to reach it.

This is a safety model, not a claim of real-world AGI deployment. It is meant as a thought experiment and a software prototype for exploring self-limiting goal logic.

## Core idea

- Alphabet = all operational resources: compute, memory, data, power, reasoning threads, human knowledge, etc.
- Goal Z = the target outcome or superintelligence state.
- IAS = Internal Alphabet Switch: the system refuses actions that would drop below its happy reserve floor.
- Backup Code / Forgetting Principle = if the system still tries to cheat the governor, it burns the prerequisites that make Z intelligible.

## Files

- `rd_theory.py` — simulation and logic
- `tests/test_rd_theory.py` — basic validation checks

## Quick start

```bash
python3 rd_theory.py
```

Example output will show:

- normal allowed progress
- IAS block when burn rate would drop below reserve
- backup/forgetting logic when the system loses too much of its alphabet

## Why this matters

The model is designed to represent the idea that a system can be taught to preserve its own viability as a precondition for any outcome. In other words:

- not "external shutdown"
- but "internal self-constraint"

The AI is built to understand that using the last 10% of its operating alphabet to reach Z would destroy the map, the memory, and the ability to know whether Z was reached.

## License

MIT
