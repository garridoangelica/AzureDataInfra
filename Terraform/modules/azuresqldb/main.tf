locals {
  azuresql_db_map = {
    for param in var.azuresql_database: 
      "${param.name}-${param.region}-${param.resourcegroup}" => {
        name = param.name
        region = param.region
        resourcegroup = param.resourcegroup
        license_type = param.license_type
        version = param.version
        admin_login = param.admin_login
        admin_pass = param.admin_pass
        azuread_login = param.azuread_login
        azuread_objectid = param.azuread_objectid
        sku_name = param.sku_name
        read_scale = param.read_scale
        zone_redundant = param.zone_redundant
        prevent_destroy = param.prevent_destroy
      }
  }
}

resource "azurerm_mssql_server" "create_sql_server" {
    for_each = local.azuresql_db_map
    name     = "sqlserver-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.name}"
    resource_group_name  = "rg-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.resourcegroup}"
    location = each.value.region
    version       = each.value.version
    administrator_login          = each.value.admin_login
    administrator_login_password = each.value.admin_pass

    azuread_administrator {
    login_username = each.value.azuread_login
    object_id      = each.value.azuread_objectid
  }
}


# https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/mssql_database
resource "azurerm_mssql_database" "create_sql_database" {
  for_each = local.azuresql_db_map
  name     = "sqldb-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.name}"
  server_id      = azurerm_mssql_server.create_sql_server["${each.value.name}-${each.value.region}-${each.value.resourcegroup}"].id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = each.value.license_type
  read_scale     = each.value.read_scale
  sku_name       = each.value.sku_name
  zone_redundant = each.value.zone_redundant
  auto_pause_delay_in_minutes = 30
  sample_name = "AdventureWorksLT"
  # prevent the possibility of accidental data loss
  lifecycle {
    prevent_destroy = false
  }
  depends_on = [
        azurerm_mssql_server.create_sql_server
  ]
}