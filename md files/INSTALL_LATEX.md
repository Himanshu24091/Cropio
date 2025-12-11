# LaTeX Installation Guide for Converter Project

## 🎯 **Goal: Install LaTeX Only in Project Directory**

Unfortunately, LaTeX distributions (MiKTeX, TeX Live) cannot be installed in Python virtual environments because they are system-level applications. However, we can install them in a way that only affects your project.

## 💡 **Recommended Solution: Portable MiKTeX**

### Option 1: Download MiKTeX Portable Manually

1. **Download MiKTeX Portable:**
   - Go to: https://miktex.org/download
   - Click "Download" for Windows
   - Choose "MiKTeX Portable" 

2. **Extract to Project Directory:**
   ```
   C:\Users\himan\Desktop\converter\latex_portable\miktex\
   ```

3. **Test Installation:**
   ```cmd
   cd C:\Users\himan\Desktop\converter\latex_portable\miktex\bin\x64
   pdflatex --version
   ```

### Option 2: Use Chocolatey (System-wide but clean)

1. **Install Chocolatey** (if not installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. **Install MiKTeX:**
   ```cmd
   choco install miktex
   ```

### Option 3: TinyTeX (Lightweight)

1. **Install TinyTeX in project:**
   ```powershell
   # Download TinyTeX installer
   Invoke-WebRequest -Uri "https://yihui.org/gh/tinytex/tools/install-windows.bat" -OutFile "install-tinytex.bat"
   # Run installer to project directory
   install-tinytex.bat
   ```

## 🔧 **After Installation**

1. **Restart Your Terminal/PowerShell**
2. **Verify Installation:**
   ```cmd
   where pdflatex
   ```
3. **Run Your App:**
   ```cmd
   activate_env.bat
   # or
   run_app.bat
   ```

## ✅ **Your Project is Now Ready!**

- ✅ Virtual environment with Python packages
- ✅ LaTeX processor with timeout improvements  
- ✅ Minimal LaTeX templates to avoid package conflicts
- ✅ Activation scripts for easy environment setup
- ✅ All dependencies managed in project scope

## 🚀 **Quick Start**

1. Install LaTeX (any option above)
2. Run: `run_app.bat`
3. Visit: http://localhost:5000
4. Test LaTeX conversion!

---

## 📁 **Project Structure**

```
converter/
├── venv/                    # Python virtual environment
├── latex_portable/          # LaTeX installation (if using portable)
├── activate_env.bat         # Activate environment
├── run_app.bat             # Run application
├── setup_latex_env.py      # LaTeX environment setup
└── utils/document/latex_processor.py  # Enhanced LaTeX processor
```
