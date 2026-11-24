# Technical Note: Crowdedness-Aware Transit Modeling for Delhi Bus Network
**Project:** Delhi DTC Crowdedness-Aware Journey Planner  
**Dataset:** October 2026 E-Ticketing & ETM Transaction Logs (2,559,899 rows)  
**Specification:** Sound Transit Crowding Estimation & GTFS Alignment  

---

## 1. Executive Summary & Problem Formulation
The goal of this system is to transform raw, transaction-level bus ticket data lacking `trip_id` and `stop_id` into sound on-board passenger load estimates per route, direction, stop-to-stop segment, and time-of-day. The primary technical challenges include:
1. **Severe Vehicle Missingness**: 48.52% of rows have null `vehicle_number` (originating from mobile QR / One Delhi ticketing where the ticket is issued independently of physical bus telematics).
2. **Lack of Stop Identifiers**: Only heterogeneous textual stop names exist, requiring topological GTFS matching.
3. **Partial Observation**: Electronic ticketing captures only formal paying passengers, omitting non-fare categories such as Delhi Government's female zero-fare "Pink Pass" travelers.

---

## 2. Handling Missing `vehicle_number` (Hybrid Methodology)
Rather than dropping 48.52% of the dataset or fabricating physical vehicle assignments, we employ an audited **Hybrid Estimation Strategy**:

### A. Method A: Physical Bus Trip Segmentation (Known Cohort)
For tickets with valid `vehicle_number` (1,159,816 clean tickets), transactions are grouped by `(vehicle_number, route, date)` and chronologically ordered. Consecutive tickets are segmented into discrete physical trips using:
$$\Delta t = t_k - t_{k-1} > 25.0 \text{ minutes} \quad \lor \quad \Delta \text{stop\_index} < -3$$
This cleanly partitioned the known cohort into **770,542 physical bus trips** with an average duration of 3.3 minutes across ticket-issuing intervals.

### B. Method B: Aggregate Time-Bin Scaling (Full Census)
For tickets lacking vehicle numbers (1,099,015 tickets), records are aggregated at the `(route, direction, 15-min time-bin, day_type)` level. The aggregate passenger volume is scaled using an empirical expansion factor:
$$\kappa = \frac{N_{\text{total}}}{N_{\text{known}}} = \frac{2,258,831}{1,159,816} = 1.9476$$

