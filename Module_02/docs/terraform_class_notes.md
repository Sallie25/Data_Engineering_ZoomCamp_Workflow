# Terraform Class Notes

## What is Terraform?

**Origin of the Name:**
- Terraform (the term) refers to transforming dead, inhospitable planets into environments that can sustain life
- The software Terraform follows this same spirit: transforming cloud platforms into infrastructure where code can live and software can run

**Official Definition (HashiCorp):**
Terraform is an infrastructure as code (IaC) tool that lets you define both cloud and on-premises resources in human-readable configuration files that you can version, reuse, and share. It provides a consistent workflow to provision and manage all infrastructure throughout its lifecycle.

**Core Concept:** Infrastructure as Code

---

## Why Use Terraform?

### 1. **Simplicity**
- Define infrastructure in a single file
- Easy to read and understand what will be created
- View all parameters, configurations, disk sizes, and storage types in one place

### 2. **Easier Collaboration**
- Files can be pushed to repositories (e.g., GitHub)
- Team members can review, add corrections, and make additions
- Deploy infrastructure once everyone agrees on the configuration

### 3. **Reproducibility**
- Build resources in a Dev environment, then deploy to Production with parameter updates
- Share projects easily - just pass the Terraform file and update parameters
- Recreate infrastructure consistently across environments

### 4. **Ensure Resources Are Removed**
- Run a single command to bring down all resources
- Avoid continued charges for forgotten test resources
- No need to manually track everything you built

---

## What Terraform is NOT

❌ **Not a software deployment tool**
- Does not manage or update code on infrastructure
- Other tools exist for deploying and updating software

❌ **Cannot change immutable resources**
- Cannot directly change VM types (must destroy and recreate)
- Cannot change Google Cloud Storage locations (must copy data, create new bucket, destroy old bucket)

❌ **Does not manage resources outside Terraform files**
- Only manages resources defined in your Terraform configuration files
- If you create resources manually (e.g., Kubernetes cluster), Terraform won't manage them unless defined in the files

---

## What Terraform IS

✅ **Infrastructure as Code**
- Does one thing very well: allows you to create resources with code files
- Powerful simplicity focused on infrastructure provisioning

---

## About These Videos

### What These Videos Are NOT:
- Not a full, comprehensive Terraform course
- Many in-depth courses (several hours long) available on YouTube

### What These Videos ARE:
- A slight introduction to Terraform
- Enough to get you started standing up infrastructure
- Sufficient for course projects and final project
- Enough to make you "dangerous"

### ⚠️ **IMPORTANT WARNING:**
- You are creating real resources that can be expensive
- Some cloud resources can incur significant charges
- **Be very sure of what you're deploying before you deploy it**
- Many things are safe, but always verify costs first

---

## How Terraform Works

**Workflow Diagram:**

```
Local Machine (Terraform installed)
    ↓
Define Provider in Terraform file
    ↓
Terraform downloads provider code
    ↓
Provider connects to service (AWS, GCP, Azure, etc.)
    ↓
Authorization (service account, access token, etc.)
    ↓
Infrastructure provisioned
```

**Key Components:**
- **Terraform software** runs on your local machine
- **Providers** allow communication with different services
- **Authorization** required to access cloud platforms

---

## Providers

**What are Providers?**
Code that allows Terraform to communicate with and manage resources on various platforms.

**Common Providers:**
- AWS
- Azure
- GCP (Google Cloud Platform)
- Kubernetes
- vSphere
- Alibaba Cloud
- Oracle Cloud Infrastructure
- Active Directory

**Note:** There are 74+ pages of available providers - many organizations and individuals have created provider code for different platforms and services.

---

## Key Terraform Commands

### `terraform init`
- Downloads provider code after you've defined your provider
- Brings provider code to your local machine
- First command to run in a new Terraform project

### `terraform plan`
- Shows you what resources will be created
- Preview of infrastructure changes before applying
- Use this to review before making changes

### `terraform apply`
- Executes what's defined in your .tf (Terraform) files
- Actually builds the infrastructure
- Creates the resources you've specified in code

### `terraform destroy`
- **Possibly the most important command**
- Tears down all infrastructure defined in your Terraform files
- Ensures you're not continuously charged for resources
- Removes everything that was created

---

## Key Takeaways

1. Terraform is focused on infrastructure provisioning through code
2. Define infrastructure once, deploy anywhere (Dev, Prod, etc.)
3. Version control your infrastructure like you version control code
4. Always review with `terraform plan` before applying changes
5. Remember to clean up resources with `terraform destroy` to avoid charges
6. Be cautious - you're creating real, potentially expensive resources

---

## File Extensions
- `.tf` - Terraform configuration files
- Human-readable format
- Can be versioned in Git repositories

