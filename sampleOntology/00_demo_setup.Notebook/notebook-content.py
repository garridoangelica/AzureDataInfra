# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   }
# META }

# MARKDOWN ********************

# <h1 align="center">🚛 Trucking Ontology Workshop</h1>
# <h3 align="center">Notebook 00 — Environment Setup</h3>
# 
# <div align="center">
# <table style="border:none;background:transparent;margin:auto"><tr style="border:none">
# <td style="border:none;padding:2px"><img src="https://img.shields.io/badge/python-3.9%2B-blue?logo=python&logoColor=white" /></td>
# <td style="border:none;padding:2px"><img src="https://img.shields.io/badge/jupyter-notebook-orange?logo=jupyter&logoColor=white" /></td>
# <td style="border:none;padding:2px"><img src="https://img.shields.io/badge/Microsoft%20Fabric-ready-0078D4?logo=microsoft&logoColor=white" /></td>
# </tr></table>
# </div>
# 
# ---
# 
# > **Purpose:** Run each cell in order to provision all Fabric resources needed for the workshop.  
# > Each step is idempotent — safe to re-run if something fails partway through.

# MARKDOWN ********************

# ## 📋 Prerequisites
# 
# #### 🏗️ Workspace & Access
# 
# <table style="text-align:left; width:100%">
# <thead><tr><th></th><th>Requirement</th><th>Detail</th></tr></thead>
# <tbody>
# <tr><td>🏢</td><td><strong>Fabric-enabled workspace</strong></td><td>Use this workspace for all resources in the tutorial</td></tr>
# <tr><td>👤</td><td><strong>Workspace role: Contributor or higher</strong></td><td>The user running this notebook must have at least Contributor access; Admin role recommended</td></tr>
# <tr><td>⚡</td><td><strong>F16 capacity (minimum)</strong></td><td>Use at least F16 to avoid throttling and ensure optimal performance</td></tr>
# </tbody>
# </table>
# 
# #### 🔧 Tenant Settings *(enabled by a Fabric Administrator)*
# 
# <table style="text-align:left; width:100%">
# <thead><tr><th></th><th>Setting</th><th>Location</th></tr></thead>
# <tbody>
# <tr><td>1️⃣</td><td>Enable <strong>Ontology item</strong> <em>(preview)</em></td><td>Admin Portal → Tenant Settings</td></tr>
# <tr><td>2️⃣</td><td>User can create <strong>Graph</strong> <em>(preview)</em></td><td>Admin Portal → Tenant Settings</td></tr>
# <tr><td>3️⃣</td><td>Users can create and share <strong>Data agent</strong> item types <em>(preview)</em></td><td>Admin Portal → Tenant Settings</td></tr>
# <tr><td>4️⃣</td><td>Users can use <strong>Copilot</strong> and features powered by Azure OpenAI</td><td>Admin Portal → Tenant Settings</td></tr>
# <tr><td>5️⃣</td><td>Data sent to Azure OpenAI can be <strong>processed outside</strong> your capacity's region</td><td>Admin Portal → Tenant Settings</td></tr>
# <tr><td>6️⃣</td><td>Data sent to Azure OpenAI can be <strong>stored outside</strong> your capacity's region</td><td>Admin Portal → Tenant Settings</td></tr>
# </tbody>
# </table>
# 
# > ⚠️ Settings 4–6 involve cross-region data processing by Azure OpenAI. Review your organization's data residency and compliance policies before enabling them.


# MARKDOWN ********************

# ---
# ## ⚙️ Setup — Configure & Download Assets
# 
# Run the two cells below to configure and download all workshop assets:
# 1. **create_ontology** — set to True if you want to create ontology at set up. Set to False to skip automated ontology creation (create manually via Option 2 in README)
# 2. **Workspace ID and Name are optional** — if left blank, the notebook will automatically detect them from your current Fabric session. Only fill these in if you want to target a different workspace.
# 
# Note: This notebook will download all workshop scripts, reference data, and the `TruckingSM.SemanticModel` files from GitHub into `./builtin/`
# 
# > These downloads only happen once — every subsequent step just uses local files.


# CELL ********************

