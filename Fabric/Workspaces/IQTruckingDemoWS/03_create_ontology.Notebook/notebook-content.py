# Fabric notebook source


# MARKDOWN ********************

# <h1 align="center">🚛 Trucking Ontology Workshop</h1>
# <h3 align="center">Notebook 03 — Create Ontology</h3>
# 
# ---
# 
# > **Purpose:** Creates a Fabric Ontology via the REST API, reading table schemas
# > from the lakehouse and building entity types, data bindings, relationships, and
# > contextualizations programmatically.
# >
# > Each run is idempotent — an existing ontology with the same name is deleted first.

# MARKDOWN ********************

# ## ⚙️ Configuration

# PARAMETERS CELL ********************

WORKSPACE_NAME = "Trucking"
LAKEHOUSE_NAME = "lh_trucking"
ONTOLOGY_NAME  = "TruckingOntology_AutoGen"

# MARKDOWN ********************

# ### ⚠️ Before running this notebook, select the **lh_trucking** lakehouse in the Explorer panel on the left so that Spark can resolve table names.

# MARKDOWN ********************

# ## 🔍 Resolve Workspace & Lakehouse IDs

# CELL ********************

import sempy.fabric as fabric

client = fabric.FabricRestClient()

WORKSPACE_ID = fabric.get_notebook_workspace_id()
print(f"Workspace: {WORKSPACE_NAME}  (ID: {WORKSPACE_ID})")

resp = client.get(f"v1/workspaces/{WORKSPACE_ID}/lakehouses")
resp.raise_for_status()
lh = next(
    (l for l in resp.json().get("value", []) if l["displayName"] == LAKEHOUSE_NAME),
    None,
)
if not lh:
    raise ValueError(f"Lakehouse '{LAKEHOUSE_NAME}' not found in workspace")

LAKEHOUSE_ID = lh["id"]
print(f"Lakehouse: {LAKEHOUSE_NAME}  (ID: {LAKEHOUSE_ID})")

# MARKDOWN ********************

# ## 📐 Entity & Relationship Definitions

# CELL ********************

ENTITY_CONFIG = {
    "customers":          {"entity_name": "Customer",         "key_column": "customer_id",          "display_column": "name"},
    "trips":              {"entity_name": "Trip",             "key_column": "trip_id",              "display_column": "trip_number"},
    "drivers":            {"entity_name": "Driver",           "key_column": "driver_id",            "display_column": "last_name"},
    "loads":              {"entity_name": "Load",             "key_column": "load_id",              "display_column": "load_number"},
    "routes":             {"entity_name": "Route",            "key_column": "route_id",             "display_column": "route_name"},
    "terminals":          {"entity_name": "Terminal",         "key_column": "terminal_id",          "display_column": "name"},
    "trailers":           {"entity_name": "Trailer",          "key_column": "trailer_id",           "display_column": "trailer_number"},
    "trucks":             {"entity_name": "Truck",            "key_column": "truck_id",             "display_column": "truck_number"},
}

RELATIONSHIPS = [
    {"name": "TripCarriesLoad",          "source_table": "trips",  "source_entity": "Trip",    "source_column": "trip_id",    "target_entity": "Load",     "target_column": "load_id"},
    {"name": "TripHasDriver",            "source_table": "trips",  "source_entity": "Trip",    "source_column": "trip_id",    "target_entity": "Driver",   "target_column": "driver_id"},
    {"name": "TripFollowsRoute",         "source_table": "trips",  "source_entity": "Trip",    "source_column": "trip_id",    "target_entity": "Route",    "target_column": "route_id"},
    {"name": "TruckMakesTrip",           "source_table": "trips",  "source_entity": "Truck",   "source_column": "truck_id",   "target_entity": "Trip",     "target_column": "trip_id"},
    {"name": "TripMovesTrailer",         "source_table": "trips",  "source_entity": "Trip",    "source_column": "trip_id",    "target_entity": "Trailer",   "target_column": "trailer_id"},
    {"name": "RouteOriginTerminal",      "source_table": "routes", "source_entity": "Route",   "source_column": "route_id",   "target_entity": "Terminal", "target_column": "origin_terminal_id"},
    {"name": "RouteDestinationTerminal", "source_table": "routes", "source_entity": "Route",   "source_column": "route_id",   "target_entity": "Terminal", "target_column": "destination_terminal_id"},
    {"name": "LoadForCustomer",          "source_table": "loads",  "source_entity": "Load",    "source_column": "load_id",    "target_entity": "Customer", "target_column": "customer_id"},
]

