
locals {
  resourcegroups_map = {
    for param in var.resourcegroups: 
      "${param.name}-${param.region}" => {
        name = param.name
        region = param.region
      }
  }
}

resource "azurerm_resource_group" "create_resource_groups" {
  for_each = local.resourcegroups_map
  name     = "rg-${var.prefix}-${var.env}-${var.application}-${var.region}-${each.value.name}"
  location = each.value.region
}