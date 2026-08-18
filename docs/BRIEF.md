# Project Dockside

*A London cycle hire availability pipeline · ELT*

**Team:** Talk Data To Me — Martins, Ogbo, Dre
**Kickoff:** Wednesday 19 August 2026
**Demo day:** Tuesday 1 September 2026

Latent Ed | Data Engineering Programme | Cohort 2026

---

## 1. The brief

Wheelhouse is a small mobility consultancy advising London boroughs on cycle infrastructure. The question they get asked most often is also the one they can answer least well: *where should we add docking capacity?*

Right now they answer it with anecdote. A councillor says the station outside their office is always empty at nine in the morning, and that becomes the evidence base.

TfL publishes live availability for every docking station in London — but only live. There is no history. Nobody is keeping it. Which means the moment you start recording it, you have something nobody else has.

Wheelhouse want to know which stations run dry in the morning peak, which fill to capacity in the evening, and how much advertised capacity is silently lost to broken docks.

> ★ **Your pipeline's value is entirely in what it accumulates**
> A day not collected is a day gone permanently. This is the only project in the programme where a missed run costs you something you cannot recover.

---

## 2. Defining 'done'

- Raw API responses are preserved in S3, partitioned by snapshot timestamp
- Snapshots land in a Snowflake bronze layer as semi-structured data, untransformed
- A silver layer resolves each snapshot into typed, columnar rows — one row per station per snapshot
- A station dimension and an availability fact are derived and separated in dbt
- A gold layer answers Wheelhouse's questions directly
- Re-running any load creates no duplicate snapshots
- dbt tests cover uniqueness, referential integrity and null constraints on silver and gold
- Runs on a fifteen-minute schedule, unattended

---

## 3. The data source

TfL Unified API, endpoint `/BikePoint`. A single call returns the current state of all ~800 stations.

Register for a free Application ID and Key — no card, takes two minutes. Store it as `TFL_APP_KEY` in `.env`. Requests still work without it, but unregistered access is rate limited. Register anyway.

### 3.1 The response structure is the whole challenge

Each station is a Place object, and its actual status is buried in an array of key/value objects:

```json
{
  "id": "BikePoints_1",
  "commonName": "River Street, Clerkenwell",
  "lat": 51.529163, "lon": -0.10997,
  "additionalProperties": [
    { "key": "TerminalName",  "value": "001023", "modified": "..." },
    { "key": "NbBikes",       "value": "9",  "modified": "..." },
    { "key": "NbEmptyDocks",  "value": "4",  "modified": "..." },
    { "key": "NbDocks",       "value": "19", "modified": "..." },
    { "key": "NbEBikes",      "value": "1",  "modified": "..." }
  ]
}
```

Your silver layer has to **pivot** that array into columns. In Snowflake that is `LATERAL FLATTEN` over `additionalProperties`, then conditional aggregation grouped by station. This is the core intellectual work of the project and it is worth taking slowly.

Keys you will encounter include `TerminalName`, `Installed`, `Locked`, `InstallDate`, `RemovalDate`, `Temporary`, `NbBikes`, `NbEmptyDocks`, `NbDocks`, `NbStandardBikes` and `NbEBikes`.

### 3.2 Five things that will catch you out

- **Everything arrives as a string.** `"NbBikes": "9"`, `"Locked": "false"`. Cast in silver, never in bronze.
- **Do not rely on array position.** You will find code online indexing `additionalProperties[7]` to get bike counts. The key set is not guaranteed identical or identically ordered across all stations. Match on key, always.
- **`modified` is per-property, not per-station.** There is no single freshness timestamp for a station. Decide deliberately which one — if any — you trust, and record your own capture timestamp regardless.
- **Broken docks are derivable.** Where `NbDocks - (NbBikes + NbEmptyDocks)` is not zero, docks are out of service. That is a genuine data-quality signal sitting inside the data, and it answers one of Wheelhouse's questions on its own.
- **There is no history endpoint.** A failed run is not a run you can repeat. This is why scheduling and reliability matter more in your project than in any exercise you have done so far.

---

## 4. Required architecture — ELT

Land raw, transform in the warehouse.