---

# Setting Up Terraform with GCP

## Creating a Service Account on GCP

### What is a Service Account?
- Similar to a regular user account but **never meant to be logged into**
- Used by software to run tasks and programs
- Has permissions just like user accounts (opening files, running programs, etc.)
- Used specifically for programmatic access to cloud resources

### Steps to Create a Service Account:

1. **Navigate to IAM & Admin**
   - Go to your GCP project dashboard
   - Select "IAM & Admin" → "Service Accounts"

2. **Create Service Account**
   - Click "Create Service Account"
   - Name it (e.g., "terraform-runner")
   - Description is optional

3. **Assign Permissions/Roles**
   
   For this course, we'll need:
   - **Cloud Storage** → Storage Admin
   - **BigQuery** → BigQuery Admin
   - **Compute Engine** → Compute Admin

   **⚠️ Important Note on Permissions:**
   - These are broad roles with extensive access
   - In production, you should limit permissions to only what's needed
   - For Terraform, you typically only need:
     - Create and destroy buckets (not full admin)
     - Create and destroy datasets (not full admin)
     - Create and destroy compute instances (not full admin)

4. **Adding Permissions Later**
   - If you need to add permissions after creation:
   - Go to IAM & Admin → IAM
   - Find your service account
   - Click "Edit Principal"
   - Add another role

---

## Managing Service Account Keys

### Creating a Key:
1. Go to "Service Accounts"
2. Click the three dots (ellipsis) next to your service account
3. Select "Manage Keys"
4. Click "Create New Key"
5. Choose **JSON** format
6. Key file will download automatically

### 🚨 CRITICAL SECURITY WARNING 🚨

**Service account keys are EXTREMELY SENSITIVE credentials!**

**Why is this dangerous?**
With broad permissions, attackers could:
- Create expensive VM instances and mine cryptocurrency (costing thousands/hour)
- Upload large files to storage and run up bills
- Create command and control servers for botnets
- Perform any action the service account has permissions for

**Real-world example: Okta Breach**
- Employee logged into work laptop with personal Google account
- Google Chrome saved the password
- Employee's credentials were in a previous password dump
- Attacker logged into Google account → accessed saved passwords → compromised Okta

**Best Practices:**
- ✅ Use strong passwords or password managers
- ✅ Delete keys when no longer needed
- ✅ Delete emails containing keys after downloading
- ✅ Store keys securely (never in public repositories)
- ❌ NEVER commit keys to GitHub
- ❌ NEVER share keys via email
- ❌ NEVER store in Google Drive without strong account security
- ❌ NEVER show keys in screenshots or videos

**Other sensitive credentials to protect:**
- SSH keys
- API access tokens
- Bitcoin wallets
- Any authentication credentials

---

## Setting Up Your Terraform Environment

### Directory Structure:
```
terra-demo/
├── keys/
│   └── my-creds.json
└── main.tf
```

### Creating the Key File:
```bash
mkdir terra-demo
cd terra-demo
mkdir keys
cd keys
nano my-creds.json
# Paste your service account JSON here
# Save and exit
```

### VS Code Extension (Recommended):
- Install "Terraform" extension by HashiCorp
- Provides:
  - Syntax highlighting
  - Autocompletion
  - Helps prevent typos
  - Format assistance

---

## Creating Your First Terraform File

### main.tf Structure:

```hcl
# Provider configuration
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project     = "your-project-id"
  region      = "us-central1"
  credentials = file("./keys/my-creds.json")
}
```

### Finding Your Project ID:
- Go to GCP Dashboard
- Look for "Project ID" (NOT the friendly name)
- Copy the exact project ID

### Setting Region:
- Choose region closest to you or your users
- Example: `us-central1`, `us-east1`, `europe-west1`

---

## Credential Configuration Methods

### Method 1: Hardcode in Provider (Not Recommended)
```hcl
provider "google" {
  credentials = file("./keys/my-creds.json")
  # Other settings...
}
```

### Method 2: Environment Variable (Recommended)
```bash
export GOOGLE_CREDENTIALS="/home/gary/terra-demo/keys/my-creds.json"

# Test it's set correctly:
echo $GOOGLE_CREDENTIALS
```

### Method 3: gcloud SDK (Alternative)
```bash
gcloud auth application-default login
```
- Provides a link for authentication
- Uses your main user account (not service account)

---

## Understanding Terraform Providers

**Analogy:**
- **Provider** = The path to the door
- **Credentials file** = The key that opens the door

**What providers do:**
- Downloaded code that allows Terraform to communicate with GCP
- Platform-specific (Google provider for GCP, AWS provider for AWS, etc.)
- Not human-readable
- Platform and architecture-specific (e.g., Linux AMD64)

