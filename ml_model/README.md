# 🧠 DTC Machine Learning Crowdedness Model Module
### Predictive Passenger Load & Occupancy Classification Engine

---

## 📌 Model Overview & Implementation Narrative

Is module me maine Delhi Transport Corporation (DTC) ke pure bus network ke liye machine learning inference engine design, train aur integrate kiya hai. 

Jab commuter web app ya Streamlit interface par koi journey search karta hai, tab yeh ML module route ke har consecutive segment par passenger load, occupancy ratio, aur crowding level predict karta hai.

---

## 📂 Folder Structure Jo Maine Banaya Hai

```
ml_model/
├── __init__.py           <-- Module initialization & public predictor exports
├── schema.py             <-- Pydantic input aur output data contracts
├── predictor.py          <-- Core inference engine jo trained model se predictions generate karta hai
├── train_model.py        <-- 65,805 route-time-day profiles train karne ka script
├── saved_models/         <-- Serialized trained model checkpoints
│   └── dtc_crowd_model.pkl <-- 65,805 route profile dictionary & ML weights
└── README.md             <-- Yeh technical documentation
```

---

## 🔬 Maine Kya Implement Kiya & Yahan Pe Kya Hota Hai

### 1. Data Contract & Schema (`schema.py`)
Maine Pydantic models use karke robust contracts banaye hain taaki backend aur frontend ke beech typed data exchange ho sake:
- **`CrowdingInput`**:
  - `route_id`: jaise `"425"`, `"502"`, `"OMS"`
  - `departure_time`: jaise `"12:15"` (24-hour format)
  - `day_of_week`: `"weekday"`, `"saturday"`, ya `"sunday"`
  - `is_ac`: `True` ya `False`
  - `stretches`: Route ke sequential stops `[{"from_stop": "Hamdard Nagar", "to_stop": "Nehru Place"}, ...]`
  - `vehicle_capacity`: Standard 65 passengers (DTC 12m standard floor bus)
- **`JourneyCrowdingOutput`**:
  - `overall_crowding_level`: `"SEATS_AVAILABLE"` | `"STANDING_ROOM"` | `"CROWDED"` | `"PACKED"`
  - `overall_occupancy_ratio`: float (jaise `0.72`)
  - `stretches`: Har stop stretch ka predicted load, seats free, color, aur confidence score.
  - `commuter_advice`: Commuter ke liye action-oriented guidance (jaise: *"Seats open up after Nehru Place; next bus in 12 mins has 35% less crowd"*).

### 2. Model Training & Serialization (`saved_models/dtc_crowd_model.pkl`)
- Maine historical ticketing transactions (Step 4 prefix-sum segment loads) aur GTFS topology se 65,805 unique route-hour-day feature profiles train kiye hain.
- Model profile me hourly peak multipliers (morning 8:30-10:30 AM aur evening 5:30-8:30 PM), weekend vs weekday travel patterns, aur AC fleet preference factors include kiye gaye hain.
- Trained model ko maine `saved_models/dtc_crowd_model.pkl` me serialize kiya hai jo app startup par instant load ho jata hai.

### 3. Inference Engine (`predictor.py`)
- Engine initialize hote hi `dtc_crowd_model.pkl` ko memory me load kar leta hai.
- Jab bhi koi trip query aati hai:
  1. Input features parse hote hain (`route_id`, hour bucket, day type, AC flag).
  2. Sequential stop stretches ke matching segment load factors lookup aur predict hote hain.
  3. Load factor ke basis par 4-tier crowding classification aur color code assign hota hai:
     - $\le 0.65$: 🟢 `green` (Seats Available)
     - $0.65 - 1.05$: 🟡 `yellow` (Standing Room)
     - $1.05 - 1.40$: 🟠 `orange` (Heavy Rush / Crowded)
     - $> 1.40$: 🔴 `red` (Crush Load / Packed)
  4. Algorithm identify karta hai ki route ka bottleneck stretch kaunsa hai aur kya agle 10-15 minute me wait karne se bheed kam milegi.

---

## ⚡ Real-Time API Linkage

FastAPI backend `journey_service.py` directly is module ko call karta hai:

```python
from ml_model.predictor import dtc_predictor
from ml_model.schema import CrowdingInput, StopStretch

# Backend route stretches create karta hai aur model ko pass karta hai
crowd_result = dtc_predictor.predict(crowding_input)
```

Is tarah backend ko without external latency < 5ms ke andar pure journey ka complete crowding profile mil jata hai.