# ─────────────────────────────────────────────────────────────────────────────────────
create_ontology = True  # Set to False to skip automated ontology creation (create manually via Option 2 in README)
# ─────────────────────────────────────────────────────────────────────────────────────
# ── Optional Configurations ──────────────────────────────────────────────────────────
# ── These are optional because the code will attempt to infer them if not set ────────
WORKSPACE_ID   = ""    # 👈 Replace with your Fabric workspace GUID
WORKSPACE_NAME = ""  # 👈 Replace with your Fabric workspace name

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

if WORKSPACE_ID == "" or WORKSPACE_NAME == "":
    import sempy.fabric as fabric
    import re

    # Get the workspace ID
    WORKSPACE_ID = fabric.get_notebook_workspace_id()

    # Get the workspace name
    WORKSPACE_NAME = fabric.resolve_workspace_name()

    # Validate: only letters, digits, spaces, hyphens, and underscores allowed
    if not re.fullmatch(r"[A-Za-z0-9 _\-]+", WORKSPACE_NAME):
        raise ValueError(
            f"Workspace name '{WORKSPACE_NAME}' contains special characters. "
            "Only letters, digits, spaces, hyphens, and underscores are allowed."
        )

    print(f"Workspace ID: {WORKSPACE_ID}")
    print(f"Workspace Name: {WORKSPACE_NAME}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import urllib.request, json
from pathlib import Path

BRANCH  = "main"
REPO    = "robkerr/trucking-ontology"
RAW     = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
API     = f"https://api.github.com/repos/{REPO}/git/trees/{BRANCH}?recursive=1"

# Folders to mirror into ./builtin/  →  (repo_prefix, local_subdir)
FOLDERS = [
    ("scripts",                                  ""),                          # flat into builtin/
    ("semantic_model_project/TruckingSM.SemanticModel", "TruckingSM.SemanticModel"),
    ("reference_data", "reference_data")

]

BUILTIN = Path("./builtin")
BUILTIN.mkdir(exist_ok=True)

def _download(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "FabricNotebook/1.0"})
    with urllib.request.urlopen(req) as r:
        dest.write_bytes(r.read())

# Fetch full tree once
print(f"Fetching file tree for branch '{BRANCH}'...")
req = urllib.request.Request(API, headers={"User-Agent": "FabricNotebook/1.0"})
with urllib.request.urlopen(req) as r:
    tree = json.loads(r.read())["tree"]
print(f"  {len(tree)} total entries in repo.\n")

for repo_prefix, local_sub in FOLDERS:
    blobs = [e for e in tree if e["type"] == "blob" and e["path"].startswith(repo_prefix + "/")]
    label = local_sub or repo_prefix
    print(f"📥 Downloading {len(blobs)} file(s) from '{repo_prefix}/'...")
    dest_root = BUILTIN / local_sub if local_sub else BUILTIN
    for entry in blobs:
        rel      = entry["path"][len(repo_prefix) + 1:]   # strip the folder prefix
        dest     = dest_root / rel
        url      = f"{RAW}/{entry['path']}"
        _download(url, dest)
        print(f"   ✅ {rel}")
    print()