```
TfL /BikePoint
      |  requests
      v
  extract           raw JSON, untouched
      |
      v
     S3             raw/bikepoint/dt=YYYY-MM-DD/hour=HH/
                    snapshot_YYYYMMDDTHHMMSSZ.json
      |  COPY INTO
      v
  BRONZE            VARIANT column + capture metadata
      |  dbt
      v
  SILVER            LATERAL FLATTEN -> pivot -> typed columns
                    |-- dim_station       (deduped, latest attributes)
                    |-- fct_availability  (station per snapshot, incremental)
      |  dbt
      v
  GOLD              empty/full patterns by hour and weekday
                    capacity lost to broken docks
```

One Airflow DAG on a fifteen-minute schedule, using BashOperator to invoke dbt — the simpler of the two patterns in `fpl-elt-dbt`.

> 💡 **Real-world tip**
> Your dimension and your fact both come from the same API call. Separating them is a modelling decision you make in dbt, not something the source hands you. Being able to explain why you separated them is worth more than the models themselves.

---

## 5. Scope

### In scope

All stations. The single `/BikePoint` endpoint. Fifteen-minute schedule. Bronze, silver and gold. Three to five dbt models. dbt tests. One incremental materialisation, on the availability fact.

### Explicitly out of scope

Do not build these, even if you have time:

- TfL line status, arrivals or journey planning endpoints
- Historic Santander journey CSVs
- Borough boundary joins requiring geospatial files
- Dashboards or web apps
- Astronomer Cosmos — use BashOperator
- Incremental materialisation on anything other than the fact table
- Alerting beyond Airflow's retries

> ⚠ **Watch out for**
> If a councillor-level insight requires a shapefile, it is out of scope. Group by station and coordinates. Scope creep is the most likely reason this project does not finish, and it always arrives disguised as a good idea.

---

## 6. Milestones

| Date | Checkpoint |
|---|---|
| Wed 19 Aug | Kickoff. Platform running, TfL key working, `additionalProperties` structure understood on paper |
| **Thu 20 Aug** | **Snapshots landing in S3 on a schedule.** Hard checkpoint |
| Fri 21 Aug | `COPY INTO` bronze working. Raw JSON queryable as VARIANT |
| Sat 22 – Sun 23 | Collection runs unattended. First flatten attempted |
| Mon 24 Aug | Silver model: flatten and pivot to typed columns |
| **Tue 25 Aug** | **End-to-end API → S3 → bronze → silver, unattended.** Hard checkpoint |
| Wed 26 – Thu 27 | Dimension and fact separated. Incremental fact. Deduplication proven |
| **Fri 28 Aug** | **Code freeze.** Gold models, dbt tests passing, README written |
| Sat 29 – Sun 30 | Buffer and demo prep |
| Mon 31 Aug | Bank holiday — deliberately empty |
| Tue 1 Sep | Demo day |

> ★ **Why Thursday matters**
> Get something crude collecting before you build anything properly. A rough snapshot landing in S3 beats an elegant pipeline that starts collecting on day eight with six days of history missing.
>
> You can rebuild bronze, silver and gold from the raw S3 files as many times as you like. You cannot rebuild the raw files.
>
> If a checkpoint slips, come and find me the same day. Do not absorb it quietly and hope to catch up.

---

## 7. Ways of working

`main` is protected. No direct commits, no force pushes, no exceptions.

Branch naming:

```
feature/<initials>-<short-description>
fix/<initials>-<short-description>

For example:  feature/dr-silver-pivot
```

Every change reaches `main` through a pull request, approved by the instructor. Your teammates cannot unblock a merge, but you should still review each other's work — it is assessed, and it catches things before I see them.

**PRs are reviewed twice daily, morning and evening.** If something is urgent outside those windows, message me.

### Who owns what

Agree this between you on day one and post it in your team channel. Pairing is encouraged — these are areas of ownership, not walls.

- **Extract, S3 landing and scheduling** — owns the DAG, the snapshot format and the Thursday checkpoint
- **Snowflake stage, `COPY INTO` and bronze** — owns everything between S3 and dbt
- **dbt silver, gold and tests** — owns the flatten, the pivot and the modelling
- README, integration testing and the demo are shared across all three

> ★ **At three people, one person unavailable is a third of the team**
> Plan so the project survives someone losing two days. The Friday code freeze exists partly for this. Do not build a plan that only works if all three of you are at full capacity for fourteen straight days.

---

## 8. Technical requirements

