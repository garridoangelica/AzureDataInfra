terraform {
  required_providers {
    databricks = {
      source = "databricks/databricks"
    }
  }
}

locals {
  cluster_map = {
    for param in var.general_clusters: 
      "${param.cluster_name}-${param.node_type_id}" => {
        cluster_name = param.cluster_name
        node_type_id = param.node_type_id
      }
  }
}


data "databricks_spark_version" "latest_lts" {
  long_term_support = true
}

resource "databricks_cluster" "shared_autoscaling" {
  for_each = local.cluster_map
  cluster_name            = each.value.cluster_name
  spark_version           = data.databricks_spark_version.latest_lts.id
  node_type_id            = each.value.node_type_id
  autotermination_minutes = 20
  autoscale {
    min_workers = 1
    max_workers = 2
  }
}
