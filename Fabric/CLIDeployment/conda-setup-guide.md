# Running Conda Environment for the First Time - Step by Step Instructions

This guide provides complete instructions for setting up and using conda environments in Git Bash on Windows.

## Quick Start - If You Already Have environment.yml

If you already have an `environment.yml` file and conda working in Git Bash:

```bash
# IMPORTANT: First-time setup - Initialize conda for bash (run this once)
conda init bash
# Close and reopen Git Bash, OR run: source ~/.bashrc

# Navigate to your project directory with environment.yml
cd /c/path/to/your/project/AzureDataInfra/Fabric/CLIDeployment

# Create the environment
conda env create -f environment.yml

# Activate the environment (use the name from your environment.yml)
conda activate fabricclideployment

# Verify it works
conda list
```

**For detailed setup instructions, continue reading below.**

## Prerequisites

- **Conda installed** (Anaconda or Miniconda)
- **Git Bash installed** (comes with Git for Windows)

## Step 1: Verify Conda Installation

First, check if conda is installed on your system. You can do this in either PowerShell or Git Bash:

**In PowerShell or Command Prompt:**
```powershell
conda --version
```

**In Git Bash:**
```bash
conda --version
```

If conda is not found in Git Bash but works in PowerShell, it means conda is not in your Git Bash PATH (we'll fix this in Step 3).

If conda is not found anywhere, download and install [Anaconda](https://www.anaconda.com/products/distribution) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

## Step 2: Find Your Conda Installation Path

**In PowerShell:**
```powershell
$env:PATH -split ';' | Where-Object {$_ -like "*conda*" -or $_ -like "*anaconda*"}
```

**In Git Bash (if conda is already accessible):**
```bash
which conda
```

This will typically return something like:
```
C:\Users\YourUsername\AppData\Local\anaconda3\Scripts\conda.exe
```

Note down the path up to the `anaconda3` folder (e.g., `C:\Users\YourUsername\AppData\Local\anaconda3`).

## Step 3: Configure Git Bash to Access Conda

### 3.1 Open Git Bash

Launch Git Bash from your Start menu or right-click in a folder and select "Git Bash Here".

### 3.2 Create/Edit Bash Profile

Create or edit your `.bashrc` file to add conda to your PATH:

```bash
# Navigate to home directory
cd ~

# Create or edit .bashrc file
nano .bashrc
```

### 3.3 Add Conda to PATH

Add the following lines to your `.bashrc` file (replace with your actual conda path):

```bash
# Add Conda to PATH
export PATH="/c/Users/YourUsername/AppData/Local/anaconda3/Scripts:$PATH"
export PATH="/c/Users/YourUsername/AppData/Local/anaconda3:$PATH"

# Initialize conda for bash (simple wrapper function to avoid cygdrive issues)
conda() {
    "/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe" "$@"
}

# Set conda environment variables
export CONDA_EXE="/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe"
export CONDA_PYTHON_EXE="/c/Users/YourUsername/AppData/Local/anaconda3/python.exe"
```

**Note**: Replace `YourUsername` with your actual Windows username, and adjust the path if your conda is installed elsewhere.

**Alternative Method**: This approach uses conda's profile script or manual initialization to avoid the cygdrive path conversion issue.

### 3.4 Save and Exit

- In nano: Press `Ctrl+X`, then `Y`, then `Enter`
- Or simply save the file if using another editor

### 3.5 Reload Bash Configuration

```bash
source ~/.bashrc
```

## Step 4: Verify Conda Works in Git Bash

Test that conda is now accessible:

```bash
conda --version
conda info
```

You should see conda version information and configuration details.

## Step 5: Initialize Conda for Bash

Run conda init to properly set up conda activation/deactivation:

```bash
conda init bash
```

After running this command, **close and reopen Git Bash** or run:

```bash
source ~/.bashrc
```

This step is crucial for `conda activate` and `conda deactivate` commands to work properly.

## Step 6: Prepare Your Environment YAML File

### Option A: If You Already Have environment.yml

If you already have an `environment.yml` file, just navigate to its directory:

```bash
# Navigate to your project directory containing environment.yml
cd /c/path/to/your/folder/AzureDataInfra/Fabric/CLIDeployment
# Example: cd /c/Users/agarrido/GitRepos/AzureDataInfra/Fabric/CLIDeployment
```

## Step 6: Create the Conda Environment

### 6.1 Navigate to Directory with environment.yml

```bash
cd /c/path/to/directory/Fabric/CLIDeployment/environment.yml
```

### 6.2 Create Environment from YAML

```bash
conda env create -f environment.yml
```

This command will:
- Read the `environment.yml` file
- Create a new environment with the specified name
- Install all listed dependencies
- Install pip packages if specified

### 6.3 Handle Existing Environment

If the environment already exists, you have two options:

**Option 1: Remove and recreate**
```bash
conda env remove -n fabricclideployment -y
conda env create -f environment.yml
```

**Option 2: Update existing environment**
```bash
conda env update -f environment.yml --prune
```

## Step 7: Activate and Use Your Environment

### 7.1 Activate Environment

```bash
conda activate fabricclideployment
```

You should see the environment name in parentheses at the beginning of your prompt:
```
(your-environment-name) user@computer MINGW64 /c/path/to/project
```

### 7.2 Verify Installation

Check installed packages:
```bash
conda list
pip list
```

### 7.3 Deactivate Environment

When done working:
```bash
conda deactivate
```

## Common Commands Reference

| Command | Description |
|---------|-------------|
| `conda env list` | List all environments |
| `conda activate env-name` | Activate environment |
| `conda deactivate` | Deactivate current environment |
| `conda env remove -n env-name` | Delete environment |
| `conda env export > environment.yml` | Export current environment |
| `conda env create -f environment.yml` | Create from YAML file |
| `conda env update -f environment.yml` | Update existing environment |

## Troubleshooting

### Conda Activate Not Working
If `conda activate` fails with an error, you need to initialize conda for bash first:

```bash
# Run this command once to set up conda for bash
conda init bash

# Then close and reopen Git Bash (REQUIRED)
# OR source both profile files:
source ~/.bash_profile
source ~/.bashrc

# Now conda activate should work:
conda activate your-environment-name
```

**Important Notes**:
- `conda init bash` modifies your `.bash_profile` file
- You MUST close and reopen Git Bash for changes to take effect
- If using wrapper functions in `.bashrc`, they may conflict with conda init - remove them after running conda init
- `conda activate` needs special shell functions that only `conda init` can properly set up

**If you get `/cygdrive/c/...` errors after conda init:**
The conda init command creates paths that Git Bash converts incorrectly. Here's the complete fix:

1. **Remove conda wrapper function from .bashrc** (if you have one):
```bash
nano ~/.bashrc
# Remove these lines if present:
# conda() {
#     "/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe" "$@"
# }
# Keep only the PATH exports
```

2. **Fix the .bash_profile file** (created by conda init):
```bash
nano ~/.bash_profile
# Find this line:
eval "$('/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe' 'shell.bash' 'hook')"

# Change it to (remove quotes and use Windows path format):
eval "$(C:/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe shell.bash hook)"

# Also change the if condition from:
if [ -f '/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe' ]; then
# To:
if [ -f "C:/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe" ]; then
```

3. **Reload both files**:
```bash
source ~/.bashrc
source ~/.bash_profile
```

**Complete example of fixed .bash_profile:**
```bash
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
if [ -f "C:/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe" ]; then
    eval "$(C:/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe shell.bash hook)"
fi
# <<< conda initialize <<<
```

**Quick Fix Method - Replace entire .bash_profile content:**
If you're still getting cygdrive errors, completely replace your `.bash_profile` content:

```bash
# Delete and recreate .bash_profile
rm ~/.bash_profile

# Create new .bash_profile with correct content
cat > ~/.bash_profile << 'EOF'
# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
if [ -f "C:/Users/agarrido/AppData/Local/anaconda3/Scripts/conda.exe" ]; then
    eval "$(C:/Users/agarrido/AppData/Local/anaconda3/Scripts/conda.exe shell.bash hook)"
fi
# <<< conda initialize <<<
EOF

# Test it
source ~/.bash_profile
```

**And ensure your .bashrc only contains:**
```bash
# Add Conda to PATH
export PATH="/c/Users/agarrido/AppData/Local/anaconda3/Scripts:$PATH"
export PATH="/c/Users/agarrido/AppData/Local/anaconda3:$PATH"
```

**Alternative: Complete Bypass Method**
If the above methods still don't work, use this alternative approach that completely avoids the cygdrive issue:

```bash
# Clear both files and use a different approach
rm ~/.bash_profile
rm ~/.bashrc

# Create a simple .bashrc with conda wrapper and activation functions
cat > ~/.bashrc << 'EOF'
# Add Conda to PATH
export PATH="/c/Users/agarrido/AppData/Local/anaconda3/Scripts:$PATH"
export PATH="/c/Users/agarrido/AppData/Local/anaconda3:$PATH"

# Conda wrapper function
conda() {
    "/c/Users/agarrido/AppData/Local/anaconda3/Scripts/conda.exe" "$@"
}

# Custom activation function that works reliably
activate() {
    if [ "$1" = "" ]; then
        echo "Usage: activate <environment_name>"
        return 1
    fi
    
    # Set environment variables manually
    export CONDA_DEFAULT_ENV="$1"
    export CONDA_PREFIX="/c/Users/agarrido/AppData/Local/anaconda3/envs/$1"
    export PATH="/c/Users/agarrido/AppData/Local/anaconda3/envs/$1/Scripts:/c/Users/agarrido/AppData/Local/anaconda3/envs/$1:$PATH"
    
    # Update prompt
    PS1="($1) $PS1"
    
    echo "Activated environment: $1"
}

# Deactivation function
deactivate() {
    if [ "$CONDA_DEFAULT_ENV" != "" ]; then
        echo "Deactivated environment: $CONDA_DEFAULT_ENV"
        unset CONDA_DEFAULT_ENV
        unset CONDA_PREFIX
        # Reload PATH from original
        export PATH="/c/Users/agarrido/AppData/Local/anaconda3/Scripts:/c/Users/agarrido/AppData/Local/anaconda3:$PATH"
        # Reset prompt (this is basic - you might need to adjust)
        PS1='$ '
    fi
}
EOF

# Reload
source ~/.bashrc
```

Then use: `activate fabricclideployment` instead of `conda activate fabricclideployment`

### Quick Fix for Cygdrive Issues
If you keep getting `/cygdrive/c/...` path errors, try this simple approach in your `.bashrc`:

```bash
# Simple conda wrapper function (most reliable method)
conda() {
    cmd.exe /c "C:\Users\YourUsername\AppData\Local\anaconda3\Scripts\conda.exe $*"
}

# For conda activate to work properly
alias activate='cmd.exe /c "C:\Users\YourUsername\AppData\Local\anaconda3\Scripts\activate.bat"'
```

Replace `YourUsername` with your actual username, then reload: `source ~/.bashrc`

### Conda Command Not Found
- Verify conda is installed: `conda --version` in PowerShell
- Check your `.bashrc` paths match your actual conda installation
- Reload bash configuration: `source ~/.bashrc`

### Git Bash Adds `/cygdrive` to Path
If Git Bash converts your path and adds `/cygdrive` (e.g., `/cygdrive/c/Users/...`), causing "No such file or directory":

**Method 1: Use conda profile script**
```bash
# Check if conda profile exists
ls /c/Users/YourUsername/AppData/Local/anaconda3/etc/profile.d/conda.sh
# If it exists, source it in .bashrc instead of using eval
source "/c/Users/YourUsername/AppData/Local/anaconda3/etc/profile.d/conda.sh"
```

**Method 2: Manual conda function**
```bash
# Add this function to your .bashrc
conda() {
    "/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe" "$@"
}
```

**Method 3: Simple alias approach**
```bash
# Add this alias to your .bashrc
alias conda='"/c/Users/YourUsername/AppData/Local/anaconda3/Scripts/conda.exe"'
```

After adding any of these methods, reload bash: `source ~/.bashrc`

### Permission Issues
- Run Git Bash as Administrator if needed
- Check file permissions on your project directory

### Package Installation Failures
- Check package names and versions exist
- Try without version constraints first
- Check if package is available on conda-forge channel

### Environment Already Exists Error
```bash
# Remove existing environment first
conda env remove -n environment-name -y
# Then recreate
conda env create -f environment.yml
```

## Example Complete Workflow

Here's a complete example using the Fabric CLI deployment environment:

```bash
# 1. Ensure you're in the right directory
cd /c/Users/agarrido/GitRepos/AzureDataInfra/Fabric/CLIDeployment

# 2. Check the environment.yml content
cat environment.yml

# 3. Create the environment
conda env create -f environment.yml

# 4. Activate the environment
conda activate fabricclideployment

# 5. Verify installation
conda list
ms-fabric --version

# 6. When done, deactivate
conda deactivate
```

## Notes

- Always activate your environment before working on a project
- Keep your `environment.yml` file in version control
- Use specific version numbers for reproducible environments
- Test your environment setup on a clean machine when possible