- **Environment variables for everything machine-specific.** No hardcoded buckets, accounts, schemas, warehouses or paths.
- `TFL_APP_KEY` in `.env`, never committed. `.env.example` kept current in the same PR that adds a variable.
- dbt `profiles.yml` reads entirely from environment variables. No credentials in the repo.
- Capture metadata on every bronze row: source file, capture timestamp, load timestamp.
- Your incremental model must be safe to re-run. Test it by running it twice and comparing counts.
- **Snowflake warehouse auto-suspend stays at 60 seconds.** A fifteen-minute schedule with a warehouse that never suspends will burn credits the other team also depends on.
- PEP 8 and type hints in Python. Consistent naming and a `schema.yml` for every dbt model.

---

## 9. Demo day

Fifteen minutes:

| Time | What you cover |
|---|---|
| 3 min | The problem and your architecture |
| 5 min | Trigger the pipeline live — show a snapshot arriving and moving through bronze to gold |
| 4 min | Answer Wheelhouse's questions from the warehouse |
| 3 min | What broke, what you would do differently, what you would build next |

Show how much history you accumulated. It is the part of this project you cannot fake, and it is the part an employer will find most convincing.

---

## 10. Assessment

Marked out of 100. **Meets** is the standard expected of everyone — a pass, not a compliment. **Exceeds** describes work you would be comfortable showing an employer without caveat.

> ★ **This is a team mark**
> There is no individual adjustment. Ensuring everyone contributes meaningfully is the team's responsibility, not something resolved after the fact.

| # | Criterion | Wt | Meets | Exceeds |
|---|---|---|---|---|
| 1 | **Pipeline function** | 25 | DAG runs unattended on a fifteen-minute schedule, populating S3, bronze, silver and gold | Recovers from a transient API failure without intervention; a gap in collection is detectable and explained rather than invisible |
| 2 | **Correctness & deduplication** | 15 | Re-running a load creates no duplicate snapshots; the incremental fact is safe to re-run; missing or malformed properties handled explicitly; dbt tests pass | Deduplication enforced by design rather than cleaned up afterwards; a station reporting an inconsistent dock count is flagged, not silently averaged |
| 3 | **Modelling & code quality** | 15 | Clear bronze/silver/gold separation; no transformation before bronze; dimension and fact properly separated; every model has a `schema.yml` | Models readable and well-named; pivot logic key-driven rather than position-dependent; sensible use of one incremental materialisation |
| 4 | **Collaboration** | 15 | Every change reaches `main` through a pull request; no direct commits; all three members have meaningful commits spread across the fortnight, not concentrated at the end; branch naming followed; PR descriptions filled in rather than left as the blank template | Teammates review each other's PRs without being required to — comments that ask questions, spot problems or suggest alternatives, not "looks good"; PRs small and single-purpose; review participation shared across all three rather than one person doing it all |
| 5 | **Config & secrets** | 10 | Nothing hardcoded; `.env` never committed; `.env.example` complete; dbt profile fully env-driven | Configuration validated at startup with a clear error when a variable is missing |
| 6 | **Reproducibility & docs** | 10 | A stranger can clone, follow the README, and run it without asking questions | Modelling decisions documented with reasoning; known limitations stated honestly |
| 7 | **Demo & reflection** | 10 | Architecture explained clearly; pipeline demonstrated live; Wheelhouse's questions answered from the warehouse | Choices defended with reasoning, including ones that proved wrong; failures described specifically and what changed as a result |

*Instructor approval is what unblocks a merge, so reviewing each other's work is voluntary. That is deliberate. Doing it anyway — properly, not as a formality — is what criterion 4 measures.*

Below **Meets** on any criterion is recorded with a specific, actionable note — what was missing and what would close the gap — rather than a lower number on its own.

---

## 11. Before you start

- [ ] Snowflake login works and you can see your team's schema
- [ ] AWS credentials in your local `.env`, and you can list your S3 bucket
- [ ] TfL Application ID and Key registered
- [ ] Repo cloned into `projects/` inside your `data-engineering` monorepo
- [ ] `docker compose up` succeeds and the Airflow UI loads
- [ ] One `/BikePoint` call made successfully in a browser or Postman

Anything unticked is a message to me straight away, not a discovery three days in.

---

## 12. When you are stuck

- `fpl-elt-dbt` — medallion structure, S3 key layouts and the BashOperator DAG pattern
- Your Week 10 dbt materials — materialisations and tests
- The API Integration Pipeline guide, sections 2 and 3 — profiling an unfamiliar response

---

*© Latent Ed 2026 | For cohort use only | latented.co.uk*

