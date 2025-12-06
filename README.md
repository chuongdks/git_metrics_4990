# ON THE REJECTION OF AGENTIC PULL REQUESTS — README

## 1. Setup and Installation

### 1.1 Python Dependencies

The following Python libraries are required to run the feature extraction and ML notebooks. It is highly recommended to use a virtual environment.

You can install all required libraries using pip:

| Library | Purpose |
|-----------------|---------------------------------------------------------------------------------------------|
| pandas | Core data manipulation and handling DataFrames. |
| numpy | Numerical operations. |
| requests | Making HTTP calls to the GitHub API. |
| python-dotenv | Loading environment variables (like the GitHub Token). |
| python-dateutil | Parsing and manipulating dates/times from the API. |
| pyarrow | Required to read the initial Parquet datasets (hf://datasets/hao-li/AIDev/...). |
| readability | Calculates readability metrics (e.g., Flesch Reading Ease). |
| syntok | Used by readability for advanced text tokenization. |
| scikit-learn | Essential for the ML classification and reporting in ML_test.ipynb. |

### 1.2 External Program Dependencies

For the Code Quality feature extraction (features_pr_code_quality.ipynb), two external tools are necessary:

#### Java Runtime Environment (JRE) or JDK
PMD is a Java application. You must have Java (version 8 or newer) installed and configured on your system path.

#### PMD Static Analysis Tool
- **Download:** Obtain the PMD binary distribution (ZIP or JAR) from the official PMD website.
- **Configuration:** Ensure the PMD command (e.g., `pmd` or `java -jar pmd-bin-*.jar`) is accessible, or update your notebook to point to its location.

### 1.3 GitHub API Configuration

To prevent rate limiting and authenticate with GitHub, a Personal Access Token (PAT) is mandatory for the feature extraction process.

1. Go to **Settings → Developer Settings → Personal Access Tokens → Fine-grained Tokens**
2. Create a token with repo read permissions.
3. Create a file named `api_key.env` in the project root with the content:

```env
# api_key.env
GITHUB_API_KEY="YOUR_PERSONAL_ACCESS_TOKEN_HERE"
```
## 2. Project Execution Flow

The project is designed to be run in a two-stage process: **Feature Extraction** followed by **Machine Learning**.
---

## 2.1 Stage 1: Feature Extraction

You must run the following 5 Jupyter notebooks, each generating a distinct set of features and caches.  
The caching logic in the Main Helper Function prevents repeated API calls, which is crucial for large datasets.

### Execution Steps

- `features_repo_dim.ipynb` — Repository Dimension Metrics  
- `features_pr_dim.ipynb` — Pull Request Dimension Metrics  
- `features_pr_dev_exp.ipynb` — Developer Experience Metrics  
- `features_pr_readability.ipynb` — Readability Metrics for PR/Issue Bodies  
- `features_pr_code_quality.ipynb` — Code Quality Metrics via PMD  

### Output

Each of these 5 notebooks will output two final CSV files: one for Accepted PRs and one for Rejected PRs. These files are typically named according to the feature dimension (e.g., repo_metrics_accepted.csv and repo_metrics_rejected.csv).
2.2 Stage 2: Machine Learning

Once all 5 feature extraction notebooks have been successfully run, the final step is to combine the features and run the classification model.

    Run ML_test.ipynb

This notebook will:

Read the 10 final CSV files (2 files x 5 dimensions) generated in Stage 1.
Merge and clean the features into a single dataset.
Define the target variable (Accepted/Rejected).
Train a Classification ML Model (e.g., Logistic Regression, Random Forest, etc., depending on the code).
Output the Classification ML Report (e.g., accuracy, precision, recall, F1-score, confusion matrix).

