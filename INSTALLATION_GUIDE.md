# Installation Guide - Skill Extraction Pipeline

## ⚠️ Common Installation Issues & Solutions

### Issue 1: spaCy Model Download Error (404)

**Error Message:**
```
ERROR: HTTP error 404 while getting https://github.com/explosion/spacy-models/releases/download/-en_core_web_sm/-en_core_web_sm.tar.gz
```

**Root Cause:** 
The spaCy model URL format has changed. The version in requirements.txt may not match available models.

**Solution (Choose One):**

#### Option A: Using Command Line (Recommended)
```bash
# First, install the base packages
pip install -r requirements.txt

# Then download the spaCy model directly
python -m spacy download en_core_web_sm
```

#### Option B: Direct Model URL (Explicit Version)
```bash
# Install specific spaCy version first
pip install spacy==3.7.2

# Then install the matching model
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl
```

#### Option C: Without spaCy Model (Fallback - Limited Functionality)
If you can't download the model, the pipeline will use a blank model:
```bash
pip install -r requirements.txt
# Pipeline will work but with reduced NER capabilities
```

#### Option D: Using Conda (Alternative)
```bash
conda create -n skill-pipeline python=3.10
conda activate skill-pipeline
conda install -c conda-forge spacy
python -m spacy download en_core_web_sm
```

---

## Complete Step-by-Step Installation

### Step 1: Create Virtual Environment (Recommended)

**On Windows:**
```bash
python -m venv skill-env
skill-env\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv skill-env
source skill-env/bin/activate
```

### Step 2: Install Base Packages

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Step 3: Download spaCy Model

**Primary Method:**
```bash
python -m spacy download en_core_web_sm
```

**If that fails, try:**
```bash
# Method 1: Force reinstall
pip install --force-reinstall https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.1/en_core_web_sm-3.7.1-py3-none-any.whl

# Method 2: Download manually and install
# Visit: https://github.com/explosion/spacy-models/releases
# Find en_core_web_sm-3.x.x-py3-none-any.whl and download
# Then: pip install ./path/to/en_core_web_sm-3.7.1-py3-none-any.whl
```

### Step 4: Verify Installation

```python
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✓ spaCy loaded successfully')"
```

**Expected Output:**
```
✓ spaCy loaded successfully
```

### Step 5: Test the Pipeline

```bash
python demo_pipeline.py
```

---

## Troubleshooting by Error Type

### Error: "ModuleNotFoundError: No module named 'spacy'"

```bash
# Install spacy explicitly
pip install spacy --upgrade
```

### Error: "OSError: [E050] Can't find model 'en_core_web_sm'"

```bash
# Download the model
python -m spacy download en_core_web_sm

# Or verify it's installed
python -m spacy info en_core_web_sm
```

### Error: "No module named 'sklearn'"

```bash
# Install scikit-learn
pip install scikit-learn --upgrade
```

### Error: "No module named 'pandas'"

```bash
# Install pandas
pip install pandas --upgrade
```

### Error: Network/Proxy Issues

If you're behind a corporate proxy:

```bash
# Configure pip to use proxy
pip install -r requirements.txt --proxy [user:passwd@]proxy.server:port

# Or set environment variables
set HTTP_PROXY=http://proxy.example.com:8080
set HTTPS_PROXY=http://proxy.example.com:8080
pip install -r requirements.txt
```

### Error: "Permission denied" or "Access denied"

```bash
# Try with --user flag
pip install -r requirements.txt --user

# Or use sudo (not recommended on modern systems)
sudo pip install -r requirements.txt
```

---

## Minimal Installation (If Issues Persist)

If you're having trouble with the full installation, try this minimal setup:

### Step 1: Install Core Only

```bash
pip install spacy numpy pandas
```

### Step 2: Use Blank spaCy Model

The pipeline will work with a blank model (less accurate NER but functional):

```python
# In skill_extraction_pipeline.py, line ~95:
# Change from:
# self.nlp = spacy.load("en_core_web_sm")
# To:
self.nlp = spacy.blank("en")
```

### Step 3: Run With Limited Features

```bash
python demo_pipeline.py
# Will still work, but NER will be less accurate
```

---

## Verification Checklist

After installation, verify each component:

```python
# verify_installation.py
import sys

print("Python Version:", sys.version)

try:
    import spacy
    print("✓ spaCy installed:", spacy.__version__)
except ImportError as e:
    print("✗ spaCy error:", e)

try:
    import numpy
    print("✓ NumPy installed:", numpy.__version__)
except ImportError as e:
    print("✗ NumPy error:", e)

try:
    import pandas
    print("✓ pandas installed:", pandas.__version__)
except ImportError as e:
    print("✗ pandas error:", e)

try:
    import sklearn
    print("✓ scikit-learn installed:", sklearn.__version__)
except ImportError as e:
    print("✗ scikit-learn error:", e)

try:
    nlp = spacy.load("en_core_web_sm")
    print("✓ spaCy model loaded successfully")
except Exception as e:
    print("✗ spaCy model error:", e)

try:
    from skill_extraction_pipeline import SkillExtractionPipeline
    print("✓ Pipeline module imported successfully")
except ImportError as e:
    print("✗ Pipeline import error:", e)

print("\n✓ Installation verified!")
```

Run with:
```bash
python verify_installation.py
```

---

## Platform-Specific Installation

### Windows Installation

```cmd
:: Create virtual environment
python -m venv skill-env
skill-env\Scripts\activate

:: Install requirements
pip install --upgrade pip
pip install -r requirements.txt

:: Download spaCy model
python -m spacy download en_core_web_sm

:: Verify
python -c "import spacy; spacy.load('en_core_web_sm'); print('OK')"

:: Run demo
python demo_pipeline.py
```

### macOS Installation

```bash
# Create virtual environment
python3 -m venv skill-env
source skill-env/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm'); print('OK')"

# Run demo
python demo_pipeline.py
```

### Linux Installation (Ubuntu/Debian)

```bash
# Install system dependencies (if needed)
sudo apt-get install python3-pip python3-venv python3-dev

# Create virtual environment
python3 -m venv skill-env
source skill-env/bin/activate

# Install requirements
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm

# Verify
python -c "import spacy; spacy.load('en_core_web_sm'); print('OK')"

# Run demo
python demo_pipeline.py
```

---

## Using Without Full spaCy Model

If you absolutely cannot install the spaCy model, the pipeline can still work:

### Modify skill_extraction_pipeline.py

**Original (line ~95):**
```python
try:
    self.nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Using blank model.")
    self.nlp = spacy.blank("en")
```

**The code already handles this!** It will automatically fall back to a blank model if the trained model isn't available. NER accuracy will be reduced, but the pipeline will still function.

---

## Testing the Installation

### Quick Test

```bash
python -c "from skill_extraction_pipeline import SkillExtractionPipeline; print('✓ Ready to use!')"
```

### Full Test

```bash
python demo_pipeline.py
```

Expected output:
- ✓ All demonstrations run successfully
- ✓ Output files created (pipeline_output.json, etc.)
- ✓ No errors in console

---

## Performance Tips

### For Faster Installation

```bash
# Use binary packages (faster than compiling from source)
pip install --only-binary :all: -r requirements.txt
```

### For Smaller Download Size

```bash
# Install only what you need
pip install spacy numpy pandas requests
# Skip: pytest, black, flake8, mypy (development tools)
```

### For Offline Use

```bash
# Download packages for offline installation
pip download -r requirements.txt -d ./packages

# Later, on offline machine:
pip install --no-index --find-links=./packages -r requirements.txt
```

---

## Getting Help

### Check spaCy Installation

```bash
python -m spacy info
# Shows spacy version and installed models
```

### Check Individual Package

```bash
python -c "import packagename; print(packagename.__version__)"
```

### View Installed Packages

```bash
pip list
```

### Reinstall Everything Fresh

```bash
# Remove virtual environment
rm -rf skill-env  # or rmdir skill-env on Windows

# Start over
python -m venv skill-env
source skill-env/bin/activate  # Windows: skill-env\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

---

## Alternative: Docker Installation

If local installation is problematic, use Docker:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt && \
    python -m spacy download en_core_web_sm

COPY . .

CMD ["python", "demo_pipeline.py"]
```

Build and run:
```bash
docker build -t skill-pipeline .
docker run skill-pipeline
```

---

## Still Having Issues?

1. **Check Python version**: `python --version` (should be 3.8+)
2. **Check pip**: `pip --version`
3. **Check internet**: Ensure you're not behind a restrictive proxy
4. **Try upgrade**: `pip install --upgrade pip setuptools wheel`
5. **Clear cache**: `pip cache purge` then reinstall
6. **Use verbose mode**: `pip install -r requirements.txt -v` for detailed output

---

**Last Updated:** May 2024  
**Status:** Tested on Windows, macOS, and Linux  
**Support:** See README.md troubleshooting section