---

## Terraform Workflow Commands in Detail

### 1. `terraform init`
**Purpose:** Download provider code

**What it does:**
- Reads your provider configuration
- Downloads the appropriate provider code
- Detects your OS and architecture
- Creates `.terraform/` directory
- Creates `terraform.lock.hcl` file (contains provider version hashes)

**When to run:** First command after creating/cloning a Terraform project

**Output files:**
- `.terraform/` directory (contains provider code)
- `.terraform.lock.hcl` (ensures correct provider version)

---

### 2. `terraform plan`
**Purpose:** Preview changes before applying

**What it shows:**
- Resources to be created (+)
- Resources to be modified (~)
- Resources to be destroyed (-)
- Default values that will be used
- Computed values (known after apply)

**Benefits:**
- **No harm, no foul** - doesn't create any resources
- See default values when not specified in config
- Catch surprises before they happen
- Review costs and settings
- Troubleshoot configuration issues

**Always use before `terraform apply`!**

---

### 3. `terraform apply`
**Purpose:** Create/modify infrastructure

**What it does:**
- Shows the plan again
- Asks for confirmation (type "yes")
- Creates resources as defined in `.tf` files
- Updates `terraform.tfstate` file
- Shows resource details after creation

**State file (`terraform.tfstate`):**
- Tracks all resources Terraform manages
- Contains resource IDs, configuration, metadata
- **CRITICAL:** Don't delete or manually edit this file
- **SENSITIVE:** Contains resource details (keep secure)

**Backup state files:**
- `terraform.tfstate.backup` - previous state
- Used for recovery if needed

---

### 4. `terraform destroy`
**Purpose:** Remove all infrastructure

**What it does:**
- Reads the state file
- Shows what will be destroyed
- Asks for confirmation (type "yes")
- Deletes all resources defined in your Terraform files
- Updates state file to reflect no resources

**When to use:**
- When done with a project
- To avoid ongoing charges
- To start fresh
- During testing/development

---

## Useful Terraform Commands

### `terraform fmt`
**Purpose:** Format your Terraform files

**What it does:**
- Aligns code properly
- Fixes spacing and indentation
- Makes code more readable
- Follows Terraform style conventions

**Usage:**
```bash
terraform fmt
```

**Always run before committing code!**

---

## Creating a Google Cloud Storage Bucket

### Finding Documentation:
1. Search: "Terraform Google Cloud Storage bucket"
2. Look for HashiCorp documentation
3. Find example code and copy it

### Basic Bucket Resource:

```hcl
resource "google_storage_bucket" "demo_bucket" {
  name          = "your-project-id-terra-bucket"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```

### Understanding Resource Blocks:

```hcl
resource "google_storage_bucket" "demo_bucket" {
  # Resource type ↑              ↑ Local name
  # (Important to Terraform)     (Important to you)
}
```

- **Resource type** (`google_storage_bucket`): Tells Terraform what to create
- **Local name** (`demo_bucket`): Variable name for referencing this resource
- **name parameter**: Must be globally unique across ALL of GCP

### Naming Considerations:
- Bucket names must be globally unique (across all GCP projects)
- Local names only need to be unique within your Terraform project
- Tip: Use project ID as prefix (already globally unique)

### Lifecycle Rules:

**Abort Incomplete Multipart Uploads:**
- Large files can be uploaded in chunks (multipart upload)
- Parallel processing makes uploads faster
- If upload fails, incomplete data remains in bucket
- This rule cleans up incomplete uploads after 1 day

### Storage Classes:
- Default is "STANDARD"
- Other options: NEARLINE, COLDLINE, ARCHIVE
- Check Terraform plan to see defaults

---

## Understanding Terraform State

### What is State?
The `terraform.tfstate` file tracks:
- What resources exist
- Their current configuration
- Resource IDs and metadata
- Dependencies between resources

### State File Properties:
- JSON format
- Contains sensitive information
- Updated after every `terraform apply` or `terraform destroy`
- Has a backup file (`terraform.tfstate.backup`)

### State File Contents:
```json
{
  "version": 4,
  "serial": 1,
  "lineage": "unique-id",
  "resources": [
    // Your resource details here
  ]
}
```

- **serial**: Increments with each state change
- **lineage**: Tracks configuration history
- **version**: Terraform state version

---

## Complete Workflow Example

### 1. Initialize:
```bash
terraform init
```
Output: Downloads provider, creates .terraform directory

### 2. Plan:
```bash
terraform plan
```
Output: Shows what will be created (preview)

### 3. Apply:
```bash
terraform apply
```
- Shows plan again
- Type "yes" to confirm
- Creates resources
- Shows resource details

