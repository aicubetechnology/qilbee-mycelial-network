# PyPI Publishing Instructions - QMN SDK v0.1.1

## ✅ Preparation Complete

The SDK v0.1.1 has been built and is ready for publication to PyPI.

### Package Details
```
Name: qilbee-mycelial-network
Version: 0.1.1
Python: >=3.9
License: MIT
Author: AICUBE TECHNOLOGY LLC
```

### Built Packages Location
```
sdk/dist/qilbee_mycelial_network-0.1.1-py3-none-any.whl
sdk/dist/qilbee_mycelial_network-0.1.1.tar.gz
```

---

## 📦 What's New in v0.1.1

### Added
- Multi-tenant support with `tenant_id` parameter
- New `hyphal_store()` method for memory storage
- Production environment configuration
- `QMN_TENANT_ID` environment variable support

### Changed
- Updated authentication to use `X-API-Key` and `X-Tenant-ID` headers
- Default API URL changed to production: `https://qmn.qube.aicube.ca`
- API endpoint paths updated for production routing
- Fixed httpx timeout configuration

### Fixed
- HTTP client timeout compatibility
- API URL construction
- Bearer token format

---

## 🔐 Publishing to PyPI

### Option 1: Using PyPI Token (Recommended)

1. **Get your PyPI token** from https://pypi.org/manage/account/token/

2. **Configure the token**:
```bash
cd /Users/kimera/projects/qilbee-mycelial-network/sdk
source ../venv/bin/activate

# Create/update ~/.pypirc file
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-YOUR_TOKEN_HERE
EOF

chmod 600 ~/.pypirc
```

3. **Upload to PyPI**:
```bash
python3 -m twine upload dist/*
```

### Option 2: Using Environment Variable

```bash
cd /Users/kimera/projects/qilbee-mycelial-network/sdk
source ../venv/bin/activate

# Set token as environment variable
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE

# Upload
python3 -m twine upload dist/*
```

### Option 3: Command Line Token

```bash
cd /Users/kimera/projects/qilbee-mycelial-network/sdk
source ../venv/bin/activate

python3 -m twine upload \
  --username __token__ \
  --password pypi-YOUR_TOKEN_HERE \
  dist/*
```

---

## 🧪 Test PyPI First (Optional but Recommended)

Test the upload on Test PyPI before publishing to production:

1. **Create Test PyPI token**: https://test.pypi.org/manage/account/token/

2. **Upload to Test PyPI**:
```bash
python3 -m twine upload \
  --repository testpypi \
  --username __token__ \
  --password pypi-YOUR_TEST_TOKEN_HERE \
  dist/*
```

3. **Install from Test PyPI**:
```bash
pip install --index-url https://test.pypi.org/simple/ qilbee-mycelial-network
```

4. **Test it works**:
```python
import qilbee_mycelial_network
print(qilbee_mycelial_network.__version__)  # Should show 0.1.1
```

5. **If successful, publish to production PyPI** using instructions above

---

## ✅ Verification After Publishing

Once uploaded to PyPI, verify the package:

### 1. Check PyPI Page
Visit: https://pypi.org/project/qilbee-mycelial-network/

Verify:
- ✅ Version shows 0.1.1
- ✅ README displays correctly
- ✅ Metadata is accurate
- ✅ Download links work

### 2. Install from PyPI
```bash
# Create fresh environment
python3 -m venv test_env
source test_env/bin/activate

# Install from PyPI
pip install qilbee-mycelial-network

# Verify version
python3 -c "import qilbee_mycelial_network; print(qilbee_mycelial_network.__version__)"
# Should output: 0.1.1
```

### 3. Test Functionality
```python
from qilbee_mycelial_network import MycelialClient, QMNSettings

# Should work without errors
settings = QMNSettings(
    api_key="test_key",
    tenant_id="test_tenant",
    api_base_url="https://qmn.qube.aicube.ca"
)

print("✅ SDK imported and configured successfully!")
```

---

## 📝 Post-Publishing Checklist

After successful PyPI upload:

- [ ] Verify package on PyPI website
- [ ] Test installation in clean environment
- [ ] Update project README with new version
- [ ] Create GitHub release tag v0.1.1
- [ ] Update CHANGELOG.md if needed
- [ ] Announce release to users
- [ ] Tweet/post on social media (optional)

---

## 🔄 For Future Releases

### Version Bump Process

1. **Update version in 3 files**:
   - `sdk/setup.py` → line 10
   - `sdk/pyproject.toml` → line 7
   - `sdk/qilbee_mycelial_network/__init__.py` → line 8

2. **Update CHANGELOG.md** with new version details

3. **Clean and rebuild**:
```bash
cd sdk
rm -rf dist/ build/ *.egg-info
python3 -m build
```

4. **Publish to PyPI** (using one of the methods above)

---

## 🆘 Troubleshooting

### Error: "File already exists"
- Package with this version already published
- Increment version number and rebuild

### Error: "Invalid credentials"
- Check PyPI token is correct
- Ensure username is `__token__`
- Token should start with `pypi-`

### Error: "Package name conflict"
- Name already taken on PyPI
- Contact PyPI support or choose different name

### Warning: "Missing metadata"
- Ensure setup.py and pyproject.toml are complete
- Check README.md exists

---

## 📧 Need Help?

- **PyPI Help**: https://pypi.org/help/
- **Twine Docs**: https://twine.readthedocs.io/
- **AICUBE Support**: contact@aicube.ca

---

**Status**: ✅ Ready to Publish
**Version**: 0.1.1
**Built**: 2025-11-05
**Repository**: /Users/kimera/projects/qilbee-mycelial-network/sdk
