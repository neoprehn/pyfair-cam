# pyfair-cam 🌭

**Monte Carlo Simulator for FAIR-CAM (Controls Analytics Model)**

Based on the FAIR-CAM Knowledge Base by Jack Jones / FAIR Institute.

## What is FAIR-CAM?

FAIR-CAM extends the FAIR methodology to provide a structured approach for analyzing and measuring the effectiveness of cybersecurity controls in reducing risk.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from pyfair_cam import FairCamModel, FairCamSimulator, BetaPert, LogNormal

model = FairCamModel(name="Ransomware Szenario")
model.input_threat_frequency(BetaPert(low=5, mode=10, high=20))
model.input_loss_magnitude(LogNormal(mean=200_000, stdev=150_000))

simulator = FairCamSimulator(n_simulations=10_000, seed=42)
simulator.run(model)

stats = simulator.get_statistics()
print(f"ALE: € {stats['mean']:,.0f}")
```

## Attribution

FAIR-CAM was created by Jack Jones.
Knowledge Base: [FAIR-CAM-Knowledge-Base](https://github.com/faircam/FAIR-CAM-Knowledge-Base) (CC BY-NC-ND 4.0)

## License

MIT (own code) | Knowledge Base content: CC BY-NC-ND 4.0