### 4. Verify:
- Check GCP Console
- Verify bucket exists
- Check resource configuration

### 5. Destroy:
```bash
terraform destroy
```
- Shows what will be destroyed
- Type "yes" to confirm
- Removes all resources
- Updates state file

### 6. Verify Cleanup:
- Check GCP Console
- Confirm bucket is gone
- Check state file (should show no resources)

---

## Git and GitHub Considerations

### 🚨 CRITICAL: What NOT to Push to GitHub

**Never commit these files:**
- `*.json` (service account keys)
- `terraform.tfstate` (contains sensitive data)
- `terraform.tfstate.backup`
- `.terraform/` directory (provider binaries)
- Any files with credentials

### Creating .gitignore:

1. **Search for template:**
   - Google "Terraform gitignore"
   - Use standard Terraform .gitignore template

2. **Essential entries:**
```gitignore
# Terraform files
**/.terraform/*
*.tfstate
*.tfstate.*

# Credentials
*.json
keys/
credentials/

# Variable files with sensitive data
*.tfvars
*.auto.tfvars
```

### Best Practices:
- ✅ Create `.gitignore` BEFORE first commit
- ✅ Use private repositories when learning
- ✅ Test your `.gitignore` works before pushing
- ✅ Take incremental steps with security
- ✅ Review what will be pushed before pushing

**GitHub Security Features:**
- GitHub scans for exposed credentials
- May alert you to leaked keys
- May work better for organization accounts
- Don't rely on this as your only protection

### Safe Files to Commit:
- `main.tf` (without hardcoded credentials)
- `.terraform.lock.hcl`
- Documentation files
- `variables.tf` (without default sensitive values)
- `outputs.tf`

---

## Terraform File Types Generated

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `main.tf` | Your infrastructure code | ✅ Yes |
| `.terraform/` | Provider binaries | ❌ No |
| `.terraform.lock.hcl` | Provider version locks | ✅ Yes |
| `terraform.tfstate` | Current infrastructure state | ❌ No |
| `terraform.tfstate.backup` | Previous state | ❌ No |
| `*.json` (keys) | Service account credentials | ❌ NEVER |

---

## Helpful Tips and Best Practices

### Documentation:
- HashiCorp documentation is thorough
- Look for example code in docs
- Search for similar projects on GitHub
- Copy and adapt existing configurations
- Check for nested block documentation

### Workflow Tips:
1. Always run `terraform fmt` before committing
2. Always run `terraform plan` before `terraform apply`
3. Always use `terraform destroy` when done testing
4. Save your work frequently (Ctrl+S)
5. Use descriptive local names for resources

### Debugging:
- Use `terraform plan` to see default values
- Check documentation for parameter details
- Look for nested blocks in resource definitions
- VS Code highlighting helps match brackets

### Cost Management:
- Preview resources with `terraform plan`
- Research costs before deploying
- Set up billing alerts in GCP
- Destroy resources immediately after testing
- Consider using cheaper resource tiers for learning

---

## Next Steps

In future videos, we'll cover:
- Building larger projects with multiple resources
- Using variables to avoid hardcoding values
- Creating reusable variable files
- Managing multiple environments (dev, staging, prod)
- Referencing resources between blocks
- Advanced Terraform features

---

## Quick Reference Card

### Essential Commands:
```bash
# Setup
terraform init                 # Download providers

# Preview
terraform plan                 # See what will change

# Deploy
terraform apply                # Create infrastructure

# Cleanup
terraform destroy              # Remove everything

# Utility
terraform fmt                  # Format code
```

### Authentication:
```bash
# Set credentials via environment variable
export GOOGLE_CREDENTIALS="/path/to/key.json"

# Verify
echo $GOOGLE_CREDENTIALS
```

### Basic Resource Block:
```hcl
resource "provider_resource_type" "local_name" {
  required_parameter = "value"
  optional_parameter = "value"
}
```

---

## Remember:
- 🔑 **Never commit credentials**
- 💰 **Always destroy test resources**
- 👀 **Always plan before apply**
- 🔒 **Treat keys like passwords**
- 📝 **Document your infrastructure**
- 🧹 **Use .gitignore from the start**

---

# Advanced Terraform: Variables and Multiple Resources

## Understanding Terraform State Files (Recap)

### State File Behavior:

**When applying changes:**
- `terraform.tfstate` - Shows current resources
- `terraform.tfstate.backup` - Shows previous state (before this apply)

**When destroying resources:**
- `terraform.tfstate` - Updated to show no resources
- `terraform.tfstate.backup` - Contains the destroyed resources (for recovery)

### State File Recovery:
If something goes wrong during destroy:
1. Terraform state shows resources are gone
2. But resources still exist in GCP
3. Copy `.backup` file contents to `.tfstate`
4. Remove `.backup` extension
5. Run `terraform destroy` again

