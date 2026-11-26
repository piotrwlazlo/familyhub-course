# Session 12: Watch the model live

*Work in VS Code, in your own copy: see `sessions/HOW_TO_WORK.md`.*

**Goal:** see, on a dashboard, what the model behind the assistant is doing right now: how fast it writes (tokens per second), how many questions it is answering, how many wait in the queue, how long people wait for the first word and how full its memory is. In production this dashboard is the first place you look when someone says "the assistant is slow".

**How it works**

| Part | What it does | Where |
|---|---|---|
| The model (vLLM) | counts everything it does and shows the numbers as text on `/metrics` | port 8004 |
| Prometheus | reads `/metrics` every 5 seconds and keeps the history | port 9090, only on this GB10 |
| Grafana | draws charts from Prometheus; everybody logs in with their own name | port 3001 |

**One stack for the whole team.** There is one Prometheus and one Grafana on the GB10. **One person** sets them up (part A) while the others watch on the shared screen. Then **everybody** builds their own dashboard (part B). Agree before the session who does part A.

**You start from** any version of your code: nothing in your code changes in this session.

**Before you start (once, the GB10 admin):** the person who does part A needs Docker rights on the GB10 (`docker ps` works without sudo).

## Part A: set up the monitoring (ONE person for the team)

The others: do not run these commands, follow on the shared screen.

**A1. Look at the raw numbers.** The model already counts everything; it just shows plain text:
```
curl -s http://127.0.0.1:8004/metrics | grep -E '^vllm:(num_requests_running|num_requests_waiting|generation_tokens_total|kv_cache_usage_perc|time_to_first_token_seconds_count)\{'
```

| Metric | Kind | What it means |
|---|---|---|
| `vllm:num_requests_running` | gauge (goes up and down) | questions being answered now |
| `vllm:num_requests_waiting` | gauge | questions waiting in the queue |
| `vllm:generation_tokens_total` | counter (only goes up) | all tokens written since the model started; Prometheus turns it into "per second" |
| `vllm:kv_cache_usage_perc` | gauge, 0 to 1 | how full the memory for running conversations is |
| `vllm:time_to_first_token_seconds` | histogram (`_bucket`, `_count`, `_sum`) | how long people waited for the first token, sorted into buckets |

Run the command again after someone asks the assistant a question: the counters went up.

**A2. Check that nobody runs it yet.** Both commands must print nothing:
```
docker ps -a --filter name=familyhub-prometheus --filter name=familyhub-grafana
ss -ltn | grep -E ':(9090|3001) '
```
If the first one shows containers, the monitoring is already running: stop here and go to part B.

**A3. Read the two configuration files** in `monitoring/`:
- `prometheus.yml`: what Prometheus reads (`127.0.0.1:8004/metrics`) and how often (every 5 s). If your model runs on another port, change it here.
- `docker-compose.yml`: the two containers, their ports and where they keep their data (two Docker volumes).

**A4. Start Prometheus.** First a password for the Grafana administrator (Docker Compose wants it for the whole file, even when you start only Prometheus). It goes into `monitoring/.env`, which only you can read and which is not in git:
```
cd monitoring
echo "GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 18 | tr -d '/+=')" > .env && chmod 600 .env
docker compose up -d prometheus
docker compose ps
```
Open it: in VS Code, tab **Ports** > **Forward a Port** > `9090`, then http://localhost:9090.
- **Status > Target health**: the target `model` must be **UP** (it can take 10 seconds).
- **Query**: type `vllm:num_requests_running` and press Execute. Then `rate(vllm:generation_tokens_total[1m])`: tokens per second over the last minute (it needs about a minute of history). Switch to the **Graph** tab.

**A5. Start Grafana**
```
docker compose up -d grafana
cat .env
```
After about 20 seconds open http://<GB10 address>:3001 (or forward port 3001 like in A4) and log in as `admin` with the password from `.env`.
- **Connections > Data sources**: Prometheus is already there. It comes from the file `grafana/provisioning/datasources/prometheus.yml` (configuration as code: no clicking needed on a new server). Open it, scroll down, **Test**: "Successfully queried the Prometheus API".

**A6. Logins for the team.** One login and one folder per person; each person can change only their own folder and can look at everybody's:
```
bash add_logins.sh <name> <name> <name>
cat learners.txt
```
Give each person their line (login and first password).

