# 🚍 DTC Bus Crowdedness Web Portal (Frontend)
### Modern Commuter Web UI • React + Vite + Tailwind CSS + Leaflet

---

## 📌 Frontend Overview & Implementation Narrative

Is frontend application me maine Delhi bus commuters ke liye ek modern, intuitive aur mobile-responsive web portal banaya hai. Commuters apne start aur destination stops enter karke best direct bus routes compare kar sakte hain aur Google Maps basemap par accurate station pinpoints aur route crowding visualizer dekh sakte hain.

---

## 🏗️ Components Jo Maine Banaye Hain

```
frontend/src/
├── components/
│   ├── JourneySearch.jsx      <-- Search controls: From/To stops, time picker, time chips (Abhi, Morning, Evening)
│   ├── StopAutocomplete.jsx   <-- Fast autocomplete: Focus karte hi popular hubs khulte hain, 1 char search
│   ├── RouteCard.jsx          <-- Bus comparison cards: Duration, crowding tag, fare, seats free, advice
│   └── TransitMap.jsx         <-- Google Maps Roadmap/Hybrid tiles, teardrop pinpoints, route polyline
├── App.jsx                    <-- Main container, state management, API service linkage
└── main.jsx                   <-- React DOM root
```

---

## 🎨 Key Features & Visual Language Jo Maine Implement Kiya Hai

1. **Exact Station Pinpoints on Google Maps**:
   - Start station coordinate par prominent green teardrop pin aur floating badge (`📍 Start Stop Name`) render hota hai.
   - Destination station coordinate par prominent red teardrop pin aur floating badge (`🏁 Destination Stop Name`) render hota hai.
   - Route ke intermediate transit stops subtle white/slate dots ke sath hover tooltip me display hote hain.

2. **Google Maps High-Res Basemap**:
   - Google Roadmap standard mode aur Google Hybrid Satellite mode ke beech toggle support.

3. **Color-Coded Crowding Stretches**:
   - Route polyline Google Maps transit stroke language me render hoti hai:
     - 🟢 Green: Seats Available
     - 🟡 Yellow: Standing Room
     - 🟠 Orange: Heavy Rush
     - 🔴 Red: Crush Load / Packed

4. **Real-Time GPS Fleet Simulation**:
   - Live DTS bus tracking toggleable hai jo route par active DTC buses aur zero-emission EV buses ki live position aur ETA show karta hai.