*Note: This is rarely needed but good to know*

---

## Creating Multiple Resources

### Adding a BigQuery Dataset

**Finding Documentation:**
1. Search: "Terraform BigQuery dataset"
2. Navigate to HashiCorp documentation
3. Look for required vs optional fields

**Reading Documentation Tips:**
- Use Ctrl+F to search for "required"
- Check which fields are mandatory
- Review default values for optional fields
- Look at official docs links for detailed explanations

### BigQuery Dataset Example:

```hcl
resource "google_bigquery_dataset" "demo_data_set" {
  dataset_id = "demo_data_set"
  location   = "US"
  
  # Optional: If you need to delete tables when destroying
  delete_contents_on_destroy = false
}
```

### Key Parameters:

**dataset_id** (Required):
- Unique identifier for the dataset
- Must be unique within your project

**location** (Optional):
- Default: "US" (multi-regional)
- Regional options: "us-central1", "europe-west1", etc.
- Multi-regional options: "US", "EU"
- Important for compliance and billing

**delete_contents_on_destroy** (Optional):
- Default: false
- If true: Deletes all tables when destroying dataset
- If false: Destroy fails if tables exist
- Set to true if you create tables in your dataset

### Location Considerations:
- **Regional**: Specific geographic place (e.g., Tokyo)
- **Multi-regional**: Large geographic area (e.g., US, EU)
- Choose based on:
  - Data residency requirements
  - Latency needs
  - Cost considerations
  - Compliance regulations

---

## Working with Variables

### Why Use Variables?

**Benefits:**
1. **Reusability**: Define once, use everywhere
2. **Maintainability**: Update in one place
3. **Sharing**: Easy for others to customize
4. **Environment Management**: Different values for dev/staging/prod
5. **Cleaner Code**: Separate configuration from logic

### Creating variables.tf

**By convention**, variables are defined in `variables.tf`:

```bash
# Create the file
touch variables.tf
```

### Variable Declaration Syntax:

```hcl
variable "variable_name" {
  description = "Human-readable description"
  default     = "default_value"
  type        = string  # optional: string, number, bool, list, map, etc.
}
```

---

## Practical Variable Examples

### Example 1: Location Variable

```hcl
variable "project_location" {
  description = "Project location"
  default     = "US"
}
```

**Usage in main.tf:**
```hcl
resource "google_storage_bucket" "demo_bucket" {
  location = var.project_location
}

resource "google_bigquery_dataset" "demo_data_set" {
  location = var.project_location
}
```

### Example 2: Project ID Variable

```hcl
variable "project" {
  description = "Project ID"
  default     = "your-project-id"
}
```

**Usage in provider block:**
```hcl
provider "google" {
  project = var.project
  region  = var.region
}
```

### Example 3: Storage Class Variable

```hcl
variable "gcs_storage_class" {
  description = "Bucket storage class"
  default     = "STANDARD"
}
```

**Possible values:**
- STANDARD (default)
- NEARLINE
- COLDLINE
- ARCHIVE

### Example 4: Resource Names

```hcl
variable "bq_dataset_name" {
  description = "BigQuery dataset name"
  default     = "demo_data_set"
}

variable "gcs_bucket_name" {
  description = "Storage bucket name"
  default     = "my-unique-bucket-name"
}
```

---

## Complete variables.tf Example

```hcl
variable "project" {
  description = "Project ID"
  default     = "your-project-id"
}

variable "region" {
  description = "Default region"
  default     = "us-central1"
}

variable "project_location" {
  description = "Project location"
  default     = "US"
}

variable "gcs_bucket_name" {
  description = "Storage bucket name"
  default     = "your-project-terra-bucket"
}

variable "gcs_storage_class" {
  description = "Bucket storage class"
  default     = "STANDARD"
}

variable "bq_dataset_name" {
  description = "BigQuery dataset name"
  default     = "demo_data_set"
}

variable "credentials" {
  description = "Path to credentials file"
  default     = file("./keys/my-creds.json")
}
```

---

## Using Variables in main.tf

### Before Variables (Hardcoded):

```hcl
provider "google" {
  project = "my-project-12345"
  region  = "us-central1"
}

resource "google_storage_bucket" "demo_bucket" {
  name     = "my-project-terra-bucket"
  location = "US"
}
```

### After Variables (Dynamic):

```hcl
provider "google" {
  project     = var.project
  region      = var.region
  credentials = var.credentials
}

resource "google_storage_bucket" "demo_bucket" {
  name          = var.gcs_bucket_name
  location      = var.project_location
  storage_class = var.gcs_storage_class
}

resource "google_bigquery_dataset" "demo_data_set" {
  dataset_id = var.bq_dataset_name
  location   = var.project_location
}
```