# Spark simpleString() → Ontology valueType
SPARK_TO_ONTOLOGY = {
    "string":  "String",
    "boolean": "Boolean",
    "date":    "DateTime",
    "timestamp": "DateTime",
    "int":     "BigInt",
    "integer": "BigInt",
    "short":   "BigInt",
    "byte":    "BigInt",
    "long":    "BigInt",
    "bigint":  "BigInt",
    "float":   "Double",
    "double":  "Double",
}

# MARKDOWN ********************

# ## 📖 Read Lakehouse Table Schemas

# CELL ********************

table_schemas = {}

for table_name, cfg in ENTITY_CONFIG.items():
    schema = spark.table(f"{LAKEHOUSE_NAME}.{table_name}").schema

    columns = []
    for field in schema.fields:
        type_str = field.dataType.simpleString()
        ontology_type = SPARK_TO_ONTOLOGY.get(type_str)
        if ontology_type:
            columns.append({"name": field.name, "valueType": ontology_type})
        else:
            print(f"  ⚠️  Skipping {table_name}.{field.name} (type: {type_str})")

    table_schemas[table_name] = columns
    print(f"  ✅ {table_name}: {len(columns)} compatible columns")

print(f"\n📊 Total: {sum(len(c) for c in table_schemas.values())} columns across {len(table_schemas)} tables")

# MARKDOWN ********************

# ## 🏗️ Build Ontology Definition

# CELL ********************

import json, base64, uuid, random

random.seed(42)
_used_ids = set()


def generate_id():
    """Generate a unique positive 64-bit integer ID (as a string)."""
    while True:
        id_val = random.randint(10**12, 10**15)
        if id_val not in _used_ids:
            _used_ids.add(id_val)
            return str(id_val)


def to_base64(obj):
    return base64.b64encode(json.dumps(obj).encode("utf-8")).decode("utf-8")


# ── Tracking maps ────────────────────────────────────────────────────────────
entity_type_ids  = {}   # entity_name → entity_type_id
property_ids     = {}   # (entity_name, col_name) → property_id
key_property_ids = {}   # entity_name → key property_id

# ── Start with the required empty definition part ────────────────────────────
parts = [
    {"path": "definition.json", "payload": to_base64({}), "payloadType": "InlineBase64"},
]

# ── Entity types + data bindings ─────────────────────────────────────────────
for table_name, cfg in ENTITY_CONFIG.items():
    entity_name = cfg["entity_name"]
    key_column  = cfg["key_column"]
    columns     = table_schemas[table_name]

    entity_type_id = generate_id()
    entity_type_ids[entity_name] = entity_type_id

    properties = []
    for col in columns:
        prop_id = generate_id()
        property_ids[(entity_name, col["name"])] = prop_id
        properties.append({
            "id": prop_id,
            "name": col["name"],
            "redefines": None,
            "baseTypeNamespaceType": None,
            "valueType": col["valueType"],
        })

    key_prop_id = property_ids[(entity_name, key_column)]
    key_property_ids[entity_name] = key_prop_id

    # Entity type definition
    entity_def = {
        "id": entity_type_id,
        "namespace": "usertypes",
        "baseEntityTypeId": None,
        "name": entity_name,
        "entityIdParts": [key_prop_id],
        "displayNamePropertyId": property_ids[(entity_name, cfg.get("display_column", key_column))],
        "namespaceType": "Custom",
        "visibility": "Visible",
        "properties": properties,
        "timeseriesProperties": [],
    }
    parts.append({
        "path": f"EntityTypes/{entity_type_id}/definition.json",
        "payload": to_base64(entity_def),
        "payloadType": "InlineBase64",
    })

    # Data binding (NonTimeSeries → lakehouse table)
    binding_id = str(uuid.uuid4())
    data_binding = {
        "id": binding_id,
        "dataBindingConfiguration": {
            "dataBindingType": "NonTimeSeries",
            "propertyBindings": [
                {"sourceColumnName": col["name"], "targetPropertyId": property_ids[(entity_name, col["name"])]}
                for col in columns
            ],
            "sourceTableProperties": {
                "sourceType": "LakehouseTable",
                "workspaceId": WORKSPACE_ID,
                "itemId": LAKEHOUSE_ID,
                "sourceTableName": table_name
            },
        },
    }
    parts.append({
        "path": f"EntityTypes/{entity_type_id}/DataBindings/{binding_id}.json",
        "payload": to_base64(data_binding),
        "payloadType": "InlineBase64",
    })
    print(f"  ✅ {entity_name}  ({len(properties)} properties, key={key_column})")

