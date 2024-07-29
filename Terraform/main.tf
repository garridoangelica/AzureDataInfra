
# Create Resource Groups
module "resource_groups" {
    source = "./modules/resourcegroup"
    resourcegroups = var.resourcegroups
    env = var.env
    application = var.application
    region = var.region
    prefix = var.prefix
}

# Create Azure SQL Managed Identity
module "azuresql_db" {
    source = "./modules/azuresqldb"
    azuresql_database = var.azuresql_database
    env = var.env
    application = var.application
    region = var.region
    prefix = var.prefix
    depends_on = [
        module.resource_groups
  ]
}