### C. Statistical Representativeness Evaluation
To determine whether scaling Cohort A represents Cohort B without bias, statistical tests were conducted across time and network dimensions:
* **Hourly Diurnal Divergence**: Kolmogorov-Smirnov test statistic $D = 0.0174$ ($p = 1.26 \times 10^{-13}$), with a **Wasserstein (Earth Mover's) distance of only 0.0807 hours** (~4.8 minutes). Maximum proportion divergence across 24 hours was just **0.78%**.
* **Route Volume Agreement**: Route volume share across top routes yielded a Pearson correlation of **$r = 0.8971$** and Spearman rank correlation of **$\rho = 0.9362$**.
* **Method Comparison**: Cross-evaluation of 19,218 route-hour bins between Method A and Method B demonstrated a **linear correlation of $r = 0.9484$** with a median percentage difference of **19.58%**.

---

## 3. Stop Matching & Directional Monotonicity
Raw stop strings were cleaned via regex normalizers expanding abbreviations (`"Bdr"` $\to$ `"border"`, `"Mkt"` $\to$ `"market"`, `"Cr"` $\to$ `"crossing"`, `"T"` $\to$ `"terminal"`, `"Sec"` $\to$ `"sector"`).
* **Two-Tier RapidFuzz Matching**:
  1. *Tier 1 (Route-Constrained)*: Fuzzy matching against the ordered stop sequence of that specific GTFS route ($99.4\%$ exact/normalized + $0.5\%$ fuzzy hits).
  2. *Tier 2 (Global Fallback)*: Fuzzy matching against the entire 7,552-stop GTFS database ($0.1\%$ hits).
  3. *Unmatched*: Only 5 stop strings (< 0.01%) remained unmatched and were logged to `data/unmatched_stops.csv`.
* **Directional Sequence Filtering**:
  Tickets where alighting index $j \le i$ boarding index (8.63% of rows, representing return trips booked prematurely or unswitched conductor ETM machines) were removed to ensure strict forward monotonicity.

---

## 4. Mathematical Passenger Load Persistence & Difference Arrays
For a ticket $t$ with boarding stop index $i$ and alighting stop index $j$, passenger count $p_t$ persists across every intermediate segment $k \in [i, j-1]$. Rather than creating 45 million exploded records, we utilize the **Difference Array Formulation** in $O(N)$ time:
$$\text{Net Change at Stop } m = \text{Boardings}(m) - \text{Alightings}(m)$$
$$\text{Segment Load } L_k = \sum_{m=0}^k \text{Net Change}(m)$$
* **Alighting Smoothing**: To accommodate commuters alighting $\pm 1$ stop from their ticketed terminus, a 3-point smoothing kernel is applied:
$$\widetilde{L}_k = 0.10 L_{k-1} + 0.80 L_k + 0.10 L_{k+1}$$

---

## 5. Pink Pass Uplift & Bus Capacity Thresholds
1. **Delhi Pink Pass / Free-Rider Uplift**: The Delhi Government provides free travel to female commuters via zero-fare Pink Passes, omitting them from ticket transactions. We apply an uplift factor:
$$\gamma_{\text{pink}} = 1.25 \quad (+25\% \text{ passenger load})$$
2. **Sampling Calibration Multiplier**: To account for the 82,500 tickets/day sample against DTC's ~3.8M daily network ridership, a calibration factor $W = 22.0$ is applied.
3. **Capacities & 3-Tier Classification**:
   * Standard 12m Non-AC: 65 total (35 seated) | Standard 12m AC: 60 total (35 seated).
   * **$\text{Load Factor (LF)} = \frac{\text{Estimated Load}}{\text{Capacity}}$**:
     * $\text{LF} \le 0.65$: 🟢 **Seats Available** (48.32% of network segments)
     * $0.65 < \text{LF} \le 1.05$: 🟡 **Standing Room** (24.74% of network segments)
     * $\text{LF} > 1.05$: 🔴 **Crowded / Packed** (26.94% of network segments)

---

## 6. Model Validation & Sanity Checks
* **Holdout Validation**: Weeks 1–3 baseline evaluated against held-out Week 4 across 21,879 cells yielded **$R^2 = 0.9443$**, Pearson **$r = 0.9787$**, and MAE = 5.66 tickets.
* **Dual Peak Ratio**: Morning peak (8-10 AM) is **$4.55\times$** midday trough; Evening peak (5-8 PM) is **$2.78\times$** midday trough.
* **Holiday Dips**: Gandhi Jayanti (Oct 2) dropped ridership by **$-58.5\%$**; Dussehra (Oct 20) dropped ridership by **$-48.5\%$**.
* **Route Profile Continuity**: Major arterial Route 717A exhibits strict concavity (9.3 pax at terminal $\to$ 174.8 pax at mid-corridor $\to$ 117.2 pax at terminus).

---

## 7. Where Estimates Are Least Reliable (Confidence Boundaries & Limitations)
Commuters and transit operators should consider confidence tags when interpreting predictions:
1. **Infrequent Outer Ring & Feeder Routes**: Segments with $< 15$ observed tickets over October are tagged **`LOW` ("Low Data")** (44.78% of total sparse cells). Load estimates here have wide confidence intervals ($\pm 35\%$).
2. **Off-Peak Night Services (11:00 PM – 4:30 AM)**: Night services exhibit minimal ETM sampling, where single QR transactions can distort load factor estimates.
3. **Route Suffix Variations (`UP2`, `DOWN2`, `STL`)**: Short-turn shuttle trips (`STL`) may turn back before the route terminus, leading to slight overestimation of terminal segments on truncated runs.
4. **Pass-Holder Variance by Neighborhood**: The $+25\%$ Pink Pass uplift is applied network-wide; actual female ridership varies geographically from ~18% on industrial corridors to ~38% on residential/educational corridors.