**A7. Build your own dashboard** exactly like part B: give yourself a login in A6 too, log out as `admin` and log in with your name.

## Part B: your own dashboard (EVERYBODY)

**B1.** Open Grafana (the address from part A) and log in with your name and the password you got. Change the password: your picture top right > **Profile** > **Change password**.

**B2.** **Dashboards** > open your folder (it has your name) > **New** > **New dashboard** > **Add visualization** > choose **Prometheus**.

**B3. Build four panels.** For each panel: in the query editor switch from **Builder** to **Code**, paste the query, press **Run queries**. On the right: type the **Title**, choose the **Visualization** and under **Standard options** the **Unit**. Then **Back to dashboard** and **Add > Visualization** for the next one.

| Panel title | Query | Visualization | Unit |
|---|---|---|---|
| Tokens per second | `sum(rate(vllm:generation_tokens_total[1m]))` | Time series | none |
| Requests running and waiting | query A: `sum(vllm:num_requests_running)`, then **+ Add query**, query B: `sum(vllm:num_requests_waiting)` | Time series | none |
| Time to first token (95%) | `histogram_quantile(0.95, sum by (le) (rate(vllm:time_to_first_token_seconds_bucket[5m])))` | Time series | seconds (s) |
| KV cache used | `max(vllm:kv_cache_usage_perc)` | Gauge | Percent (0.0-1.0) |

For the two queries in the second panel, set **Options > Legend** to `running` and `waiting` so the chart says which line is which.

**B4. Save** (top right) with the title `<your name> - Family Hub model`, in **your** folder. Set the time range (top right) to **Last 15 minutes** and the refresh to **5s**, then save again.

**B5. Give it something to show.** In VS Code, in your own folder:
```
python sessions/s12/load.py
```
It sends 10 golden questions to the model, 2 at a time. Watch your dashboard while it runs. Then, all together at the same moment: `python sessions/s12/load.py --users 4 --questions 20`. What happens to "waiting", to tokens per second and to the time to first token?

**B6. Check:** `python sessions/s12/check.py` (it asks for your Grafana login and password).

**Done when** `python sessions/s12/check.py` prints `SESSION DONE` (4 of 4).

## Rules for the shared stack
- Only the part A person runs `docker compose`, `add_logins.sh` or `cleanup.sh` in `monitoring/`. Never start a second copy from your own folder.
- After the course the part A person removes everything (containers, data, dashboards, logins, images): `bash cleanup.sh --yes` in `monitoring/`.

## Prompts for the AI assistant
- *"Explain this PromQL query step by step for a beginner: histogram_quantile(0.95, sum by (le) (rate(vllm:time_to_first_token_seconds_bucket[5m])))"*
- *"What is the difference between a counter and a gauge in Prometheus? Why do we use rate() only on counters?"*
- *"Write a PromQL query for the median time of a whole answer from the histogram vllm:e2e_request_latency_seconds_bucket."*

## Hints
- **No data** on a panel: nobody asked anything in the chosen time range. Run `load.py`, or choose a longer time range.
- **Target DOWN** in Prometheus (A4): the model is not running, or it runs on another port than the one in `prometheus.yml`.
- **Port 9090 or 3001 already used** (A2): another program has it. Change the port in `docker-compose.yml` (Prometheus `--web.listen-address`, Grafana `GF_SERVER_HTTP_PORT`, and the Prometheus URL in the data source file).
- **You cannot save:** you are not in your own folder. Save as > choose your folder.
- **Forgot the admin password:** `cat monitoring/.env` (part A person only).
- Why `rate(...[1m])` and not the counter itself? The counter only grows since the model started; what you want to see is how fast it grows now.
- Why the 95% and not the average? An average hides the few people who waited a long time; "95% of people waited less than X seconds" does not.

## Try at the end
- Add a fifth panel "Whole answer time" from `vllm:e2e_request_latency_seconds_bucket` (median and 95%).
- Add a panel "Answers per minute, by how they ended": `sum by (finished_reason) (increase(vllm:request_success_total[1m]))`, legend `{{finished_reason}}`. What does `length` mean for a user?
- Look at a colleague's dashboard (you can open it, but not change it).
