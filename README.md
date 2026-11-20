# Low-Power Task Scheduling for Heterogeneous Multi-Core Architectures

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/design-SOLID%20%26%20Design%20Patterns-green.svg)](#software-architecture--solid-design)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-35%20passed-brightgreen.svg)](#running-tests)

An open-source Python framework for energy-aware task scheduling on heterogeneous multiprocessor systems-on-chip (MPSoC) featuring Dynamic Voltage and Frequency Scaling (DVFS), shared communication bus arbitration, and Genetic Algorithm optimization.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Physical Energy & Power Modeling](#physical-energy--power-modeling)
- [Software Architecture & SOLID Design](#software-architecture--solid-design)
- [Flow Bug Fixes & Enhancements](#flow-bug-fixes--enhancements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Code Examples](#code-examples)
- [Project Directory Structure](#project-directory-structure)
- [Running Tests](#running-tests)
- [Contributing & License](#license)

---

## Overview

In modern embedded and high-performance multi-core processors, energy dissipation is a first-order design constraint. This framework provides an end-to-end simulation and optimization suite for scheduling directed task graphs onto heterogeneous processing elements (PEs) equipped with discrete DVFS operating points.

The optimization engine employs an evolutionary Genetic Algorithm to simultaneously search the combinatorial space of:
1. **Task-to-Processor Spatial Mapping** (which core executes which task)
2. **DVFS Frequency/Voltage Scaling** (which energy-performance point is selected)
3. **Shared Interconnect Arbitration** (serializing cross-core communications)

---

## Key Features

- **Heterogeneous Processor Modeling**: Define custom processing elements with discrete voltage-frequency pairs $(f, V)$.
- **CMOS Power Formulations**: Computes dynamic energy, voltage transition penalties, idle energy, and bus communication dissipation.
- **Genetic Algorithm Engine**: Fully customizable evolutionary solver with elitism, convergence tracking, and early stopping.
- **Strict Precedence & DAG Scheduling**: Support for both deadline-sorted scheduling and dependency-aware DAG scheduling (`DagTaskScheduler`).
- **Pluggable Strategies**: Strategy pattern implementation for Selection, Crossover, Mutation, and Bus Arbitration.
- **Fluent Builders**: Fluent API for constructing processors, energy parameters, tasks, and dependency matrices.
- **100% Backward Compatibility**: Drop-in replacement for legacy modules with all mathematical and algorithmic bugs resolved.
- **Zero Third-Party Dependencies**: Pure Python standard library implementation for the core scheduling engine.

---

## Physical Energy & Power Modeling

The framework computes total system energy across four distinct physical dissipation sources:

### 1. Dynamic Energy ($E_{\text{dynamic}}$)
Dynamic power dissipation in CMOS circuits is governed by:

$$P_{\text{dynamic}} = C_{\text{eff}} \cdot f \cdot V^2$$

Where $C_{\text{eff}}$ is the effective switching capacitance, $f$ is operating frequency, and $V$ is supply voltage. If a task has base execution time $t_{\text{base}}$ at the processor's maximum base frequency $f_{\text{base}}$, its scaled duration at frequency $f$ is:

$$t_{\text{exec}} = \frac{f_{\text{base}}}{f} \cdot t_{\text{base}}$$

Thus, dynamic energy consumed during execution is:

$$E_{\text{dynamic}} = P_{\text{dynamic}} \cdot t_{\text{exec}} = C_{\text{eff}} \cdot f_{\text{base}} \cdot t_{\text{base}} \cdot V^2$$

Scaling down frequency and voltage yields quadratic energy savings.

### 2. Voltage Transition Energy ($E_{\text{transition}}$)
Switching voltage states on a power distribution rail charges and discharges rail capacitance $C_{\text{rail}}$:

$$E_{\text{transition}} = C_{\text{rail}} \sum_{i=1}^{N} |V_{i-1} - V_i|^2 + C_{\text{rail}} |V_N - V_{\text{base}}|^2$$

This prevents rapid, thrashing voltage modulations.

### 3. Idle Power Dissipation ($E_{\text{idle}}$)
Processors that finish their assigned workloads before the overall system makespan ($T_{\text{makespan}}$) consume static/idle power $P_{\text{idle}}$:

$$E_{\text{idle}} = P_{\text{idle}} \cdot \max(0, T_{\text{makespan}} - t_{\text{busy}})$$

### 4. Communication Interconnect Energy ($E_{\text{comm}}$)
When tasks mapped to different processors exchange data, transfers are transmitted across a shared half-duplex bus:

$$E_{\text{comm}} = P_{\text{comm}} \cdot \sum \text{duration}(comm_{\text{cross-core}})$$

Intra-core communications incur zero bus energy overhead.

### 5. Multi-Objective Fitness Evaluation
The fitness function maximizes energy savings while penalizing deadline violations:

$$\text{Fitness} = \frac{1}{E_{\text{total}} \cdot (1 + \lambda \cdot N_{\text{missed}})}$$

Where $\lambda \ge 0$ is the deadline penalty weight factor and $N_{\text{missed}}$ is the number of tasks completing after their deadline.

---

## Software Architecture & SOLID Design

```
+-------------------------------------------------------------+
|                      LowPowerOptimizer                      | (Facade Pattern)
+------------------------------+------------------------------+
                               |
       +-----------------------+-----------------------+
       |                                               |
+------v-------------------+               +-----------v----------+
|     GeneticAlgorithm     |               |    TaskScheduler     |
| (Template Method Pattern)|               |  (IScheduler Strat)  |
+--------------+-----------+               +-----------+----------+
               |                                       |
    +----------+----------+                 +----------+----------+
    |          |          |                 |                     |
+---v----+ +---v----+ +---v----+       +----v-----+          +----v----+
|Select  | |Cross   | |Mutate  |       |Processor |          |BusChannel
|Strategy| |Strategy| |Strategy|       |Element   |          |& Arbiter
+--------+ +--------+ +--------+       +----------+          +---------+
```

### Applied SOLID Principles
1. **Single Responsibility Principle (SRP)**:
   - `Task` models task definitions; `TaskGraph` manages topological precedence; `ProcessorElement` models hardware states; `BusChannel` manages communication contention; `FitnessEvaluator` computes CMOS physical energy.
2. **Open/Closed Principle (OCP)**:
   - Evolutionary operators and arbitration algorithms are decoupled behind abstract strategy interfaces (`SelectionStrategy`, `CrossoverStrategy`, `MutationStrategy`, `ArbiterStrategy`). Users can plug in custom heuristics without modifying engine internals.
3. **Liskov Substitution Principle (LSP)**:
   - Subtypes (`TournamentSelection`, `SinglePointCrossover`, `PriorityArbiter`, `DagTaskScheduler`) conform completely to their base contracts and can be swapped interchangeably.
4. **Interface Segregation Principle (ISP)**:
   - Granular interfaces keep client code independent of unused methods.
5. **Dependency Inversion Principle (DIP)**:
   - High-level orchestrators depend upon abstractions rather than concrete subclasses.

---

## Flow Bug Fixes & Enhancements

During comprehensive auditing, the following algorithmic and implementation bugs in the original codebase were identified and resolved:

| # | Component | Original Bug | Resolution |
|---|---|---|---|
| 1 | `Fitness.__init__` | Scalar `efficient_capacity` was overwritten with `idle_power` due to variable shadowing | Correctly sets `[efficient_capacity] * pe_count` |
| 2 | `IndividualGenerator.mutate` | `random.randint(0, len(dna))` produced an off-by-one `IndexError` | Clamped to `len(dna) - 1` |
| 3 | `IndividualGenerator.mutate` | Gene boundary used `<= task_count`, misclassifying the first frequency gene as a PE gene | Corrected condition to `< task_count` |
| 4 | `Individual.get_pe_index` | `index <= task_count` caused boundary access to read frequency gene as PE gene | Adjusted indexing logic to `< task_count` |
| 5 | `crossover` | Slice `dna[cut : -1]` omitted the final gene from crossover operations | Swapped to full tail slice `dna[cut :]` |
| 6 | Mutation/Crossover | Mutating a PE gene left frequency index exceeding new PE's available DVFS levels | Added automatic gene validation and chromosome repair |
| 7 | `CommunicationElement.Arbiter` | Over-constrained `and` logic required all comparison criteria simultaneously | Implemented proper hierarchical key comparisons |
| 8 | `CommunicationElement` | `timeline` was never cleared on re-scheduling, accumulating duration across runs | Reset timeline on each scheduling pass |
| 9 | `ProcessorElement.__str__` | Method contained only `pass`, returning `None` | Implemented clear, readable string format |
| 10 | Task Precedence | Sequential scheduler ran tasks from time zero regardless of dependencies | Introduced `DagTaskScheduler` enforcing DAG ready-time constraints |

---

## Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/JA303/LowPower-Task-Scheduling.git
cd LowPower-Task-Scheduling
pip install -e .
```

*Note: The core framework requires only Python 3.8+ and no third-party packages.*

---

## Quick Start

Run the end-to-end demonstration script:

```bash
python main.py
```

---

## Code Examples

### 1. Fluent System & Task Graph Construction
```python
from lowpower_scheduler import SystemBuilder, TaskGraphBuilder, LowPowerOptimizer

# Build multiprocessor system
system = (
    SystemBuilder()
    .add_processor("P0", [(1000, 5.0), (500, 3.0), (100, 1.0)])
    .add_processor("P1", [(1000, 5.0), (400, 3.0), (200, 1.0)])
    .set_communication_power(10.0)
    .set_idle_power(10.0)
    .set_efficient_capacities([1.0, 2.0])
    .set_voltage_rail_capacities([4.0, 4.0])
    .build()
)

# Build task graph
tasks = (
    TaskGraphBuilder()
    .add_task("T0", deadline=25.0, execution_times={"P0": 10.0, "P1": 10.0}, communications={"T1": 2.0})
    .add_task("T1", deadline=25.0, execution_times={"P0": 8.0, "P1": 16.0})
    .build_task_list()
)

# Optimize with Facade
optimizer = LowPowerOptimizer(tasks, system.processors, system.fitness_evaluator)
summary = optimizer.optimize(generations=40, population_size=30)
```

### 2. DAG-Precedence Scheduling with Shared Bus Interconnect
```python
from lowpower_scheduler import DagTaskScheduler, TaskAssignment

scheduler = DagTaskScheduler(system.processors)
scheduler.assign([
    TaskAssignment(tasks[0], "P0", frequency_index=0),
    TaskAssignment(tasks[1], "P1", frequency_index=1),
])
scheduler.schedule()
scheduler.print()
system.fitness_evaluator.print(scheduler)
```

### 3. Custom Strategy Injection (Strategy Pattern)
```python
from lowpower_scheduler import GeneticAlgorithm
from lowpower_scheduler.strategies.selection import RankSelection
from lowpower_scheduler.strategies.crossover import TwoPointCrossover
from lowpower_scheduler.strategies.mutation import SwapMutation

ga = GeneticAlgorithm(
    task_list=tasks,
    pe_list=system.processors,
    fitness_evaluator=system.fitness_evaluator,
    selection_strategy=RankSelection(),
    crossover_strategy=TwoPointCrossover(),
    mutation_strategy=SwapMutation(),
)
best_ind, best_sched, min_energy = ga.run()
```

---

## Project Directory Structure

```
LowPower-Task-Scheduling/
├── pyproject.toml              # PEP 621 packaging metadata
├── setup.py                    # Setup script for packaging
├── requirements.txt            # Package dependencies
├── requirements-dev.txt        # Development dependencies
├── README.md                   # Project documentation
├── main.py                     # Interactive demonstration script
├── lowpower_scheduler/         # Main package (SOLID refactored)
│   ├── __init__.py
│   ├── facade.py               # LowPowerOptimizer unified facade
│   ├── models/                 # Domain models
│   │   ├── task.py             # Task and TaskGraph (DAG)
│   │   ├── processor.py        # ProcessorElement and DVFSLevel
│   │   ├── communication.py    # CommunicationRequest and BusChannel
│   │   └── assignment.py       # TaskAssignment and ScheduleResult
│   ├── core/                   # Core scheduling and energy modules
│   │   ├── timeline.py         # Timeline and TimeInterval
│   │   ├── scheduler.py        # TaskScheduler and DagTaskScheduler
│   │   ├── energy.py           # EnergyModel and FitnessEvaluator
│   │   └── individual.py       # Individual and chromosome factory
│   ├── strategies/             # Pluggable strategies
│   │   ├── arbiter.py          # Priority, FCFS, ShortestFirst
│   │   ├── selection.py        # Tournament, Roulette, Rank
│   │   ├── crossover.py        # SinglePoint, TwoPoint, Uniform
│   │   └── mutation.py         # RandomResetting, Swap
│   ├── ga/                     # Evolutionary optimization engine
│   │   ├── engine.py           # GeneticAlgorithm solver
│   │   └── callbacks.py        # HistoryLogger, EarlyStopping, ConsoleReporter
│   └── builder/                # Fluent builders
│       └── system_builder.py   # SystemBuilder and TaskGraphBuilder
├── Scheduler/                  # Backward compatibility wrapper package
│   ├── Task.py
│   ├── ProcessorElement.py
│   ├── CommunicationElement.py
│   ├── Timeline.py
│   ├── TaskScheduler.py
│   ├── Individual.py
│   └── Fitness.py
├── examples/                   # Executable example workflows
│   ├── 01_basic_scheduling.py
│   ├── 02_genetic_optimization.py
│   ├── 03_custom_strategies.py
│   └── 04_dag_precedence_scheduling.py
└── tests/                      # Unit test suite
    ├── test_models.py
    ├── test_timeline.py
    ├── test_energy.py
    ├── test_arbiters.py
    ├── test_ga_operators.py
    ├── test_scheduler.py
    ├── test_genetic_algorithm.py
    ├── test_builder.py
    └── test_backward_compatibility.py
```

---

## Running Tests

Execute the complete test suite via Python's built-in `unittest` runner:

```bash
python -m unittest discover -s tests
```

Or using `pytest`:

```bash
pytest tests/
```

All 35 unit tests validate core modeling, energy formulas, algorithmic invariants, and bug fixes.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
