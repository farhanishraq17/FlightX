## FlightX

FlightX is an **AI simulation** where *virtual aircraft* learn to fly through a challenging environment filled with obstacles. Each aircraft is controlled by a **neural network** that acts as its "brain," making decisions based on its perception. The project uses a **NEAT evolutionary algorithm** to allow these AI players to *learn and improve* their flying skills over many generations, progressively getting smarter at navigating the game world.


## Visual Overview

```mermaid
flowchart TD
    A0["Game Loop & Orchestration
"]
    A1["AI Player (Aircraft Agent)
"]
    A2["Neural Network (AI Brain)
"]
    A3["NEAT Evolutionary Algorithm
"]
    A4["Game Environment & Obstacles
"]
    A5["Global Game Configuration
"]
    A0 -- "Orchestrates simulation" --> A1
    A0 -- "Triggers evolution" --> A3
    A0 -- "Updates & draws" --> A4
    A0 -- "Uses & configures" --> A5
    A1 -- "Controls with" --> A2
    A1 -- "Interacts with" --> A4
    A1 -- "Reads settings from" --> A5
    A2 -- "Evolved by" --> A3
    A3 -- "Manages & evolves" --> A1
    A4 -- "Configured by" --> A5
    A5 -- "Provides central settings" --> A0
```

## Chapters

1. [Global Game Configuration
](01_global_game_configuration_.md)
2. [Game Environment & Obstacles
](02_game_environment___obstacles_.md)
3. [AI Player (Aircraft Agent)
](03_ai_player__aircraft_agent__.md)
4. [Neural Network (AI Brain)
](04_neural_network__ai_brain__.md)
5. [NEAT Evolutionary Algorithm
](05_neat_evolutionary_algorithm_.md)
6. [Game Loop & Orchestration
](06_game_loop___orchestration_.md)

---