print(f"✅ All assets downloaded → {BUILTIN.resolve()}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🏗️ Step 1 — Create Lakehouse
# 
# Creates the `lh_trucking` Lakehouse in your workspace.
# If it already exists the cell is a no-op — safe to re-run.

# CELL ********************

import sempy.fabric as fabric

LAKEHOUSE_NAME = "lh_trucking"          # Lakehouse to create (or reuse if it exists)

client = fabric.FabricRestClient()

# List all lakehouses in the workspace and find ours by name
resp = client.get(f"v1/workspaces/{WORKSPACE_ID}/lakehouses")
resp.raise_for_status()
lakehouses = resp.json().get("value", [])
existing = next((lh for lh in lakehouses if lh["displayName"] == LAKEHOUSE_NAME), None)

if existing:
    LAKEHOUSE_ID = existing["id"]
    print(f"ℹ️  Lakehouse '{LAKEHOUSE_NAME}' already exists — skipping creation.")
    print(f"   LAKEHOUSE_ID = {LAKEHOUSE_ID}")
else:
    resp = client.post(
        f"v1/workspaces/{WORKSPACE_ID}/lakehouses",
        json={"displayName": LAKEHOUSE_NAME},
    )
    resp.raise_for_status()
    LAKEHOUSE_ID = resp.json()["id"]
    print(f"✅ Lakehouse created: {LAKEHOUSE_NAME}")
    print(f"   LAKEHOUSE_ID = {LAKEHOUSE_ID}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 📄 Step 2 — Generate Reference Data
# 
# reference_data files (already in `./builtin/`) have 11 synthetic
# JSONL files, upload them directly to the Lakehouse via OneLake:
# `Files/reference_data/`
# 
# Files are download it to `./builtin/` first, then uploaded using `mssparkutils.fs.put()`
# — no default lakehouse mount required.

# CELL ********************

import os
from pathlib import Path

LOCAL_TMP      = Path("./builtin/reference_data")
ONELAKE_DEST   = (
    f"abfss://{WORKSPACE_ID}@onelake.dfs.fabric.microsoft.com"
    f"/{LAKEHOUSE_ID}/Files/reference_data"
)

jsonl_files = sorted(LOCAL_TMP.glob("*.jsonl"))
if not jsonl_files:
    raise RuntimeError("No JSONL files were written. Check the output above for errors.")

print(f"\nUploading {len(jsonl_files)} files to Lakehouse...")
for f in jsonl_files:
    dest = f"{ONELAKE_DEST}/{f.name}"
    mssparkutils.fs.put(dest, f.read_text(encoding="utf-8"), True)
    print(f"   ✅ {f.name:<35} {f.stat().st_size / 1024:>7.1f} KB")

print(f"\n🎉 {len(jsonl_files)} files written to the Lakehouse.")
print(f"   Lakehouse : {LAKEHOUSE_NAME} ({LAKEHOUSE_ID})")
print( "   Next      : Step 3 will create Delta tables from these files.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 📊 Step 3 — Create Delta Tables
# 
# Runs `01_load_reference_data.ipynb` as a child notebook, passing the Lakehouse name and data path as parameters. That notebook reads each JSONL file and creates a corresponding Delta table in the Lakehouse.
# 
# > This step may take 2–5 minutes to complete.

# CELL ********************

notebookutils.notebook.run(
    "01_load_reference_data",
    timeout_seconds=600,
    arguments={
        "LAKEHOUSE_NAME":      LAKEHOUSE_NAME,
        "WORKSPACE_NAME": WORKSPACE_NAME,
        "REFERENCE_DATA_PATH": "Files/reference_data",
        "LAKEHOUSE_ID": LAKEHOUSE_ID,
        "WORKSPACE_ID": WORKSPACE_ID
    },
)
print("✅ Delta tables created successfully.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🚀 Step 4 — Deploy Semantic Model
# 
# Uses `create_trucking_sm.py` (already in `./builtin/`) and the pre-downloaded
# `TruckingSM.SemanticModel` files to:
# 
# 1. Install **fabric-cicd** (if needed)
# 2. Patch `expressions.tmdl` with this workspace's OneLake URL
# 3. Publish the model via `fabric-cicd`
# 4. Trigger a full refresh and wait for completion
# 
# > Run the single cell below.

# CELL ********************

import importlib.util
from pathlib import Path

# Load create_trucking_sm.py as a module from builtin/
spec = importlib.util.spec_from_file_location(
    "create_trucking_sm", "./builtin/create_trucking_sm.py"
)
sm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sm)

sm.ensure_fabric_cicd()

# Patch the pre-downloaded expressions.tmdl then publish
sm_dir = Path("./builtin/TruckingSM.SemanticModel")
sm.patch_expressions(sm_dir, WORKSPACE_ID, LAKEHOUSE_ID)
sm.publish_model(WORKSPACE_ID, Path("./builtin"))

sm.trigger_refresh(WORKSPACE_ID)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## 🏠 Step 5 — Create Eventhouse & KQL Database
# 
# Uses `create_trucking_eventhouse.py` (already in `./builtin/`) to create:
# - **Eventhouse** `eh_trucking`
# - **KQL Database** `trucking_db` inside it
# 
# Both resources are idempotent — existing ones are detected and skipped.
# 
# > Provisioning is asynchronous; the cell polls until both are ready.

# CELL ********************

import importlib.util

# Load create_trucking_eventhouse.py as a module from builtin/
spec = importlib.util.spec_from_file_location(
    "create_trucking_eventhouse", "./builtin/create_trucking_eventhouse.py"
)
eh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(eh)

client = eh._get_client()

print("[1/3] Eventhouse...")
EVENTHOUSE_ID = eh.ensure_eventhouse(WORKSPACE_ID, client)

print("\n[2/3] KQL Database...")
KQL_DB_ID = eh.ensure_kql_database(WORKSPACE_ID, EVENTHOUSE_ID, client)

print(f"\n✅ Eventhouse  : {eh.EVENTHOUSE_NAME} ({EVENTHOUSE_ID})")
print(f"   KQL Database : {eh.KQL_DB_NAME} ({KQL_DB_ID})")

print("\n[3/3] KQL Tables...")
created = eh.create_kql_tables(WORKSPACE_ID, EVENTHOUSE_ID, eh.KQL_DB_NAME, client)
print(f"\n✅ Tables ready: {', '.join(created) if created else '(none)'}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Verify KQL Tables

# CELL ********************

import requests

# Resolve Eventhouse query URI
resp = client.get(f"v1/workspaces/{WORKSPACE_ID}/eventhouses/{EVENTHOUSE_ID}")
resp.raise_for_status()
KUSTO_URI = resp.json()["properties"]["queryServiceUri"]
KUSTO_DATABASE = eh.KQL_DB_NAME

kusto_token = notebookutils.credentials.getToken("https://kusto.kusto.windows.net")
headers = {
    "Authorization": f"Bearer {kusto_token}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
mgmt_url = f"{KUSTO_URI}/v1/rest/mgmt"

# Verify tables exist in the KQL database
verify_stmt = ".show tables | project TableName"
body = {"db": KUSTO_DATABASE, "csl": verify_stmt, "properties": {}}
r = requests.post(mgmt_url, headers=headers, json=body, timeout=60)
r.raise_for_status()

rows = r.json().get("Tables", [{}])[0].get("Rows", [])
existing = sorted(row[0] for row in rows)

expected = {"TelemetryEvent", "EngineFaultEvent", "GeofenceEvent", "HOSStatusChangeEvent", "LoadStatusEvent"}
print(f"Tables in '{KUSTO_DATABASE}':\n")
for name in existing:
    status = "✅" if name in expected else "  "
    print(f"  {status} {name}")

missing = expected - set(existing)
if missing:
    print(f"\n⚠️  Missing tables: {', '.join(sorted(missing))}")
else:
    print(f"\n✅ All {len(expected)} event tables confirmed.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ---
# ## ⚡ Step 6 — Generate Synthetic Events
# 
# Runs `02_generate_events.ipynb` as a child notebook, passing the Eventhouse
# query URI and KQL Database name as parameters.
# 
# The notebook generates realistic telemetry, load-status, engine-fault,
# and weather-alert event streams and ingests them directly into the
# `trucking_db` KQL tables via the Kusto Python SDK.

# CELL ********************

# Resolve the Eventhouse query URI from the REST API
resp = client.get(f"v1/workspaces/{WORKSPACE_ID}/eventhouses/{EVENTHOUSE_ID}")
resp.raise_for_status()
KUSTO_URI = resp.json()["properties"]["queryServiceUri"]
KUSTO_DATABASE = eh.KQL_DB_NAME   # 'trucking_db'

print(f"  Eventhouse URI : {KUSTO_URI}")
print(f"  KQL Database   : {KUSTO_DATABASE}")

notebookutils.notebook.run(
    "02_generate_events",
    timeout_seconds=900,
    arguments={
        "KUSTO_URI":      KUSTO_URI,
        "KUSTO_DATABASE": KUSTO_DATABASE,
        "LAKEHOUSE_ID": LAKEHOUSE_ID,
        "WORKSPACE_ID": WORKSPACE_ID

    },
)
print("\n✅ Event generation complete.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Step 7: Create Ontology
# 
# Creates the Fabric Ontology if `create_ontology = True`. Set to `False` to create manually — see README Option 2.

# CELL ********************

if create_ontology:
    print("Running 03_create_ontology notebook...")
    notebookutils.notebook.run(
        "03_create_ontology",
        timeout_seconds=900,
        arguments={
            "WORKSPACE_NAME": WORKSPACE_NAME,
            "LAKEHOUSE_NAME": LAKEHOUSE_NAME,
        }
    )
    print("✅ Ontology created successfully.")
else:
    print("ℹ️  create_ontology = False — skipping automated creation.")
    print("Follow README Option 2 to create the ontology manually from the semantic model.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