---

## Referencing Variables

### Syntax:
```hcl
var.variable_name
```

### Example with Autocomplete:
When you type `var.` in VS Code with the Terraform extension:
- Autocomplete shows all available variables
- Helps prevent typos
- Shows variable descriptions

### Benefits of var. prefix:
- Clear indication that it's a variable
- Easy to search and replace
- Consistent across all Terraform files

---

## The file() Function

### Purpose:
Load the contents of a file into a Terraform variable

### Syntax:
```hcl
file("path/to/file")
```

### Common Use Cases:

**1. Loading Credentials:**
```hcl
variable "credentials" {
  description = "Service account credentials"
  default     = file("./keys/my-creds.json")
}
```

**2. In Provider Block:**
```hcl
provider "google" {
  credentials = var.credentials
}
```

### File Path Options:
```hcl
# Relative to current directory
file("./keys/creds.json")

# Relative path with subdirectory
file("keys/creds.json")

# Absolute path
file("/home/user/keys/creds.json")
```

### Important Notes:
- The `file()` function should be called where the variable is **used**, not where it's declared
- If declaring in `variables.tf`, you might pass just the path as default
- Call `file()` in `main.tf` when actually using the variable

---

## Environment Variables vs Terraform Variables

### Method 1: System Environment Variable (Previous Method)

```bash
export GOOGLE_CREDENTIALS="/path/to/creds.json"
```

**Advantages:**
- Not in Terraform files
- Can be set in shell profile
- Works across multiple projects

**Disadvantages:**
- Must be set every session (unless in .bashrc/.zshrc)
- Not portable with the Terraform code

### Method 2: Terraform Variable with file() Function

```hcl
variable "credentials" {
  description = "Credentials file path"
  default     = file("./keys/my-creds.json")
}

provider "google" {
  credentials = var.credentials
}
```

**Advantages:**
- Portable with the code
- No need to set environment variables
- Clear in the configuration

**Disadvantages:**
- Path must be correct relative to Terraform files
- Still need to gitignore the actual credentials file

### Testing Credential Methods:

**Unsetting environment variable:**
```bash
# Remove the environment variable
unset GOOGLE_CREDENTIALS

# Verify it's gone
echo $GOOGLE_CREDENTIALS
# (should show nothing)
```

**Testing Terraform without credentials:**
```bash
terraform plan
# Should show error about missing credentials
```

**After adding credentials variable:**
```bash
terraform plan
# Should work if variable is configured correctly
```

---

## Error Handling and Troubleshooting

### Common Errors:

**1. "No credentials loaded"**
```
Error: Attempted to load application default credentials
since neither credentials nor access token was set
```

**Solution:**
- Set GOOGLE_CREDENTIALS environment variable, OR
- Add credentials parameter to provider block

**2. "Could not find default credentials"**
```
Error: google: could not find default credentials
```

**Solution:**
- Check file path is correct
- Verify credentials file exists
- Ensure proper JSON formatting in credentials file

**3. "Functions may not be called here"**
```
Error: Functions may not be called here
```

**Solution:**
- Move `file()` function call from variable default to where variable is used
- Call `file()` in main.tf, not in variables.tf default value

**Correct pattern:**
```hcl
# variables.tf
variable "credentials_path" {
  description = "Path to credentials"
  default     = "./keys/my-creds.json"
}

# main.tf
provider "google" {
  credentials = file(var.credentials_path)
}
```

---

## Project Structure Best Practices

### Recommended File Organization:

```
terraform-project/
├── keys/
│   └── my-creds.json          # Credentials (gitignored)
├── main.tf                     # Main infrastructure code
├── variables.tf                # Variable declarations
├── outputs.tf                  # Output values (optional)
├── terraform.tfvars           # Variable values (optional)
├── .gitignore                 # Git ignore rules
├── .terraform/                 # Provider plugins (gitignored)
├── .terraform.lock.hcl        # Provider version locks
├── terraform.tfstate          # State file (gitignored)
└── terraform.tfstate.backup   # State backup (gitignored)
```

### File Purposes:

| File | Purpose | Commit? |
|------|---------|---------|
| `main.tf` | Infrastructure definitions | ✅ Yes |
| `variables.tf` | Variable declarations | ✅ Yes |
| `outputs.tf` | Output definitions | ✅ Yes |
| `terraform.tfvars` | Variable values | ⚠️ Maybe (if no secrets) |
| `*.auto.tfvars` | Auto-loaded variable values | ⚠️ Maybe (if no secrets) |

---

## Variable Files (.tfvars)

### What are .tfvars files?

