locals {
  azuresql_mi_map = {
    for param in var.azuresql_mi: 
      "${param.name}-${param.region}-${param.resourcegroup}" => {
        name = param.name
        region = param.region
        resourcegroup = param.resourcegroup
        license_type = param.license_type
        admin_login = param.admin_login
        admin_pass = param.admin_pass
        sku_name = param.sku_name
        storage_size_in_gb = param.storage_size_in_gb
        vcores = param.vcores
      }
  }
}

resource "azurerm_mssql_managed_instance" "create_sql_mi" {
  for_each = local.azuresql_mi_map
  name     = "sqlmi-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.name}"
  resource_group_name  = "rg-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.resourcegroup}"
  location = each.value.region
  license_type       = each.value.license_type
  sku_name           = each.value.sku_name
  storage_size_in_gb = each.value.storage_size_in_gb
  vcores             = each.value.vcores
  administrator_login          = each.value.admin_login
  administrator_login_password = each.value.admin_pass
}