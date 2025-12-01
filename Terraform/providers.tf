# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
  # skip_provider_registration = true
  # client_id       = var.client_id
  # client_secret   = var.client_secret
  # tenant_id       = var.tenant_id
  # subscription_id = var.subscription_id
}

# data "azurerm_databricks_workspace" "dbxworkspace" {
#   name                = var.dbx_workspace_name
#   resource_group_name = var.resource_group
# }

# provider "databricks" {
#   host                        = data.azurerm_databricks_workspace.dbxworkspace.workspace_url
#   azure_workspace_resource_id = data.azurerm_databricks_workspace.dbxworkspace.id
#   azure_client_id             = var.client_id
#   azure_client_secret         = var.client_secret
#   azure_tenant_id             = var.tenant_id
# }