# ── Relationship types + contextualizations ──────────────────────────────────
for rel in RELATIONSHIPS:
    rel_id = generate_id()
    source_entity = rel["source_entity"]
    target_entity = rel["target_entity"]

    rel_def = {
        "namespace": "usertypes",
        "id": rel_id,
        "name": rel["name"],
        "namespaceType": "Custom",
        "source": {"entityTypeId": entity_type_ids[source_entity]},
        "target": {"entityTypeId": entity_type_ids[target_entity]},
    }
    parts.append({
        "path": f"RelationshipTypes/{rel_id}/definition.json",
        "payload": to_base64(rel_def),
        "payloadType": "InlineBase64",
    })

    # Contextualization — binds columns in the source table to entity keys
    ctx_id = str(uuid.uuid4())
    contextualization = {
        "id": ctx_id,
        "dataBindingTable": {
            "workspaceId": WORKSPACE_ID,
            "itemId": LAKEHOUSE_ID,
            "sourceTableName": rel["source_table"],
            "sourceType": "LakehouseTable",
        },
        "sourceKeyRefBindings": [
            {"sourceColumnName": rel["source_column"], "targetPropertyId": key_property_ids[source_entity]}
        ],
        "targetKeyRefBindings": [
            {"sourceColumnName": rel["target_column"], "targetPropertyId": key_property_ids[target_entity]}
        ],
    }
    parts.append({
        "path": f"RelationshipTypes/{rel_id}/Contextualizations/{ctx_id}.json",
        "payload": to_base64(contextualization),
        "payloadType": "InlineBase64",
    })
    print(f"  ✅ {rel['name']}  ({source_entity} → {target_entity})")

print(f"\n📦 Total definition parts: {len(parts)}")

# MARKDOWN ********************

# ## 🚀 Create Ontology via REST API

# CELL ********************

import time

# ── Delete existing ontology if present ──────────────────────────────────────
resp = client.get(f"v1/workspaces/{WORKSPACE_ID}/ontologies")
resp.raise_for_status()
existing = next(
    (o for o in resp.json().get("value", []) if o["displayName"] == ONTOLOGY_NAME),
    None,
)
if existing:
    print(f"🗑️  Deleting existing ontology '{ONTOLOGY_NAME}' (id={existing['id']})...")
    del_resp = client.delete(f"v1/workspaces/{WORKSPACE_ID}/ontologies/{existing['id']}")
    del_resp.raise_for_status()
    print(f"   ⏳ Deleted. Waiting 30 seconds for cleanup...")
    time.sleep(30)
    print(f"   ✅ 30 second wait completed...proceeding with new ontology creation.") 

# ── Create ontology with full definition ─────────────────────────────────────
payload = {
    "displayName": ONTOLOGY_NAME,
    "description": "Trucking domain ontology — entities and relationships for the long-haul trucking domain.",
    "definition": {"parts": parts},
}

print(f"⏳ Creating ontology '{ONTOLOGY_NAME}'...")
resp = client.post(f"v1/workspaces/{WORKSPACE_ID}/ontologies", json=payload)

if resp.status_code == 201:
    result = resp.json()
    print(f"✅ Ontology created!  ID: {result['id']}")

elif resp.status_code == 202:
    operation_id = resp.headers.get("x-ms-operation-id")
    retry_after  = int(resp.headers.get("Retry-After", "30"))
    print(f"   Operation {operation_id} — polling every {retry_after}s...")

    while True:
        time.sleep(retry_after)
        poll = client.get(f"v1/operations/{operation_id}")
        poll.raise_for_status()
        status = poll.json().get("status")
        print(f"   Status: {status}")

        if status == "Succeeded":
            result_resp = client.get(f"v1/operations/{operation_id}/result")
            if result_resp.status_code == 200:
                print(f"✅ Ontology created!  ID: {result_resp.json().get('id', 'N/A')}")
            else:
                print(f"✅ Ontology creation succeeded.")
            break
        elif status in ("Failed", "Cancelled"):
            print(f"❌ Ontology creation {status.lower()}.")
            print(f"   {poll.json()}")
            break
else:
    print(f"❌ HTTP {resp.status_code}: {resp.text}")
    resp.raise_for_status()
