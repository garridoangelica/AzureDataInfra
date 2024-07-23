ARG UBUNTU_VER=22.04

# Install Ubuntu 22.04 LTS as base image for container
FROM ubuntu:${UBUNTU_VER}

# This arguments need to be after From if not they will be lost
ARG CONDA_VER=latest
ARG OS_TYPE=x86_64
ARG PY_VER=3.8.11
ARG TF_VER=2.5.0
ARG TERRAFORM_VERSION=1.7.4

# Skip installation of unnecessary packages. Reduce size of final container
RUN echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
RUN echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker

# Prevent prompts and avoid errors at package installation
RUN DEBIAN_FRONTEND=noninteractive

# System packages 
RUN apt-get update && apt-get -y install curl
RUN apt-get install ca-certificates -y && update-ca-certificates
RUN apt-get install -y git
RUN apt-get install wget -y 
RUN apt-get install unzip -y
RUN apt-get install vim -y
# Install necessary packages and programs

## Install Miniconda
RUN curl -LO "http://repo.continuum.io/miniconda/Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh"
RUN bash Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh -p /miniconda -b
RUN rm Miniconda3-${CONDA_VER}-Linux-${OS_TYPE}.sh
ENV PATH=/miniconda/bin:${PATH}
RUN conda update -y conda

# Copy yml and create from environment file for conda
COPY environment.yml .
RUN conda env create -f environment.yml

## Install Databricks CLI
RUN curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh

## Install Terraform
# Download terraform for linux
RUN wget --progress=dot:mega https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip

RUN \
	# Unzip
	unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
	# Move to local bin
	mv terraform /usr/local/bin/ && \
	# Make it executable
	chmod +x /usr/local/bin/terraform && \
	# Check that it's installed
	terraform --version

RUN pip install azure-cli

# Clean up package list after required packages are installed
RUN rm -rf /var/lib/apt/lists/*

# Create an user with less priviledges that is not root user
RUN useradd -ms /bin/bash apprunner

# Set user as the default for any further operations
USER apprunner