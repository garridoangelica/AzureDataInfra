# Docker Getting Started

- Creating your first image
- Running your first container

## 1. Create the Docker Image (if it's the first time)
```bash
docker build -t data-infra-environment .
```

## 1. Re-build the same container

docker-compose build -t data-infra-environment

## 2. Run the Docker Image for interactive Ubuntu

```bash
# docker run data-infra-environment
docker run -i -t data-infra-environment
```

## 3. List running containers the Docker Image

```bash
docker ps
```

## 3. Stop running container Docker Image

```bash
docker stop <container_id>
```

## 4. Exit container by pressing CTRL+D

For conda environemnt
run: 
```bash
source /miniconda/etc/profile.d/conda.sh
conda activate infra_env
```

az login --use-device-code
terraform init
terraform plan -var-file=parameters.tfvars
terraform apply -var-file=parameters.tfvars
terraform destroy  -var-file=parameters.tfvars

terraform init -backend-config="resource_group_name=rg-demos" -backend-config="storage_account_name=tfbackendinfra" -backend-config="container_name=dev-terraform" -backend-config="key=dev.terraform.tfstate"