# pyfair-cam – Monte Carlo Simulator Notiz

## Architektur-Entscheidung

Eigener Monte Carlo Simulator – nicht von pyfair abgeleitet.
Gleiche Eigenschaften wie pyfair MC, aber für FAIR-CAM Faktoren optimiert.
pyfair bleibt eine separate Abhängigkeit für FAIR-Berechnungen.

---

## Eigenschaften des MC Simulators (Wurstmaschine)

### 1. Verteilungen
| Verteilung | Klasse | Zweck |
|---|---|---|
| BetaPERT | `BetaPert` | Drei-Punkt-Schätzung (min/wahrscheinlich/max) |
| Lognormal | `LogNormal` | Verlusthöhen (rechts-schief) |
| Normal | `Normal` | Symmetrische Größen |
| Uniform | `Uniform` | Gleichverteilung |
| Poisson | `Poisson` | Häufigkeiten (Events pro Zeit) |
| Bernoulli | `Bernoulli` | Ja/Nein Events (z.B. Vulnerability) |

### 2. Sampling-Eigenschaften
| Eigenschaft | Wert | Implementierung |
|---|---|---|
| Anzahl Simulationen | 10.000 - 100.000 | Konfigurierbar per Parameter |
| Reproduzierbarkeit | Seed-basiert | `numpy.random.seed()` |
| Geschwindigkeit | Vektorisiert | `numpy` arrays, kein loop |

### 3. Berechnungsfähigkeiten
| Berechnung | Zweck | Methode |
|---|---|---|
| Loss Exceedance Curve (LEC) | Wahrscheinlichkeit für Verluste über X | `calculate_lec()` |
| Annual Loss Expectancy (ALE) | Erwartungswert | `calculate_ale()` |
| Value at Risk (VaR) | 95%/99% Perzentile | `calculate_var()` |
| Risikoaggregation | Mehrere Szenarien kombinieren | `aggregate()` |

### 4. Statistische Auswertung
| Metrik | Bedeutung | numpy Funktion |
|---|---|---|
| Mean | Durchschnitt | `np.mean()` |
| Median | Mittelwert | `np.median()` |
| Perzentile | P10/P25/P50/P75/P90/P95/P99 | `np.percentile()` |
| Standardabweichung | Streuung | `np.std()` |
| Min/Max | Extremwerte | `np.min() / np.max()` |

### 5. FAIR-CAM spezifische Erweiterungen
| Faktor | Beschreibung | Implementierung |
|---|---|---|
| Resistance | Reduktionsfaktoren (0-1) | Multiplikator auf Loss |
| Susceptibility | Anfälligkeit modellieren | Bedingte Wahrscheinlichkeit |
| Detection Time | Zeitverteilungen | Exponential/Weibull Verteilung |
| Response Effectiveness | Wirksamkeitsverteilungen | Beta Verteilung |
| Control Function Composition | Faktoren verkettet anwenden | Pipeline Pattern |

---

## Geplante Klassen-Struktur

```python
# pyfair_cam/simulator/monte_carlo.py
class FairCamSimulator:
    def __init__(self, n_simulations=10_000, seed=None):
        self.n_simulations = n_simulations
        self.seed = seed
    
    def run(self, model):
        # Hauptmethode der Wurstmaschine
        ...

# pyfair_cam/simulator/distributions.py
class BetaPert:
    def __init__(self, low, mode, high, gamma=4):
        ...

class LogNormal:
    def __init__(self, mean, stdev):
        ...

# pyfair_cam/factors/resistance.py
class ResistanceFactor:
    def __init__(self, distribution, **params):
        ...

# pyfair_cam/factors/susceptibility.py
class SusceptibilityFactor:
    def __init__(self, distribution, **params):
        ...
```

---

## Abhängigkeiten

```
numpy          →  Vektorisierte Berechnungen
scipy          →  Statistische Verteilungen
pandas         →  Ergebnis-DataFrames
matplotlib     →  Basis-Grafiken
plotly         →  Interaktive Grafiken (LEC Kurve)
pyfair         →  Separate FAIR Berechnungen (kein MC Import)
```

---

## Wichtige Designprinzipien

1. **Unabhängig von pyfair MC** – eigene Engine
2. **Gleiche Schnittstelle** – ähnliche API wie pyfair für Konsistenz
3. **Vektorisiert** – kein Python-Loop, alles numpy
4. **Reproduzierbar** – immer Seed setzen
5. **Erweiterbar** – neue FAIR-CAM Faktoren einfach hinzufügbar
6. **Knowledge Base** – FAIR-CAM-Knowledge-Base als Git Submodule (read-only)

---

## Knowledge Base Anbindung

```
FAIR-CAM-Knowledge-Base (Git Submodule)
→ Wird als Referenz für Faktoren-Definitionen genutzt
→ Read-only, keine Änderungen
→ Update via: git submodule update --remote
→ Enthält: 10 MD-Dateien zu FAIR-CAM Konzepten
```

Lizenz beachten: CC BY-NC-ND 4.0
- Namensnennung: Jack Jones / FAIR Institute
- Nicht-kommerziell
- Keine Bearbeitung/Weiterverbreitung der MD-Dateien
