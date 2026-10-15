# AeroAI — Comprehensive Model Evaluation & Benchmark Report

> **Dataset**: U.S. DOT Bureau of Transportation Statistics (BTS) Airline On-Time Performance + NOAA/ASOS Surface Weather  
> **Evaluation Methodology**: Strict Out-of-Time Holdout Partition (Months 10–12, 2013)  
> **Test Records**: 82,609 flights (63,637 On-Time vs. 18,972 Delayed)  
> **Target Definition**: Binary Arrival Delay (>= 15 minutes)  
> **Class Base Rate**: 22.97% Delayed / 77.03% On-Time  
> **Evaluation Timestamp**: 2026-10-14T20:20:06Z  

---

## 1. Executive Summary & Model Comparison

Three candidate model architectures were trained strictly on Months 1–9 and evaluated on the out-of-time test partition (Months 10–12). Weather observations (NOAA/ASOS surface observations) are synchronized by origin airport and scheduled departure hour to eliminate data leakage.

| Architecture | ROC-AUC | PR-AUC (Average Precision) | Brier Score | Accuracy (@ 0.50) | Precision (@ 0.50) | Recall (@ 0.50) | F1 Score (@ 0.50) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Logistic Regression)** | 0.6321 | 0.3470 | 0.1955 | 0.7706 | 0.9259 | 0.0013 | 0.0026 |
| **Random Forest (100 Trees)** | **0.6929** | 0.4244 | **0.1614** | 0.7778 | 0.6805 | 0.0614 | 0.1126 |
| **XGBoost (150 Trees)** | 0.6876 | **0.4257** | 0.1656 | **0.7798** | 0.6589 | **0.0854** | **0.1513** |

---

## 2. Operational Threshold Analysis (Calibrated Threshold = 0.25)

Because flight delay is naturally imbalanced (~23.0% delayed), evaluating models at the standard 0.50 decision threshold results in high precision on rare events but low operational recall. In commercial flight operations, a calibrated decision threshold of 0.25 (matching the empirical prior base rate) yields optimal operational utility for proactive passenger rebooking.

| Architecture | Decision Threshold | Accuracy | Precision | Recall | F1 Score | True Positives (Caught Delays) | False Alarms (FP) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline (Logistic Regression)** | 0.25 | 0.7723 | 0.5516 | 0.0462 | 0.0853 | 877 | 713 |
| **Random Forest (100 Trees)** | **0.25** | **0.7369** | **0.4272** | **0.4275** | **0.4274** | **8,111** | 10,876 |
| **XGBoost (150 Trees)** | 0.25 | 0.7677 | 0.4907 | 0.3088 | 0.3791 | 5,859 | **6,080** |

---

## 3. Confusion Matrix Breakdown

### 3.1 Random Forest (Best Discriminative Ranker: ROC-AUC = 0.6929)
- **Standard Threshold (Threshold = 0.50)**:
  ```
  Predicted ->    On-Time (0)   Delayed (1)
  Actual On-Time:     63090           547  (Specificity: 99.14%)
  Actual Delayed:     17807          1165  (Sensitivity: 6.14%)
  ```
- **Operational Threshold (Threshold = 0.25)**:
  ```
  Predicted ->    On-Time (0)   Delayed (1)
  Actual On-Time:     52761         10876  (Specificity: 82.91%)
  Actual Delayed:     10861          8111  (Sensitivity: 42.75%)
  ```

### 3.2 XGBoost (Best PR-AUC = 0.4257)
- **Standard Threshold (Threshold = 0.50)**:
  ```
  Predicted ->    On-Time (0)   Delayed (1)
  Actual On-Time:     62798           839
  Actual Delayed:     17351          1621
  ```
- **Operational Threshold (Threshold = 0.25)**:
  ```
  Predicted ->    On-Time (0)   Delayed (1)
  Actual On-Time:     57557          6080
  Actual Delayed:     13113          5859
  ```

---

## 4. SHAP Feature Attribution & Interpretability

To explain predictions at inference time without treating correlations as causal relationships, AeroAI integrates **TreeSHAP** (`shap.TreeExplainer`) into the best-performing model.

### Key Guidelines for SHAP Interpretability:
1. **Non-Causal Grounding**: SHAP attributions quantify the additive marginal contribution of each observed feature toward pushing the model's output above or below the empirical training base rate (23.0%). They must **not** be presented as root causes.
2. **Operational Terminology**: All explanations utilize standard operational phrasing:  
   `"These features contributed most to the model's prediction."`
3. **Primary Attributed Features**:
   - **Meteorological Indicators**: Surface visibility (`visib`), relative humidity (`humid`), precipitation rate (`precip`), and wind speed (`wind_speed`).
   - **Temporal Congestion**: Departure hour delay rate (`hour_delay_rate`, `sched_dep_hour`) reflecting terminal airspace saturation during afternoon/evening banks.
   - **Network Effects**: Origin airport congestion baseline (`origin_delay_rate` at `EWR`/`LGA`/`JFK`) and carrier operational reliability (`carrier_delay_rate`).
