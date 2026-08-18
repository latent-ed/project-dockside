# Project Dockside

London cycle hire availability pipeline — ELT

**Team:** Talk Data To Me
**Programme:** Latent Ed Data Engineering, Cohort 2026

The full brief is in [`docs/BRIEF.md`](docs/BRIEF.md). Read it before you start.

---

## What this pipeline does

<!-- TODO: two or three sentences, in your own words. -->

## Architecture

<!-- TODO: each layer, and where data lands. -->

## Setup

Clone this repo **inside** your existing `data-engineering` monorepo:

```
cd data-engineering/projects
git clone <this-repo-url>
```

Airflow mounts `../projects` as its DAGs folder, so this project appears
automatically. Your platform and `.env` are untouched.

Then:

```
cp .env.example .env
pip install -r requirements.txt
```

Never commit `.env`.

## Running it

<!-- TODO: how to trigger it, and what to expect when it works. -->

## Decisions we made

<!-- TODO: why you chose things. This is assessed. -->

## Known limitations

<!-- TODO: be honest. Stating a limitation scores better than hiding it. -->
test