Variable files allow you to:
- Separate variable values from declarations
- Maintain different configurations (dev, staging, prod)
- Share configurations without hardcoded values

### Creating a terraform.tfvars file:

```hcl
# terraform.tfvars
project          = "my-project-12345"
region           = "us-central1"
project_location = "US"
gcs_bucket_name  = "my-unique-bucket-name"
```

### Using .tfvars files:

**Default file (auto-loaded):**
```bash
# terraform.tfvars is automatically loaded
terraform apply
```

**Custom file:**
```bash
# Specify custom variable file
terraform apply -var-file="production.tfvars"
terraform apply -var-file="development.tfvars"
```

### Example: Multiple Environments

**development.tfvars:**
```hcl
project          = "dev-project"
region           = "us-central1"
project_location = "US"
gcs_bucket_name  = "dev-bucket"
```

**production.tfvars:**
```hcl
project          = "prod-project"
region           = "us-west1"
project_location = "US"
gcs_bucket_name  = "prod-bucket"
```

**Usage:**
```bash
# Deploy to development
terraform apply -var-file="development.tfvars"

# Deploy to production
terraform apply -var-file="production.tfvars"
```

---

## Sharing Terraform Projects

### Scenario: Friend in EU wants to use your project

**What they need to change:**

**Option 1: Edit variables.tf defaults**
```hcl
variable "project_location" {
  description = "Project location"
  default     = "EU"  # Changed from "US"
}

variable "region" {
  description = "Default region"
  default     = "europe-west1"  # Changed from "us-central1"
}
```

**Option 2: Create their own .tfvars file**
```hcl
# eu-config.tfvars
project          = "their-project-id"
region           = "europe-west1"
project_location = "EU"
gcs_bucket_name  = "their-unique-bucket-name"
```

```bash
terraform apply -var-file="eu-config.tfvars"
```

---

## Complete Workflow with Variables

### Step-by-Step Process:

**1. Create Directory Structure:**
```bash
mkdir terraform-project
cd terraform-project
mkdir keys
```

**2. Add Credentials:**
```bash
# Place service account JSON in keys/
cp ~/Downloads/service-account.json keys/my-creds.json
```

**3. Create variables.tf:**
```bash
code variables.tf
# Add all variable declarations
```

**4. Create main.tf:**
```bash
code main.tf
# Add provider and resource configurations using var.variable_name
```

**5. Format Code:**
```bash
terraform fmt
```

**6. Initialize:**
```bash
terraform init
```

**7. Review Plan:**
```bash
terraform plan
```

**8. Apply Changes:**
```bash
terraform apply
# Type 'yes' to confirm
```

**9. Verify in GCP Console:**
- Check that resources were created
- Verify configurations match your variables

**10. Clean Up:**
```bash
terraform destroy
# Type 'yes' to confirm
```

---

## Verification Examples

### Checking Bucket Creation:

**In GCP Console:**
1. Navigate to Cloud Storage → Buckets
2. Before apply: No buckets
3. After apply: Bucket appears with correct name and location
4. After destroy: Bucket is removed

**With Terraform:**
```bash
# Check state file
cat terraform.tfstate | grep -A 5 "google_storage_bucket"
```

### Checking BigQuery Dataset:

**In GCP Console:**
1. Navigate to BigQuery
2. Before apply: No datasets
3. After apply: Dataset appears
4. After destroy: Dataset is removed

---

## Variable Best Practices

### 1. **Use Descriptive Names**
```hcl
# Good
variable "gcs_bucket_name" { }
variable "bq_dataset_name" { }

# Bad
variable "name1" { }
variable "bucket" { }
```

### 2. **Always Include Descriptions**
```hcl
variable "project_location" {
  description = "Geographic location for resources (US, EU, etc.)"
  default     = "US"
}
```

### 3. **Provide Sensible Defaults**
```hcl
variable "gcs_storage_class" {
  description = "Storage class for GCS buckets"
  default     = "STANDARD"  # Most common use case
}
```

### 4. **Group Related Variables**
```hcl
# Project-level settings
variable "project" { }
variable "region" { }

# Storage settings
variable "gcs_bucket_name" { }
variable "gcs_storage_class" { }

# BigQuery settings
variable "bq_dataset_name" { }
variable "bq_location" { }
```

### 5. **Document Expected Values**
```hcl
variable "gcs_storage_class" {
  description = "Storage class: STANDARD, NEARLINE, COLDLINE, or ARCHIVE"
  default     = "STANDARD"
}
```

---

## Terraform fmt Reminder

### Always format before committing:
```bash
# Format all .tf files in current directory
terraform fmt

# Format and show which files were changed
terraform fmt -diff

# Check formatting without making changes
terraform fmt -check
```

