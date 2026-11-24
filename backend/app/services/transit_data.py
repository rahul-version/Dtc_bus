"""
Delhi Transit Topology Database
Rich GTFS-aligned data covering key DTC routes, stops, and coordinates.
Grounded in October-Delhi.csv transit patterns.
"""

from typing import List, Dict, Any

DELHI_STOPS: Dict[str, Dict[str, Any]] = {
    "anand vihar isbt": {
        "id": "stop_001",
        "name": "Anand Vihar ISBT",
        "lat": 28.6469,
        "lon": 77.3164,
        "zone": "East Delhi",
        "is_major_hub": True
    },
    "connaught place": {
        "id": "stop_002",
        "name": "Connaught Place (Shivaji Stadium)",
        "lat": 28.6315,
        "lon": 77.2167,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "rajiv chowk": {
        "id": "stop_003",
        "name": "Rajiv Chowk (Inner Circle)",
        "lat": 28.6328,
        "lon": 77.2197,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "kashmere gate isbt": {
        "id": "stop_004",
        "name": "Kashmere Gate ISBT",
        "lat": 28.6675,
        "lon": 77.2285,
        "zone": "North Delhi",
        "is_major_hub": True
    },
    "aiims": {
        "id": "stop_005",
        "name": "AIIMS (Sri Aurobindo Marg)",
        "lat": 28.5672,
        "lon": 77.2100,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "dhaula kuan": {
        "id": "stop_006",
        "name": "Dhaula Kuan",
        "lat": 28.5921,
        "lon": 77.1614,
        "zone": "South West Delhi",
        "is_major_hub": True
    },
    "nehru place": {
        "id": "stop_007",
        "name": "Nehru Place Bus Terminal",
        "lat": 28.5494,
        "lon": 77.2519,
        "zone": "South East Delhi",
        "is_major_hub": True
    },
    "laxmi nagar": {
        "id": "stop_008",
        "name": "Laxmi Nagar / Shakarpur",
        "lat": 28.6304,
        "lon": 77.2773,
        "zone": "East Delhi",
        "is_major_hub": True
    },
    "ito": {
        "id": "stop_009",
        "name": "ITO (Income Tax Office)",
        "lat": 28.6289,
        "lon": 77.2407,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "karol bagh": {
        "id": "stop_010",
        "name": "Karol Bagh (Gurudwara Road)",
        "lat": 28.6517,
        "lon": 77.1906,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "delhi gate": {
        "id": "stop_011",
        "name": "Delhi Gate",
        "lat": 28.6406,
        "lon": 77.2409,
        "zone": "Central Delhi",
        "is_major_hub": False
    },
    "akshardham": {
        "id": "stop_012",
        "name": "Akshardham Temple",
        "lat": 28.6186,
        "lon": 77.2778,
        "zone": "East Delhi",
        "is_major_hub": False
    },
    "preet vihar": {
        "id": "stop_013",
        "name": "Preet Vihar",
        "lat": 28.6418,
        "lon": 77.2952,
        "zone": "East Delhi",
        "is_major_hub": False
    },
    "sarai kale khan isbt": {
        "id": "stop_014",
        "name": "Sarai Kale Khan ISBT",
        "lat": 28.5898,
        "lon": 77.2575,
        "zone": "South East Delhi",
        "is_major_hub": True
    },
    "mehrauli": {
        "id": "stop_015",
        "name": "Mehrauli Terminal",
        "lat": 28.5186,
        "lon": 77.1856,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "saket": {
        "id": "stop_016",
        "name": "Saket Metro Station",
        "lat": 28.5204,
        "lon": 77.2014,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "badarpur": {
        "id": "stop_017",
        "name": "Badarpur Border (T)",
        "lat": 28.4947,
        "lon": 77.3012,
        "zone": "South East Delhi",
        "is_major_hub": True
    },
    "sangam vihar": {
        "id": "stop_018",
        "name": "Hamdard Nagar / Sangam Vihar",
        "lat": 28.5123,
        "lon": 77.2415,
        "zone": "South Delhi",
        "is_major_hub": False
    },
    "kapashera": {
        "id": "stop_019",
        "name": "Kapashera Border",
        "lat": 28.5182,
        "lon": 77.0851,
        "zone": "South West Delhi",
        "is_major_hub": True
    },
    "mahipalpur": {
        "id": "stop_020",
        "name": "Mahipal Pur Village",
        "lat": 28.5441,
        "lon": 77.1264,
        "zone": "South West Delhi",
        "is_major_hub": False
    },
    "andrews ganj": {
        "id": "stop_021",
        "name": "Andrews Ganj",
        "lat": 28.5678,
        "lon": 77.2289,
        "zone": "South Delhi",
        "is_major_hub": False
    },
    "patel nagar": {
        "id": "stop_022",
        "name": "West Patel Nagar",
        "lat": 28.6534,
        "lon": 77.1652,
        "zone": "West Delhi",
        "is_major_hub": False
    },
    "moti nagar": {
        "id": "stop_023",
        "name": "Moti Nagar",
        "lat": 28.6578,
        "lon": 77.1432,
        "zone": "West Delhi",
        "is_major_hub": True
    },
    "rohini sec 9": {
        "id": "stop_024",
        "name": "Rohini Sector 9",
        "lat": 28.7123,
        "lon": 77.1234,
        "zone": "North West Delhi",
        "is_major_hub": False
    },
    "rohini sec 22": {
        "id": "stop_025",
        "name": "Rohini Sector 22 Depot",
        "lat": 28.7289,
        "lon": 77.0876,
        "zone": "North West Delhi",
        "is_major_hub": True
    },
    "dwarka sec 21": {
        "id": "stop_026",
        "name": "Dwarka Sector 21",
        "lat": 28.5524,
        "lon": 77.0583,
        "zone": "South West Delhi",
        "is_major_hub": True
    },
    "dwarka mor": {
        "id": "stop_027",
        "name": "Dwarka Mor",
        "lat": 28.6192,
        "lon": 77.0336,
        "zone": "South West Delhi",
        "is_major_hub": True
    },
    "janakpuri": {
        "id": "stop_028",
        "name": "Janakpuri District Centre",
        "lat": 28.6294,
        "lon": 77.0818,
        "zone": "West Delhi",
        "is_major_hub": True
    },
    "uttam nagar": {
        "id": "stop_029",
        "name": "Uttam Nagar Terminal",
        "lat": 28.6215,
        "lon": 77.0594,
        "zone": "West Delhi",
        "is_major_hub": True
    },
    "tilak nagar": {
        "id": "stop_030",
        "name": "Tilak Nagar",
        "lat": 28.6366,
        "lon": 77.0967,
        "zone": "West Delhi",
        "is_major_hub": False
    },
    "rajouri garden": {
        "id": "stop_031",
        "name": "Rajouri Garden",
        "lat": 28.6492,
        "lon": 77.1215,
        "zone": "West Delhi",
        "is_major_hub": True
    },
    "punjabi bagh": {
        "id": "stop_032",
        "name": "Punjabi Bagh Terminal",
        "lat": 28.6682,
        "lon": 77.1325,
        "zone": "West Delhi",
        "is_major_hub": True
    },
    "azadpur": {
        "id": "stop_033",
        "name": "Azadpur Terminal",
        "lat": 28.7067,
        "lon": 77.1783,
        "zone": "North Delhi",
        "is_major_hub": True
    },
    "gtb nagar": {
        "id": "stop_034",
        "name": "GTB Nagar Metro Station",
        "lat": 28.6978,
        "lon": 77.2064,
        "zone": "North Delhi",
        "is_major_hub": True
    },
    "vishwa vidyalaya": {
        "id": "stop_035",
        "name": "Vishwa Vidyalaya (DU)",
        "lat": 28.6947,
        "lon": 77.2144,
        "zone": "North Delhi",
        "is_major_hub": True
    },
    "chandni chowk": {
        "id": "stop_036",
        "name": "Chandni Chowk",
        "lat": 28.6506,
        "lon": 77.2303,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "red fort": {
        "id": "stop_037",
        "name": "Red Fort (Lal Qila)",
        "lat": 28.6562,
        "lon": 77.2410,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "new delhi station": {
        "id": "stop_038",
        "name": "New Delhi Railway Station",
        "lat": 28.6429,
        "lon": 77.2195,
        "zone": "Central Delhi",
        "is_major_hub": True
    },
    "nizamuddin": {
        "id": "stop_039",
        "name": "Hazrat Nizamuddin Railway Station",
        "lat": 28.5889,
        "lon": 77.2534,
        "zone": "South East Delhi",
        "is_major_hub": True
    },
    "lajpat nagar": {
        "id": "stop_040",
        "name": "Lajpat Nagar",
        "lat": 28.5700,
        "lon": 77.2384,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "south extension": {
        "id": "stop_041",
        "name": "South Extension",
        "lat": 28.5684,
        "lon": 77.2212,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "munirka": {
        "id": "stop_042",
        "name": "Munirka",
        "lat": 28.5583,
        "lon": 77.1729,
        "zone": "South West Delhi",
        "is_major_hub": False
    },
    "hauz khas": {
        "id": "stop_043",
        "name": "Hauz Khas Terminal",
        "lat": 28.5447,
        "lon": 77.2064,
        "zone": "South Delhi",
        "is_major_hub": True
    },
    "malviya nagar": {
        "id": "stop_044",
        "name": "Malviya Nagar",
        "lat": 28.5323,
        "lon": 77.2105,
        "zone": "South Delhi",
        "is_major_hub": False
    },
    "govindpuri": {
        "id": "stop_045",
        "name": "Govindpuri Metro Station",
        "lat": 28.5369,
        "lon": 77.2654,
        "zone": "South East Delhi",
        "is_major_hub": False
    },
    "okhla depot": {
        "id": "stop_046",
        "name": "Okhla Depot",
        "lat": 28.5298,
        "lon": 77.2842,
        "zone": "South East Delhi",
        "is_major_hub": True
    },
    "kalkaji temple": {
        "id": "stop_047",
        "name": "Kalkaji Temple",
        "lat": 28.5482,
        "lon": 77.2603,
        "zone": "South East Delhi",
        "is_major_hub": False
    },
    "mayur vihar 1": {
        "id": "stop_048",
        "name": "Mayur Vihar Phase 1",
        "lat": 28.6042,
        "lon": 77.2941,
        "zone": "East Delhi",
        "is_major_hub": True
    },
    "noida sec 37": {
        "id": "stop_049",
        "name": "Noida Sector 37",
        "lat": 28.5667,
        "lon": 77.3400,
        "zone": "NCR / Noida",
        "is_major_hub": True
    },
    "kalindi kunj": {
        "id": "stop_050",
        "name": "Kalindi Kunj Border",
        "lat": 28.5447,
        "lon": 77.3112,
        "zone": "South East Delhi",
        "is_major_hub": False
    },
    "dilshad garden": {
        "id": "stop_051",
        "name": "Dilshad Garden",
        "lat": 28.6759,
        "lon": 77.3214,
        "zone": "North East Delhi",
        "is_major_hub": True
    }
}

# Authentic Delhi DTC routes (matching real Delhi routes and October-Delhi.csv dataset)
DELHI_ROUTES: Dict[str, Dict[str, Any]] = {
    "85": {
        "route_id": "85",
        "route_number": "85",
        "route_name": "Route 85 (Anand Vihar to Shivaji Stadium / CP)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 8,
        "capacity": 65,
        "corridor": "East-Central",
        "stops": [
            "Anand Vihar ISBT",
            "Preet Vihar",
            "Laxmi Nagar / Shakarpur",
            "ITO (Income Tax Office)",
            "Connaught Place (Shivaji Stadium)"
        ],
        "travel_time_mins": 42,
        "fare_inr": 15
    },
    "73": {
        "route_id": "73",
        "route_number": "73 (AC)",
        "route_name": "Route 73 AC (Anand Vihar to Shivaji Stadium Express)",
        "type": "Low Floor AC (Red/Blue)",
        "is_ac": True,
        "headway_mins": 12,
        "capacity": 60,
        "corridor": "East-Central",
        "stops": [
            "Anand Vihar ISBT",
            "Akshardham Temple",
            "ITO (Income Tax Office)",
            "Connaught Place (Shivaji Stadium)"
        ],
        "travel_time_mins": 36,
        "fare_inr": 25
    },
    "236": {
        "route_id": "236",
        "route_number": "236",
        "route_name": "Route 236 (Anand Vihar to CP via Delhi Gate)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 15,
        "capacity": 65,
        "corridor": "East-Central",
        "stops": [
            "Anand Vihar ISBT",
            "Preet Vihar",
            "Laxmi Nagar / Shakarpur",
            "Delhi Gate",
            "Connaught Place (Shivaji Stadium)"
        ],
        "travel_time_mins": 50,
        "fare_inr": 15
    },
    "740": {
        "route_id": "740",
        "route_number": "740",
        "route_name": "Route 740 (Anand Vihar to CP / Uttam Nagar)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 10,
        "capacity": 65,
        "corridor": "East-West",
        "stops": [
            "Anand Vihar ISBT",
            "Preet Vihar",
            "ITO (Income Tax Office)",
            "Connaught Place (Shivaji Stadium)",
            "Rajiv Chowk (Inner Circle)"
        ],
        "travel_time_mins": 44,
        "fare_inr": 15
    },
    "502": {
        "route_id": "502",
        "route_number": "502 (AC)",
        "route_name": "Route 502 AC (Kashmere Gate to Mehrauli / AIIMS)",
        "type": "Low Floor AC (Red)",
        "is_ac": True,
        "headway_mins": 12,
        "capacity": 60,
        "corridor": "North-South",
        "stops": [
            "Kashmere Gate ISBT",
            "Chandni Chowk",
            "Delhi Gate",
            "Connaught Place (Shivaji Stadium)",
            "AIIMS (Sri Aurobindo Marg)",
            "Mehrauli Terminal"
        ],
        "travel_time_mins": 45,
        "fare_inr": 25
    },
    "429": {
        "route_id": "429",
        "route_number": "429",
        "route_name": "Route 429 (Kashmere Gate to AIIMS via Delhi Gate)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 10,
        "capacity": 65,
        "corridor": "North-South",
        "stops": [
            "Kashmere Gate ISBT",
            "Chandni Chowk",
            "Delhi Gate",
            "ITO (Income Tax Office)",
            "AIIMS (Sri Aurobindo Marg)"
        ],
        "travel_time_mins": 48,
        "fare_inr": 15
    },
    "181": {
        "route_id": "181",
        "route_number": "181",
        "route_name": "Route 181 (Kashmere Gate to Nizamuddin / AIIMS)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 14,
        "capacity": 65,
        "corridor": "North-South",
        "stops": [
            "Kashmere Gate ISBT",
            "Red Fort (Lal Qila)",
            "Delhi Gate",
            "Hazrat Nizamuddin Railway Station",
            "AIIMS (Sri Aurobindo Marg)"
        ],
        "travel_time_mins": 52,
        "fare_inr": 15
    },
    "764": {
        "route_id": "764",
        "route_number": "764",
        "route_name": "Route 764 (Nehru Place to Dhaula Kuan / Najafgarh)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 8,
        "capacity": 65,
        "corridor": "South-West",
        "stops": [
            "Nehru Place Bus Terminal",
            "Lajpat Nagar",
            "AIIMS (Sri Aurobindo Marg)",
            "Dhaula Kuan"
        ],
        "travel_time_mins": 34,
        "fare_inr": 15
    },
    "544": {
        "route_id": "544",
        "route_number": "544",
        "route_name": "Route 544 (Badarpur / Nehru Place to Dhaula Kuan)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 12,
        "capacity": 65,
        "corridor": "South-West",
        "stops": [
            "Nehru Place Bus Terminal",
            "Andrews Ganj",
            "AIIMS (Sri Aurobindo Marg)",
            "Dhaula Kuan"
        ],
        "travel_time_mins": 36,
        "fare_inr": 15
    },
    "724": {
        "route_id": "724",
        "route_number": "724 (AC)",
        "route_name": "Route 724 AC (Nehru Place to Uttam Nagar via Dhaula Kuan)",
        "type": "Low Floor AC (Blue)",
        "is_ac": True,
        "headway_mins": 15,
        "capacity": 60,
        "corridor": "South-West",
        "stops": [
            "Nehru Place Bus Terminal",
            "AIIMS (Sri Aurobindo Marg)",
            "Dhaula Kuan",
            "Uttam Nagar Terminal"
        ],
        "travel_time_mins": 32,
        "fare_inr": 25
    },
    "717A": {
        "route_id": "717A",
        "route_number": "717A",
        "route_name": "Route 717A (Badarpur Border to Saket / Mehrauli)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 6,
        "capacity": 65,
        "corridor": "South-East",
        "stops": [
            "Badarpur Border (T)",
            "Hamdard Nagar / Sangam Vihar",
            "Saket Metro Station",
            "Mehrauli Terminal"
        ],
        "travel_time_mins": 38,
        "fare_inr": 15
    },
    "729": {
        "route_id": "729",
        "route_number": "729",
        "route_name": "Route 729 (Kapashera Border to Badarpur Border)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 12,
        "capacity": 65,
        "corridor": "South-Outer",
        "stops": [
            "Kapashera Border",
            "Mahipal Pur Village",
            "Saket Metro Station",
            "Badarpur Border (T)"
        ],
        "travel_time_mins": 55,
        "fare_inr": 20
    },
    "943": {
        "route_id": "943",
        "route_number": "943",
        "route_name": "Route 943 (Karol Bagh to Anand Vihar ISBT)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 14,
        "capacity": 65,
        "corridor": "West-East",
        "stops": [
            "Karol Bagh (Gurudwara Road)",
            "Connaught Place (Shivaji Stadium)",
            "ITO (Income Tax Office)",
            "Laxmi Nagar / Shakarpur",
            "Anand Vihar ISBT"
        ],
        "travel_time_mins": 50,
        "fare_inr": 15
    },
    "990": {
        "route_id": "990",
        "route_number": "990",
        "route_name": "Route 990 (Rohini to Shivaji Stadium via Karol Bagh)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 10,
        "capacity": 65,
        "corridor": "NorthWest-Central",
        "stops": [
            "Rohini Sector 22 Depot",
            "Rohini Sector 9",
            "Punjabi Bagh Terminal",
            "Karol Bagh (Gurudwara Road)",
            "Connaught Place (Shivaji Stadium)"
        ],
        "travel_time_mins": 52,
        "fare_inr": 20
    },
    "405": {
        "route_id": "405",
        "route_number": "405",
        "route_name": "Route 405 (Badarpur Border to Kashmere Gate ISBT)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 10,
        "capacity": 65,
        "corridor": "South-North",
        "stops": [
            "Badarpur Border (T)",
            "Okhla Depot",
            "Sarai Kale Khan ISBT",
            "Delhi Gate",
            "Kashmere Gate ISBT"
        ],
        "travel_time_mins": 58,
        "fare_inr": 20
    },
    "OMS": {
        "route_id": "OMS",
        "route_number": "OMS (Ring Road)",
        "route_name": "Outer Mudrika Seva (Ring Road Circular)",
        "type": "Standard Non-AC (Green)",
        "is_ac": False,
        "headway_mins": 7,
        "capacity": 65,
        "corridor": "Ring-Road",
        "stops": [
            "Dhaula Kuan",
            "AIIMS (Sri Aurobindo Marg)",
            "Lajpat Nagar",
            "Sarai Kale Khan ISBT",
            "ITO (Income Tax Office)",
            "Kashmere Gate ISBT"
        ],
        "travel_time_mins": 45,
        "fare_inr": 15
    }
}
