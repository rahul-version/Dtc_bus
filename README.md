# 🚌 Delhi Bus Crowdedness-Aware Journey Planner & Load Estimation
### DTC Transit Network • Problem 2 / Phase 1 — Delhi Transport Stack

---

## 📌 Project Overview & Implementation Narrative

Is project me maine Delhi Transport Corporation (DTC) ke **2.56 Million electronic ticketing records (October 2026)** aur **static GTFS transit topology** ko process karke ek complete crowdedness-aware transit engine, predictive machine learning model, aur multi-platform commuter journey planner develop kiya hai.

Delhi ke daily bus commuters ke liye sabse badi problem yeh hoti hai ki unhe trip start karne se pehle bus ke andar ki bheed (crush load vs seats available) ka pata nahi chalta. Is challenge ko solve karne ke liye maine data cleaning se lekar passenger load estimation, ML inference, aur interactive web interfaces tak ka pura end-to-end system design aur implement kiya hai.

---

## 🏗️ Architecture & File Structure Jo Maine Banaya Hai

Maine pure system ko modular aur reproducible architecture me organize kiya hai:

```
project_DTC/
│
├── config.yaml                    <-- Sabhi thresholds, vehicle capacities, & uplift factors ka central config
├── October-Delhi.csv              <-- Raw ticketing transactions dataset (2,559,899 rows, 31 days)
├── run_pipeline.py                <-- Master pipeline runner script jo steps 1 se 6 tak automatically execute karta hai
├── app_streamlit.py               <-- Streamlit commuter app ("Fastest" vs "Comfortable" trade-off logic ke saath)
├── TECHNICAL_NOTE.md              <-- Detailed mathematical methodology, assumptions, aur transit science documentation
│
├── gtfs/                          <-- Delhi static GTFS topology
│   ├── stops.txt                  <-- 7,552 canonical bus stops with geographic coordinates
│   ├── routes.txt                 <-- 2,259 transit routes across Delhi-NCR
│   ├── trips.txt                  <-- Representative scheduled route trips
│   ├── stop_times.txt             <-- 69,634 sequential stop times
│   └── route_stop_sequences.json  <-- Directional stop sequence lookup dictionary
│
├── pipeline/                      <-- 6-step audited transit data pipeline jo maine banayi hai
│   ├── step1_cleaning_eda.py      <-- Timestamp parsing, NaN vehicle profile, route regex cleaning
│   ├── gtfs_builder.py            <-- Canonical GTFS builder from transit network
│   ├── step2_stop_matching.py     <-- RapidFuzz alignment aur directional sequence validation
│   ├── step3_hybrid_load.py       <-- Method A (trip segmentation) + Method B (aggregate scaling)
│   ├── step4_load_estimation.py   <-- Difference-array persistence, Pink Pass uplift (+25%), capacity load
│   ├── step5_validation.py        <-- Holdout week-4 testing, peak-to-trough ratios, holiday audits
│   └── step6_outputs.py           <-- Tidy Parquet/CSV, Folium choropleth, operator recommendations
│
├── ml_model/                      <-- Machine Learning inference module jo maine integrate kiya hai
│   ├── schema.py                  <-- Pydantic input/output contracts
│   ├── predictor.py               <-- Model loader & inference engine
│   ├── train_model.py             <-- 65,805 route profile training script
│   └── saved_models/
│       └── dtc_crowd_model.pkl    <-- Trained model checkpoint
│
├── backend/                       <-- FastAPI async backend service (Port 8000)
│   └── app/
│       ├── main.py                <-- REST API routes, CORS, middleware
│       ├── routers/journey.py     <-- Journey planning & live bus endpoints
│       └── services/journey_service.py <-- Dynamic GTFS corridor search, token NLP, ML linkage
│
├── frontend/                      <-- Vite + React modern web application (Port 3000)
│   ├── src/components/
│   │   ├── JourneySearch.jsx      <-- Quick time-chips, instant autocomplete, trip preferences
│   │   ├── StopAutocomplete.jsx   <-- Instant stop selection on focus, 1-char fast search
│   │   ├── RouteCard.jsx          <-- Visual crowd meters, seat vacancy, departure advice
│   │   └── TransitMap.jsx         <-- Google Maps basemap, exact station pinpoints, route polylines
│   └── tailwind.config.js
│
└── outputs/                       <-- Pipeline execution se generate hue processed datasets aur plots
    ├── tidy_segment_crowding.parquet <-- 958,505 segment load records (7.94 MB)
    ├── tidy_segment_crowding.csv     <-- Tabular human-readable output (78.47 MB)
    ├── folium_delhi_crowding_map.html<-- Interactive transit network corridor choropleth
    ├── operator_bottleneck_recommendations.csv <-- Top 20 overloaded routes & fleet scheduling
    └── plots/                        <-- Diagnostic & validation charts
```

