# Football AI Platform — Beginner Guide (Terms, Workflow, Tech)

This document explains **AI and ML words in plain language**, then describes **how this project works**, **what each part does**, and **why we built it that way**.

---

## Part A — AI & ML terms (simple explanations)

**Artificial Intelligence (AI)**  
Software that can make useful decisions or outputs from data. Here, “useful” means things like match probabilities or short explanations — not magic; it is built from data + rules + models.

**Machine Learning (ML)**  
A type of AI where the computer **learns patterns from historical examples** instead of you writing every rule by hand. You show it many past matches and outcomes; it adjusts internal numbers (“parameters”) to predict better on new matches.

**Model**  
The trained program (or mathematical object) that turns **inputs** (features) into **outputs** (predictions). Examples: XGBoost model, Poisson goals model, Elo rating.

**Training**  
The phase where the model **learns from old data**. You feed features + known results (“labels”). The model updates until it fits the past data well — but not *too* well (see overfitting).

**Inference (prediction)**  
Using a **finished** model on a **new** match to get probabilities before the match is played.

**Features**  
The **inputs** the model sees: numbers that describe situation and form, e.g. “goals scored in last 5 games”, “rest days”, “table pressure”. Good features matter more than a fancy model name.

**Feature engineering**  
Designing and computing those inputs carefully: rolling averages, home vs away splits, fatigue, motivation, etc. This is where much of the “intelligence” of the system lives.

**Labels / targets**  
The **true outcomes** we want to predict, used only in training and evaluation: e.g. final score, win/draw/loss, over/under. Never use future match information as a feature — that would be cheating (leakage).

**Dataset**  
A table (or files) where each row is one match (or one example) with features + labels for training.

**Time-series aware training**  
Football data is ordered in time. We train on **older** matches and test on **newer** matches so the test simulates the real world (you never predict the past using the future).

**Train / validation / test split**  
- **Train**: data the model learns from.  
- **Validation**: data used to tune settings without peeking at the final test.  
- **Test**: final check on the newest period — closest to “real deployment”.

**Overfitting**  
The model memorizes noise in training data and gets worse on new matches. We fight it with simpler models, regularization, good splits, and better features.

**Data leakage**  
Accidentally giving the model **information it would not have at prediction time** (e.g. final score, or standings updated after the match). The model looks accurate in tests but fails in production.

**Generalization**  
How well the model works on **new** matches and leagues it was not overfit to.

**Memorization (e.g. team names)**  
If the model mainly learns “Team X always wins” instead of **situations** (fatigue, style, pressure), it breaks when squads change. We prefer **dynamic stats and context** over raw names as strong signals.

**XGBoost / LightGBM**  
Popular **gradient boosting** libraries: many small decision trees combined; strong for tabular data (tables of features). Fast and often very accurate for sports ML when features are good.

**Poisson model (goals)**  
A statistical approach that models **how many goals** each side might score using rate parameters; good for scorelines and over/under thinking.

**Elo rating**  
A number representing **team strength** that goes up/down after each result; useful as a simple, interpretable strength signal.

**Ensemble**  
Combining several models (e.g. Elo + Poisson + XGBoost) into one final probability — often more stable than any single model.

**Calibration**  
Making predicted probabilities **match real frequencies** (e.g. when the model says 60% win, wins happen ~60% of the time over many cases).

**LLM (Large Language Model)**  
A text model (e.g. via Ollama) used here **only** for explanations and readable insights — **not** as the main number engine for win probabilities.

**Feature store**  
A structured place (often database tables) where **versioned feature snapshots** live so training and live predictions use the **same definitions**.

**Pipeline**  
Automated steps: ingest data → clean → compute features → validate → train or predict.

**Rolling window**  
Statistics computed over the **last N matches** (e.g. last 5), updating as time moves forward.

**Exponentially weighted (EWMA)**  
Recent matches count **more** than old matches in an average — good for “momentum”.

---

## Part B — General workflow of this project

High level:

1. **Collect** match schedules, results, stats, injuries, standings (from providers or manual pipelines).  
2. **Store** everything in **PostgreSQL** (historical, never deleted for research and retraining).  
3. **Compute features** at a fixed time before kickoff (no future data).  
4. **Save feature snapshots** (feature store) so training and production match.  
5. **Train ML models** on old seasons; validate with time-based splits.  
6. **Serve predictions** via **FastAPI** to the **Flutter** app.  
7. **Optional**: **Ollama** turns structured outputs into human-readable explanations.

