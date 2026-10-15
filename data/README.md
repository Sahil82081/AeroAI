# AeroAI — Aviation Datasets & Ground Truth Data

> **Subsystem**: AeroAI ML & Data Engineering  
> **Primary Dataset**: U.S. Bureau of Transportation Statistics (BTS) Airline On-Time Performance Data  
> **Storage Location**: `data/flights/`  
> **Format**: Compressed CSV (`flights.csv.zip`) alongside reference tables (`airlines.csv`, `airports.csv`, `weather.csv`)

---

## 1. Dataset Source & Attribution

- **Source**: U.S. Department of Transportation (DOT) Bureau of Transportation Statistics (BTS)
- **Database**: Airline On-Time Performance Data (TranStats)
- **Distribution Package**: `nycflights13` (Python/R BTS data package maintained by Hadley Wickham & community)
- **Source URL**: [https://www.transtats.bts.gov/DatabaseInfo.asp?DB_URL=Mode_ID=1&Mode_Desc=Aviation](https://www.transtats.bts.gov/DatabaseInfo.asp?DB_URL=Mode_ID=1&Mode_Desc=Aviation)
- **Licensing & Usage**: U.S. Federal Government Public Domain work under **17 U.S.C. § 105**. Free for academic, personal, research, and commercial applications without copyright restrictions.

---

## 2. Dataset Overview & Dimensions

- **Temporal Coverage**: Full calendar year 2013 (`2013-01-01` to `2013-12-31`).
- **Raw Row Count**: **336,776** commercial flights.
- **Cleaned Row Count (Valid Arrival Records)**: **327,346** flights (9,430 cancelled/diverted flights missing arrival times excluded for delay classification).
- **Origin Airports**: All 3 major New York metropolitan hubs:
  - `EWR`: Newark Liberty International Airport (120,835 flights)
  - `JFK`: John F. Kennedy International Airport (111,279 flights)
  - `LGA`: LaGuardia Airport (104,662 flights)
- **Destination Airports**: **104** commercial airports across North America.
- **Operating Carriers**: **16** major airlines and regional carriers (`UA`, `B6`, `EV`, `DL`, `AA`, `MQ`, `US`, `WN`, `VX`, `FL`, `AS`, `9E`, `F9`, `HA`, `YV`, `OO`).

---

## 3. Important Columns & Schema

| Column Name | Type | Temporal Status | Role in Pipeline | Description |
| :--- | :--- | :--- | :--- | :--- |
| `year`, `month`, `day` | Integer | Scheduled (Pre-flight) | Feature & Split | Scheduled calendar date of departure. |
| `sched_dep_time` | Integer | Scheduled (Pre-flight) | Feature | Scheduled departure time in local HHMM format (e.g., `515` = 05:15 AM). |
| `sched_arr_time` | Integer | Scheduled (Pre-flight) | Feature | Scheduled arrival time in local HHMM format (e.g., `819` = 08:19 AM). |
| `carrier` | String | Scheduled (Pre-flight) | Feature | Two-letter IATA carrier code. |
| `flight` | Integer | Scheduled (Pre-flight) | Identifier | Scheduled flight number. |
| `origin` | String | Scheduled (Pre-flight) | Feature | Three-letter IATA departure airport code. |
| `dest` | String | Scheduled (Pre-flight) | Feature | Three-letter IATA destination airport code. |
| `distance` | Integer | Scheduled (Pre-flight) | Feature | Scheduled flight route distance in statute miles. |
| `hour`, `minute` | Integer | Scheduled (Pre-flight) | Feature | Scheduled departure hour and minute. |
| `time_hour` | Timestamp | Scheduled (Pre-flight) | Validation / Split | Scheduled departure timestamp in ISO 8601 UTC. |
| `arr_delay` | Float | Post-flight (Outcome) | **Ground Truth Target** | Arrival delay in minutes. Positive = late, negative = early. |
| `dep_time` | Float | Post-flight (Outcome) | **STRICTLY EXCLUDED** | Actual wheel-off / gate departure time (data leakage risk). |
| `dep_delay` | Float | Post-flight (Outcome) | **STRICTLY EXCLUDED** | Departure delay in minutes (data leakage risk). |
| `arr_time` | Float | Post-flight (Outcome) | **STRICTLY EXCLUDED** | Actual landing / gate arrival time (data leakage risk). |
| `air_time` | Float | Post-flight (Outcome) | **STRICTLY EXCLUDED** | Actual airborne duration in minutes (data leakage risk). |

---

## 4. Target Definition

The target variable for binary classification follows the standard aviation industry and U.S. Federal Aviation Administration (FAA) / Bureau of Transportation Statistics (BTS) definition:

$$\text{Delayed} = \begin{cases} 1 & \text{if } \text{Arrival Delay} \ge 15 \text{ minutes} \\ 0 & \text{if } \text{Arrival Delay} < 15 \text{ minutes} \end{cases}$$

### Class Distribution & Imbalance
- **On-Time ($y = 0$)**: 247,249 flights (**75.53%**)
- **Delayed ($y = 1$)**: 80,097 flights (**24.47%**)
- **Class Imbalance Ratio**: $\approx 3.09 : 1$ (negative to positive)

---

## 5. Strict Prevention of Data Leakage

In real-world flight operations, predictions are made **before departure** (e.g., at booking, 24h prior, or 2h before scheduled takeoff).

### Strictly Excluded Post-Flight Variables
1. `dep_delay`: Contains ~85% of the arrival delay signal. Using departure delay to predict arrival delay pre-flight is invalid leakage.
2. `dep_time`: Reveals actual departure delay.
3. `arr_time`: Known only after landing.
4. `air_time`: Known only after arrival.
5. `taxi_in`, `taxi_out`: Known only after ground maneuvers.

### Strictly Allowed Pre-Flight Features
All features utilized in `AeroAI` are derived from information known prior to gate departure:
- Scheduled departure hour, minute, and time-of-day blocks.
- Cyclical calendar transforms (sine/cosine representations of hour, day of week, and month).
- Route distance and scheduled elapsed flight duration.
- Historical airline, origin, and destination delay baselines computed **strictly from the training partition** to prevent lookahead bias.

---

## 6. Preprocessing & Feature Pipeline

1. **Missing Target Handling**: Flights with `NaN` in `arr_delay` (9,430 rows, ~2.8%) represent cancelled or diverted flights and are excluded from the delay duration classification task.
2. **Missing Feature Handling**: Numerical missing values are imputed using the median from the training partition. Categorical missing values or unseen categories are assigned a global fallback prior.
3. **Out-of-Time Target Encoding**: Historical delay probabilities for airlines, destination airports, origin hubs, and departure hours are calculated strictly on the training partition (`months 1–9`) and mapped onto test/inference records.
4. **Encoding & Scaling**: Categorical features (`carrier`, `origin`) are one-hot encoded (`OneHotEncoder(handle_unknown='ignore')`). Continuous features are scaled using `StandardScaler`.

---

## 7. Time-Based Train / Test Split

To simulate genuine future prediction without lookahead data leakage, a **chronological time-based split** is enforced:

- **Training Partition**: January 1, 2013 to September 30, 2013 (Months 1–9)
  - Records: **244,737** flights
  - Delayed: 61,128 flights (**24.98%**)
  - On-Time: 183,609 flights (75.02%)
- **Test Partition**: October 1, 2013 to December 31, 2013 (Months 10–12)
  - Records: **82,609** flights
  - Delayed: 18,969 flights (**22.97%**)
  - On-Time: 63,640 flights (77.03%)

---

## 8. Limitations & Scope

---

## 9. Weather Intelligence Dataset (Stage 3 Integration)

### 9.1 Data Sources & Provenance
AeroAI integrates two complementary weather data sources through a decoupled provider abstraction (`WeatherProvider`):

1. **NOAA ASOS Ground Surface Observations (`HistoricalWeatherProvider`)**:
   - **Source**: Automated Surface Observing System (ASOS) stations co-located at primary commercial airports, distributed via NOAA / `nycflights13`.
   - **Storage**: `data/flights/weather.csv`
   - **Dimensions**: **26,115** hourly airport observations across the NYC terminal area (`EWR`, `JFK`, `LGA`) spanning all 365 days of 2013.
   - **Match Rate**: **99.53%** successful exact hourly match against the flight database.
   - **Licensing**: U.S. National Oceanic and Atmospheric Administration (NOAA) Public Domain.

2. **Open-Meteo REST API (`LiveWeatherProvider`)**:
   - **Source**: High-resolution numerical weather prediction models (NOAA GFS / DWD ICON / ECMWF).
   - **Endpoint**: `https://api.open-meteo.com/v1/forecast`
   - **Coverage**: Worldwide airport coordinates (`EWR`, `JFK`, `LGA`, `ORD`, `LAX`, `BOM`, `DEL`, `BLR`, etc.).
   - **Performance**: Zero-authentication, sub-second latency, wrapped with a 10-minute in-memory TTL cache and 4.0-second timeout protection.

3. **Deterministic Fallback (`MockWeatherProvider`)**:
   - Zero-network fallback providing realistic observations across predefined meteorological conditions (`CLEAR`, `FOG`, `THUNDERSTORM`, `WINTER_STORM`).

### 9.2 Weather Features Extracted & Derived
| Feature Name | Type | Unit | Operational Aviation Impact |
| :--- | :--- | :--- | :--- |
| `temp` | Continuous | °F | Air density, engine thrust, de-icing threshold. |
| `dewp` | Continuous | °F | Dew point temperature; indicator of cloud ceiling and moisture. |
| `humid` | Continuous | % | Relative humidity; fog and carburetor/wing icing potential. |
| `wind_speed` | Continuous | mph | Crosswind and headwind components affecting runway acceptance rate. |
| `precip` | Continuous | inches/hr | Surface water accumulation, runway braking action degradation. |
| `pressure` | Continuous | mb | Atmospheric sea-level pressure; altimeter setting and barometric tendencies. |
| `visib` | Continuous | miles | Surface visibility; determines VFR vs. IFR instrument approach procedures. |
| `is_fog` | Binary (0/1) | Flag | Low visibility obstruction (`visib < 3.0` miles). |
| `is_high_wind`| Binary (0/1) | Flag | Crosswind / gust hazard (`wind_speed > 25.0` mph). |
| `is_freezing` | Binary (0/1) | Flag | Ground icing conditions (`temp <= 32.0` °F and `precip > 0`). |
| `has_precip`  | Binary (0/1) | Flag | Active surface precipitation (`precip > 0.0`). |

### 9.3 Temporal & Spatial Alignment (Leakage Prevention)
To strictly prevent data leakage and lookahead bias:
1. **Alignment Key**: Weather observations are fused strictly on:
   $$\text{Key} = \Big(\text{Origin Airport}, \text{Year}, \text{Month}, \text{Day}, \text{Scheduled Departure Hour}\Big)$$
2. **Pre-Flight Observability**: Only weather observations recorded **at or prior to scheduled departure** at the origin airport are injected into feature vector $X$.
3. **No Destination Arrival Weather**: Arrival destination weather at time of scheduled landing is not used because real-world gate departures are decided based on origin conditions, Ground Delay Programs (GDP), and departure airport acceptance rates.
4. **No Actual Departure Information**: Flight delay actuals are never used to look up weather.

### 9.4 Missing Data & Graceful Fallback Strategy
If weather is unavailable (e.g. airport station offline, network disconnection, or missing observation):
- Numerical weather features are imputed using median values computed **strictly from the training partition** (`temp=55.4°F`, `humid=62.5%`, `visib=10.0 mi`, `wind_speed=10.36 mph`, `precip=0.0 in`, `pressure=1017.6 mb`).
- Operational severe flags default to safe non-disrupted states (`0`).
- The prediction response sets `weather_available: false` and explicitly notes the fallback state in `weather_intelligence.source`, ensuring zero prediction crashes.

