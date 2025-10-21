# LaTeX Installation for Cropio Converter

## Automatic Installation Failed
The automatic installation could not complete. Please install LaTeX manually using one of these options:

### Option 1: MiKTeX (Recommended for Windows)
1. Visit: https://miktex.org/download
2. Download "MiKTeX Installer" for Windows
3. Run the installer and follow prompts
4. Make sure to enable "Install missing packages on-the-fly"

### Option 2: TeX Live
1. Visit: https://tug.org/texlive/acquire-netinst.html
2. Download the network installer
3. Run and follow installation prompts

### Option 3: Package Manager
If you have a package manager installed:

**Using winget:**
```
winget install MiKTeX.MiKTeX
```

**Using Chocolatey:**
```
choco install miktex
```

**Using Scoop:**
```
scoop install latex
```

### After Installation
1. Restart your terminal/command prompt
2. Test with: `pdflatex --version`
3. Run your Flask app: `python app.py`

The LaTeX converter will work once LaTeX is properly installed and available in your PATH.