```text
Data sources → PostgreSQL → Feature jobs (Celery) → Models → FastAPI → Flutter app
                                      ↓
                                   Redis (cache)
```

---

## Part C — Technologies applied (what each is for)

| Technology | Role |
|------------|------|
| **Flutter** | Mobile app (iOS/Android): leagues, fixtures, match detail, charts. |
| **FastAPI** | Backend HTTP API: returns fixtures, predictions, insights metadata. |
| **PostgreSQL** | Permanent storage: matches, stats, standings snapshots, features, predictions. |
| **SQLAlchemy** | Python layer to talk to PostgreSQL safely and maintainably. |
| **Redis** | Fast cache for hot reads (fixtures, latest predictions). |
| **Celery** | Background workers: heavy feature rebuilds, training exports, emails later. |
| **Python ML stack** (pandas, numpy, scikit-learn, XGBoost, LightGBM) | Training, evaluation, feature tables, ensembles. |
| **Ollama + Qwen/Llama** | Offline/local LLM for explanations only. |

---

## Part D — Main sections of the system (what / how / why)

### 1) Database (PostgreSQL)

- **What**: Tables for leagues, seasons, teams, matches, per-match stats, standings snapshots, injuries, feature snapshots, predictions.  
- **How**: SQL schema + migrations; append-only history where possible.  
- **Why**: Single source of truth, reproducible ML, audit trail.

### 2) Feature engineering

- **What**: Rolling form, home/away, fatigue, motivation from standings, tactical proxies, discipline, Elo, etc.  
- **How**: Batch jobs read only data **before kickoff**; output one **feature vector per match**.  
- **Why**: Models learn **situations**, not lucky one-off labels.

### 3) Feature store (`match_feature_sets`, definitions)

- **What**: Saved feature JSON (or columns) per `match_id` + **pipeline version**.  
- **How**: After each pipeline run, insert/update immutable rows for audit.  
- **Why**: Training and inference stay aligned; you can replay old matches.

### 4) ML training

- **What**: Time-based splits, metrics, saved model files, registry in DB.  
- **How**: Export Parquet or use `training_examples`; train XGBoost/LightGBM + baselines.  
- **Why**: Controlled quality before users see probabilities.

### 5) Inference API

- **What**: Endpoint like “prediction for match X”.  
- **How**: Load features → model → calibrated probabilities → JSON response.  
- **Why**: Fast, stable contract for the Flutter app.

### 6) LLM explanation layer

- **What**: Short narrative + bullet insights.  
- **How**: Send **structured facts + probabilities** to Ollama; forbid inventing stats.  
- **Why**: UX and trust without letting the LLM “guess” the score.

---

## Part E — What this project is (one paragraph)

It is a **data-driven football prediction platform**: historical and pre-match data live in **PostgreSQL**; **features** describe context (form, fatigue, motivation, tactics, discipline); **ML models** output probabilities; **FastAPI** serves them; **Flutter** shows them; an **LLM** may **explain** results in natural language. The architecture is modular so you can improve **data** and **features** without rewriting the whole app.

---

## Part F — How you work on it (beginner path)

1. Run database migrations (create tables).  
2. Ingest a small sample league season into `matches` + `team_match_stats`.  
3. Implement one feature family (e.g. last-5 form) and write to `match_feature_sets`.  
4. Train a simple baseline (Elo or logistic regression) with time split.  
5. Expose `/predictions/{match_id}` in FastAPI reading stored features.  
6. Connect Flutter to that endpoint.

---

## Part G — Why we do it this way (principles)

- **No leakage**: honest predictions in production.  
- **Reproducibility**: same inputs → same features → comparable models.  
- **Scalability**: workers + cache + append-only history.  
- **Separation**: numbers from ML, words from LLM.  
- **Beginner-friendly growth**: schema and pipelines first; complex deep learning only if needed.

---

## Related files in this repo

- `general_doc.txt` — archived **technical architecture** (feature categories, schema rationale, risks).  
- `db/schema/001_core_schema.sql` — **PostgreSQL tables and indexes** to create the database.  
- Application code under `app/` (FastAPI routes and services).

For detailed SQL, open `db/schema/001_core_schema.sql` and run it against your PostgreSQL instance (after creating an empty database).
