## Prerequesites:
# Deployment SPN needs to be DB account admin and workspace admin
# SPN needs to have contributor permissions on subscription
# Storage Account needs to be created for Terraform Backend

# Resource Parameters
env = "dev" # environment
application = "msft"
region = "eastus"
prefix = "ag"
## Resource Groups
resourcegroups = [
    {
        name = "dataeng"
        region = "eastus"
    },
    {
        name = "openai"
        region = "eastus"
    }
]

## Azure SQL 
azuresql_database = [
    {
        name = "sample"
        resourcegroup = "dataeng"
        region = "eastus"
        license_type   = "LicenseIncluded"
        version = "12.0"
        admin_login ="ag_admin"
        admin_pass = "2Z1/(0KO)Xsr"
        azuread_login = "<>"
        azuread_objectid = "<>"
        read_scale = true
        sku_name = "HS_Gen5_2"
        zone_redundant = false
        prevent_destroy = true
    }
]

azuresql_mi = [
    {
        name = "managed-instance"
        resourcegroup = "dataeng"
        region = "eastus"
        license_type = "BasePrice"
        admin_login ="ag_admin"
        admin_pass = "rubbish_pass!"
        sku_name = "GP_Gen5"
        storage_size_in_gb = 32
        vcores             = 4
    }
]
