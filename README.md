# BusBidder
Final project for ACIT4420


## Repository & Package Layout

```
BusBidder
│
├── main.py         # Main entry point
├── tests.py        # Automated unit test suite (14 cases)
├── models.py       # Core domain entities
├── exceptions.py   # Custom exceptions
├── validators.py   # Regex pattern matchers and range guards
├── loader.py       # CSV parser and type converter
├── filters.py      # Hard constraint filtering engine
├── scoring.py      # MCDA Min-Max feature normalizer (0-100 scale)  and weighted aggregate scorer
├── recommender.py  # Readable recommendation generator and preset traveler profiles
├── booking.py      # Inventory, regex booking-reference generator, and file persistence 
├── registry.py     # Decorator-based plugin registry (Metaprogramming)
│
├── data/               # Input CSV datasets
│   ├── companies.csv   # Company profiles
│   ├── offers.csv      # Journey offers dataset
│
└── output/         # Auto-created output directory for generated reports, logs, and persistant state
    ├── recommendation_report.txt   # Readable recommendation report
    ├── rejected_records.txt        # Error triage log for invalid or corrupt CSV rows
    ├── bookings.csv                # Persistent CSV ledger of confirmed reservation
    └── booking_receipts.txt        # A formatted receipt for confirmed bookings
```

## Installation & Instructions
### Prerequisites
* Python 3.8 or higher
* No external third-party packages required

> [!NOTE]
> On systems where ```python3``` is not aliased, use ```python main.py [...]``` instead

### Instructions
1. Clone the repository
```
  git clone https://github.com/Funeralpyre-git/BusBidder
  cd /BusBidder
  ```
1.1. Verify that ```companies.csv``` and ```offers.csv``` exist inside the ```data/``` directory:**
  ```
  BusBidder/
  └── data/
      ├── companies.csv
      └── offers.csv
  ```
2. Execute the Main Application
Run the main application using python3 (or python)

2.1. Default Execution (Budget Traveler Profile)
```
python3 main.py --companies data/companies.csv --offers data/offers.csv --profile budget --output output
```
2.2. Running other traveler profiles
```
# Business Traveler Profile (Prioritizes travel speed and ticket flexibility)
python3 main.py --companies data/companies.csv --offers data/offers.csv --profile business --output output

# Eco-Conscious Traveler Profile (Prioritizes low CO2 emissions and eco-certified carriers
python3 main.py --companies data/companies.csv --offers data/offers.csv --profile eco --output output

# Comfort & Flexibility Tourist Profile (Prioritizes customer ratings and refundable terms)
python3 main.py --companies data/companies.csv --offers data/offers.csv --profile comfort --output output
```
### Running the Automated Unit Test Suite
The project includes an automated test suite implemented in tests.py using Python's standard `unittest` framework
```
python3 -m unittest tests.py
```
***Test Suite Covers:***
* `TestDomainModels`: Verifies attribute bounds, seat decrements, and overbooking exception handling
* `TestValidators`: Tests regex matchers (`^BB-[A-Z]{3}-\d{6}$`, `^COMP-...`, `OFF-...`) against valid and malformed identifiers
* `TestFilters:` Tests budged, window, destination, seat, and transfer constraint short-circuits
* `TestScoringEngine`: Validates Min-Max 0.0-100.0 normalization (lower vs higher is better) and zero-division fallbacks
* `TestLoaderAndRejectedRecords`: Verifies error triage logging when encountering corrupt CSV rows
* `TestBookingManager`: Verifies capacity decrements, regex reference creation, and CSV persistence using temporary test directories

***Expected Test Output***
```
..............
----------------------------------------------------------------------
Ran 14 tests in 0.020s

OK
```

