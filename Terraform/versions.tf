# We strongly recommend using the required_providers block to set the
# Azure Provider source and version being used
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=3.0.0"
    }
    databricks = {
      source = "databricks/databricks"
      version = "1.0.1"
    }
  }
   # Save State in Azure
  # backend "azurerm" {
  #   resource_group_name  = var.backend_rg
  #   storage_account_name = var.backend_st
  #   container_name       = "${var.env}-terraform"
  #   key                  = "${var.env}.terraform.tfstate"
  # }
  backend "azurerm" {}
}