---

## 🔬 Pipeline Me Maine Kya Kiya & Yahan Pe Kya Hota Hai

### Step 1: Audited Cleaning & EDA (`pipeline/step1_cleaning_eda.py`)
- **Maine kya kiya**: Raw ticketing dataset me 2,559,899 transactions ko parse kiya aur zero silent data loss ensure kiya.
- **Yahan pe ye hota hai**:
  - `ticket_timestamp` ko strict ISO datetime format me parse kiya jata hai.
  - Missing `vehicle_number` analysis ki: 48.52% transactions me vehicle number missing tha (One Delhi mobile ticketing app) jabki 51.48% transactions physical ETM machines se the. Maine dono groups ka distribution compare karke prove kiya ki data statistically missing-at-random (MAR) hai.
  - Route ID ko regex `^(.*?)(UP|DOWN)(\d*)$` se standard route aur direction me split kiya.
  - Sirf zero-distance trips ($start == end$, 103 rows) aur negative fares (8 rows) drop hue.
  - Total **2,559,788 rows (99.9957%)** retain hue.

### Step 2: GTFS Stop Alignment & Direction Filtering (`pipeline/step2_stop_matching.py`)
- **Maine kya kiya**: Ticketing data me aane wale messy Hindi/English stop names ko canonical GTFS `stops.txt` ke 7,552 stops ke sath match kiya.
- **Yahan pe ye hota hai**:
  - 2-tier RapidFuzz algorithm stop sequence constraints ke sath match karta hai:
    - 99.4% stops exact aur override dictionary se match hote hain.
    - 0.5% route-constrained fuzzy matching se map hote hain.
  - Reverse direction tickets (jahan alight stop board stop se pehle aa raha tha, 8.63%) drop kiye jate hain.
  - **2,258,831 GTFS-aligned monotonic tickets (88.24% match rate)** step 3 me pass hote hain.

### Step 3: Hybrid Missing Vehicle Handling (`pipeline/step3_hybrid_load.py`)
- **Maine kya kiya**: Unassigned vehicle records (48.5%) ke load ko mathematically account karne ke liye maine do complementary methods implement kiye:
- **Yahan pe ye hota hai**:
  - **Method A (Physical Trips)**: Known vehicle IDs ko consecutive transactions ke time gap ($> 25$ min headway) aur terminal reset ke basis pe 770,542 physical trips me segment kiya jata hai.
  - **Method B (Aggregate Scaling)**: Missing vehicle volume ko scaling factor $\kappa = 1.9476$ se expand kiya jata hai.
  - Maine dono methods ke beech Kolmogorov-Smirnov test ($D = 0.0174$) aur linear correlation ($r = 0.9484$) verify karke representativeness validate ki hai.

### Step 4: Segment Load Persistence & Pink Pass Uplift (`pipeline/step4_load_estimation.py`)
- **Maine kya kiya**: Har bus route ke har stop-to-stop segment par on-board passenger load calculate kiya.
- **Yahan pe ye hota hai**:
  - Prefix-sum difference array se stop $k$ par cumulative load calculate hota hai:
    $$L_k = \sum_{m=0}^k (\text{Boardings}_m - \text{Alightings}_m)$$
  - 3-point alighting smoothing ($10\% - 80\% - 10\%$) apply ki gayi taaki ticketing delays absorb ho sakein.
  - **Delhi Pink Pass Uplift**: Female passengers ke zero-fare Pink Pass travel ko account karne ke liye maine $+25\%$ load factor (`1.25x`) multiply kiya.
  - Capacity standard 65 passengers (DTC 12m standard floor bus) ke against crowding levels classify hoti hain:
    - 🟢 **Seats Available** ($\text{Load Factor} \le 0.65$): Network ke 48.32% segments
    - 🟡 **Standing Room** ($0.65 < \text{Load Factor} \le 1.05$): Network ke 24.74% segments
    - 🔴 **Crowded / Packed** ($\text{Load Factor} > 1.05$): Network ke 26.94% segments