## Data Files & Schema Formats
`data/companies.csv:`
```
company_id,name,profile_type,fleet_rating,eco_certified
COMP-SOL01,SolRuta,low_cost,4.1,false
COMP-CAM02,Camino Express,express,4.7,false
COMP-COS03,CostaLink,coastal,4.3,false
COMP-VER04,VerdeBus,eco,4.8,true
COMP-NOC05,NocheVia,overnight,4.0,false
```
`data/offers.csv:`
```
offer_id,company_id,origin,destination,travel_date,departure_time,arrival_time,duration_minutes,price,transfers,available_seats,customer_rating,co2_emissions_kg,is_changeable,is_refundable,luggage_kg,change_fee_eur
OFF-MAD-BCN-101,COMP-SOL01,Madrid,Barcelona,2026-07-12,08:00:00,14:30:00,390,29.50,0,15,4.2,19.5,false,false,20.0,0.0
OFF-MAD-BCN-102,COMP-CAM02,Madrid,Barcelona,2026-07-12,09:15:00,14:45:00,330,48.00,0,20,4.8,18.0,true,true,25.0,0.0
OFF-MAD-BCN-103,COMP-VER04,Madrid,Barcelona,2026-07-12,10:00:00,16:15:00,375,36.00,0,12,4.7,11.2,true,false,20.0,5.0
OFF-MAD-VAL-104,COMP-COS03,Madrid,Valencia,2026-07-12,08:30:00,12:30:00,240,22.00,0,8,4.3,13.0,false,false,20.0,0.0
OFF-MAD-AGP-105,COMP-NOC05,Madrid,Malaga,2026-07-12,23:00:00,06:00:00,420,32.00,0,18,4.1,16.5,true,false,20.0,10.0
OFF-MAD-BCN-999,COMP-SOL01,Madrid,Barcelona,2026-07-12,12:00:00,18:00:00,360,fast,0,10,4.0,15.0,false,false,20.0,0.0
```
> [!note]
> Row 6 of `data/offers.csv` contains `price=fast` to test error triage logging to `rejected_records.txt`

### Output Files & Examples
1. `output/recommendation_report.txt`

***Contains the complete decision rationale formatted to be readable by humans:***
```
=================================================
     BUSBIDDER SPAIN - RECOMMENDATION REPORT     
=================================================
Traveler Profile  : Sofia (Comfort)
Route             : Madrid -> Barcelona
Travel Window     : 2026-07-12 to 2026-07-15
-------------------------------------------------
RECOMMENDED OFFER  : OFF-MAD-BCN-102
Carrier            : Camino Express (express)
Composite Score    : 100.0/100.0
Fare Price         : EUR 48.00
Departure & Arrival: 09:15 -> 14:45 (330 mins
-------------------------------------------------
DECISION RATIONALE:
    'OFF-MAD-BCN-102' operated by Camino Express is recommended as the top match for Sofia (Comfort) with a total composite score of 100.0/100. The primary preference driver for this profile was 'flexibility' (weight 40%), where this offer scored 100.0/100. 
-------------------------------------------------
```
2. `output/rejected_records.txt`

***Log file containing corrupt or invalid CSV rows encountered during data loading:***
```
===========================================================
           BUSBIDDER SPAIN - REJECTED RECORDS LOG          
===========================================================

[offers.csv: Row 7] Field 'offer_data' rejected: could not convert string to float: 'fast'
```
3. `output/bookings.csv`

***Persistent ledger appending confirmed reservations with regex-validated booking codes:***
```
booking_reference,offer_id,company_id,company_name,traveler_name,origin,destination,traveler_date,departure_time,num_seats,total_price_eur,status,booking_timestamp
BB-MAD-865031,OFF-MAD-BCN-101,COMP-SOL01,SolRuta,Ana (Budget),Madrid,Barcelona,2026-07-12,08:00,1,29.50,CONFIRMED,2026-11-15 02:18:04
BB-MAD-984535,OFF-MAD-BCN-102,COMP-CAM02,Camino Express,Carlos (Business),Madrid,Barcelona,2026-07-12,09:15,1,48.00,CONFIRMED,2026-11-15 02:18:15
BB-MAD-176219,OFF-MAD-BCN-103,COMP-VER04,VerdeBus,Diego (Eco),Madrid,Barcelona,2026-07-12,10:00,1,36.00,CONFIRMED,2026-11-15 02:18:19
BB-MAD-282531,OFF-MAD-BCN-103,COMP-VER04,VerdeBus,Diego (Eco),Madrid,Barcelona,2026-07-12,10:00,1,36.00,CONFIRMED,2026-11-15 02:43:03
BB-MAD-897052,OFF-MAD-BCN-102,COMP-CAM02,Camino Express,Sofia (Comfort),Madrid,Barcelona,2026-07-12,09:15,1,48.00,CONFIRMED,2026-11-16 05:41:20
```
4. `output/booking_receipts.txt`

***Formatted receipts for auditability and verification:***
```
--- BOOKING CONFIRMATION: BB-MAD-282531 ---
Passenger         : Diego (Eco)
Route             : Madrid -> Barcelona
Carrier           : VerdeBus (eco)
Date & Departure  : 2026-07-12 at 10:00
Seats Reserved    : 1 (Total: EUR 36.00)
Flexibility       : Changeable=True, Refundable=False
Status            : CONFIRMED
------------------------------------------------
```