### VS Code Autocomplete Benefits:
- Type `var.` to see all available variables
- Reduces typos
- Shows variable descriptions
- Makes refactoring easier

---

## Troubleshooting Variable Issues

### Issue: Variable not recognized
**Symptom:** `var.my_variable` shows error

**Solutions:**
1. Check variable is declared in `variables.tf`
2. Verify spelling matches exactly
3. Run `terraform init` after adding new variables
4. Save files (Ctrl+S)

### Issue: Default value not working
**Symptom:** Terraform asks for value despite default

**Solutions:**
1. Check variable declaration syntax
2. Ensure `default` is spelled correctly
3. Verify value type matches variable type

### Issue: File function fails
**Symptom:** "Could not find file" error

**Solutions:**
1. Verify path is correct relative to where `terraform apply` is run
2. Check file actually exists
3. Use `./` for relative paths
4. Test with absolute path first

---

## Power of Variables - Real Example

### Scenario: Sharing Project with International Team

**Your setup (US):**
```hcl
variable "project_location" { default = "US" }
variable "region" { default = "us-central1" }
```

**EU colleague:**
```hcl
variable "project_location" { default = "EU" }
variable "region" { default = "europe-west1" }
```

**Asia colleague:**
```hcl
variable "project_location" { default = "asia-northeast1" }
variable "region" { default = "asia-northeast1" }
```

### Same main.tf works for everyone:
```hcl
resource "google_storage_bucket" "demo_bucket" {
  name     = var.gcs_bucket_name
  location = var.project_location  # Adapts to each region
}

resource "google_bigquery_dataset" "demo_data_set" {
  dataset_id = var.bq_dataset_name
  location   = var.project_location  # Adapts to each region
}
```

**Result:** One codebase, multiple deployments across different regions!

---

## Summary: Key Concepts

### Variables Enable:
1. ✅ **Reusability** - Define once, use many times
2. ✅ **Maintainability** - Change in one place
3. ✅ **Shareability** - Easy for others to customize
4. ✅ **Flexibility** - Different values for different environments
5. ✅ **Clarity** - Separate config from infrastructure code

### Variable Workflow:
1. Declare variables in `variables.tf`
2. Use variables in `main.tf` with `var.variable_name`
3. Override defaults with `.tfvars` files or command-line flags
4. Format with `terraform fmt`
5. Apply with `terraform apply`

### Commands Learned:
```bash
terraform init       # Download providers
terraform fmt        # Format code
terraform plan       # Preview changes
terraform apply      # Create infrastructure
terraform destroy    # Remove infrastructure
unset VARIABLE_NAME  # Remove environment variable
```

---

## Next Steps and Further Learning

### Topics Not Covered (But Worth Exploring):

1. **terraform.tfvars files**
   - Separate variable values from declarations
   - Different files for different environments
   - Useful for team collaboration

2. **Variable types**
   - String, number, bool
   - Lists and maps
   - Complex types

3. **Output values**
   - Display resource information after creation
   - Pass values between modules
   - Useful for CI/CD pipelines

4. **Modules**
   - Reusable Terraform configurations
   - Community modules
   - Creating your own modules

5. **Remote state**
   - Store state in cloud storage
   - Enable team collaboration
   - State locking

6. **Workspaces**
   - Manage multiple environments
   - Separate state for each workspace
   - Switch between environments easily

### Recommended Next Steps:

1. Practice creating and destroying resources
2. Experiment with different variable configurations
3. Try using `.tfvars` files for different environments
4. Explore more GCP resources (Cloud Functions, Cloud Run, etc.)
5. Look into Terraform modules for reusability

---

## Final Checklist

Before deploying with Terraform:
- ✅ Review variable defaults
- ✅ Run `terraform fmt` to format code
- ✅ Run `terraform plan` to preview changes
- ✅ Verify costs in GCP pricing calculator
- ✅ Check `.gitignore` is properly configured
- ✅ Ensure credentials are secure
- ✅ Have a destroy plan ready

After working with Terraform:
- ✅ Run `terraform destroy` to clean up
- ✅ Verify resources are removed in GCP Console
- ✅ Check state file shows no resources
- ✅ Unset environment variables if needed
- ✅ Remove local credentials if no longer needed

---

## Quick Reference: Variables

### Declaration:
```hcl
variable "name" {
  description = "Description"
  default     = "value"
}
```

### Usage:
```hcl
resource "type" "name" {
  parameter = var.variable_name
}
```

### With file() function:
```hcl
credentials = file(var.credentials_path)
```

### Override at command line:
```bash
terraform apply -var="variable_name=value"
```

### With .tfvars file:
```bash
terraform apply -var-file="custom.tfvars"
```