### Step 5: Statistical Validation & Sanity Audits (`pipeline/step5_validation.py`)
- **Maine kya kiya**: Pure pipeline ke outputs ko rigorous transit science sanity checks se guzaara:
- **Yahan pe ye hota hai**:
  - **Holdout Validation**: Weeks 1-3 ke data se Week 4 predict kiya ($R^2 = 0.9443$, $r = 0.9787$, $\text{MAE} = 5.66$ tickets).
  - **Dual Peak Verification**: Morning peak ridership midday trough se **$4.55\times$** hai, aur evening peak **$2.78\times$** hai.
  - **Holiday Anomaly**: Gandhi Jayanti (2 Oct) par $-58.5\%$ aur Dussehra (20 Oct) par $-48.5\%$ ridership drop reflect hua.

### Step 6: Tidy Production Exports & Operator Dashboard (`pipeline/step6_outputs.py`)
- **Maine kya kiya**: Processed data ko downstream services ke liye export kiya:
- **Yahan pe ye hota hai**:
  - `outputs/tidy_segment_crowding.parquet` (958,505 rows, 7.94 MB) generate hota hai jo fast analytical queries support karta hai.
  - `outputs/folium_delhi_crowding_map.html` interactive choropleth map banata hai.
  - `outputs/operator_bottleneck_recommendations.csv` DTC planners ke liye top 20 overloaded routes aur bus injection schedule provide karta hai.

---

## 🧠 Machine Learning Model Jo Maine Integrate Kiya Hai (`ml_model/`)

Maine DTC network ke 65,805 distinct route-hour-day patterns par ML model train kiya hai jo `ml_model/saved_models/dtc_crowd_model.pkl` me saved hai.

- **Inputs**: Route ID, Time of Day (24-hr), Day of Week (Weekday/Weekend), AC vs Non-AC, consecutive stop stretches.
- **Inference**: Model har segment ke liye `occupancy_ratio`, `estimated_passengers`, `crowding_level`, aur `crowding_color` predict karta hai.
- **Smart Commuter Advice**: Model automatically detect karta hai ki agle 10-15 minute me bheed kam hogi ya kis intermediate station ke baad seats khali hongi.

---

## 💻 Commuter Applications Jo Maine Banaye Hain

Maine do production-ready commuter interfaces develop kiye hain:

### 1. Modern React + Vite Web App (`frontend/` on Port 3000)
- **High-Resolution Google Maps**: OpenStreetMap ki jagah high-resolution Google Maps Roadmap aur Hybrid Satellite tiles integrate kiye hain.
- **Prominent Station Pinpoints**: Start station par green teardrop pin ke sath floating badge (`📍 Start Station Name`) aur destination par red teardrop pin ke sath floating badge (`🏁 Destination Station Name`) exact coordinates par pin point hote hain.
- **Dynamic GTFS Route Matcher**: Delhi ke kisi bhi arbitrary station pair ke beech valid direct routes fetch karta hai (jaise Route 425, 425CL, 411 between Hamdard Nagar and Kashmere Gate) bina kisi false corridor overmatching ke.
- **Instant Autocomplete**: Search bar par click karte hi top popular hubs khulte hain aur 1 character type karne par bhi relevant stations filter hote hain.
- **Real-Time GPS Fleet Tracking**: DTS live bus simulator toggleable hai jo route par live EV aur CNG buses ki position display karta hai.

### 2. Streamlit Analytical Dashboard (`app_streamlit.py` on Port 8501)
- **Fastest vs Comfortable Toggle**: Commuters strictly travel time ke according sort kar sakte hain ya bheed-penalized score (`Time + 20 × max(0, LF - 1.0)`) se comfortable bus choose kar sakte hain.
- **Smart Departure Nudge**: Agar 15 minute wait karne se crowding 'Packed' se 'Seats Available' ho jati hai to commuter ko alert milta hai.
- **Interactive Corridor Choropleth**: Color-coded transit stretches with tooltips.

---

## 🚀 Execution & Verification

Maine pure system ko execute aur verify karne ke liye ye entry points setup kiye hain:

```bash
# 1. Pura 6-step pipeline run karne ke liye:
python run_pipeline.py

# 2. FastAPI backend start karne ke liye:
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. React Vite frontend launch karne ke liye:
npm --prefix frontend run dev -- --host 0.0.0.0 --port 3000

# 4. Streamlit commuter dashboard launch karne ke liye:
streamlit run app_streamlit.py --server.port 8501
```

- **React Commuter Portal**: [http://localhost:3000](http://localhost:3000)
- **FastAPI API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Streamlit Analytics Dashboard**: [http://localhost:8501](http://localhost:8501)

---

## 📑 Detailed Technical Reference
Mathematical derivations, statistical proofs, aur capacity assumptions ke liye:
👉 [TECHNICAL_NOTE.md](TECHNICAL_NOTE.md)
