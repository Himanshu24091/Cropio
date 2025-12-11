# utils/latex_utils.py

import os
import re
import time
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote
from flask import current_app, url_for

# Optional imports for enhanced functionality
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    from pdfplumber import PDF
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

class LatexProcessor:
    """LaTeX document processing and compilation utilities"""
    
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
        self.latex_engines = ['pdflatex', 'xelatex', 'lualatex']
        self.required_packages = ['latex', 'pdflatex', 'texlive']
        
    def check_system_requirements(self):
        """Check if LaTeX system requirements are met"""
        requirements = []
        
        # Check for LaTeX engines
        for engine in self.latex_engines:
            try:
                result = subprocess.run(
                    [engine, '--version'], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.split('\n')[0]
                    requirements.append({
                        'name': f'{engine.upper()} Engine',
                        'status': f'Available - {version_line}',
                        'met': True
                    })
                    break
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        else:
            requirements.append({
                'name': 'LaTeX Engine',
                'status': 'No LaTeX engine found (pdflatex, xelatex, lualatex)',
                'met': False
            })
        
        # Check for common LaTeX packages
        try:
            result = subprocess.run(
                ['kpsewhich', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                requirements.append({
                    'name': 'Package Manager',
                    'status': 'kpsewhich available for package detection',
                    'met': True
                })
            else:
                requirements.append({
                    'name': 'Package Manager',
                    'status': 'kpsewhich not available',
                    'met': False
                })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            requirements.append({
                'name': 'Package Manager',
                'status': 'Package manager not found',
                'met': False
            })
        
        # Check for PDF processing libraries
        pdf_libs = []
        if PYPDF2_AVAILABLE:
            pdf_libs.append('PyPDF2')
        if PDFPLUMBER_AVAILABLE:
            pdf_libs.append('pdfplumber')
        if PYMUPDF_AVAILABLE:
            pdf_libs.append('PyMuPDF')
        
        if pdf_libs:
            requirements.append({
                'name': 'PDF Processing',
                'status': f'Available libraries: {", ".join(pdf_libs)}',
                'met': True
            })
        else:
            requirements.append({
                'name': 'PDF Processing',
                'status': 'No PDF processing libraries found',
                'met': False
            })
        
        return requirements
    
    def validate_latex(self, latex_content):
        """Validate LaTeX syntax and structure"""
        results = []
        
        # Basic syntax checks
        if not latex_content.strip():
            return [{
                'type': 'info',
                'message': 'Enter LaTeX code to validate'
            }]
        
        # Check for document structure
        has_documentclass = r'\documentclass' in latex_content
        has_begin_document = r'\begin{document}' in latex_content
        has_end_document = r'\end{document}' in latex_content
        
        if not has_documentclass:
            results.append({
                'type': 'warning',
                'message': 'Missing \\documentclass declaration. Auto-wrap is recommended.'
            })
        
        if not has_begin_document or not has_end_document:
            results.append({
                'type': 'warning',
                'message': 'Missing document environment. Auto-wrap is recommended.'
            })
        
        # Check for balanced braces
        open_braces = latex_content.count('{')
        close_braces = latex_content.count('}')
        if open_braces != close_braces:
            results.append({
                'type': 'error',
                'message': f'Unbalanced braces: {open_braces} opening, {close_braces} closing'
            })
        
        # Check for balanced math environments
        math_delimiters = [('$', '$'), ('\\(', '\\)'), ('\\[', '\\]')]
        for open_delim, close_delim in math_delimiters:
            open_count = latex_content.count(open_delim)
            close_count = latex_content.count(close_delim)
            if open_count != close_count:
                results.append({
                    'type': 'error',
                    'message': f'Unbalanced math delimiters: {open_delim}...{close_delim}'
                })
        
        # Check for common LaTeX commands and environments
        common_envs = ['itemize', 'enumerate', 'table', 'figure', 'equation']
        for env in common_envs:
            begin_pattern = rf'\\begin\{{{env}\}}'
            end_pattern = rf'\\end\{{{env}\}}'
            begin_count = len(re.findall(begin_pattern, latex_content))
            end_count = len(re.findall(end_pattern, latex_content))
            if begin_count != end_count:
                results.append({
                    'type': 'error',
                    'message': f'Unbalanced {env} environment: {begin_count} begin, {end_count} end'
                })
        
        # Check for undefined references
        label_refs = set(re.findall(r'\\ref\{([^}]+)\}', latex_content))
        defined_labels = set(re.findall(r'\\label\{([^}]+)\}', latex_content))
        undefined_refs = label_refs - defined_labels
        if undefined_refs:
            results.append({
                'type': 'warning',
                'message': f'Undefined references: {", ".join(undefined_refs)}'
            })
        
        # Check for common packages that might be needed
        content_indicators = {
            r'\\includegraphics': 'graphicx',
            r'\\href': 'hyperref',
            r'\\url': 'url',
            r'\\begin\{tabular\}': 'array (usually included by default)',
            r'\\textcolor': 'xcolor',
            r'\\begin\{lstlisting\}': 'listings'
        }
        
        missing_packages = []
        for pattern, package in content_indicators.items():
            if re.search(pattern, latex_content):
                if f'\\usepackage{{{package.split()[0]}}}' not in latex_content:
                    missing_packages.append(package)
        
        if missing_packages:
            results.append({
                'type': 'info',
                'message': f'Consider adding packages: {", ".join(missing_packages)}'
            })
        
        # If no issues found
        if not results:
            results.append({
                'type': 'success',
                'message': 'LaTeX syntax appears valid!'
            })
        
        return results
    
    def compile_to_pdf(self, latex_content, auto_wrap=True, include_log=False):
        """Compile LaTeX content to PDF"""
        start_time = time.time()
        
        try:
            # Auto-wrap content if needed
            if auto_wrap and not self._has_document_structure(latex_content):
                latex_content = self._wrap_in_document(latex_content)
            
            # Create temporary directory for compilation
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write LaTeX content to file
                tex_file = os.path.join(temp_dir, 'document.tex')
                with open(tex_file, 'w', encoding='utf-8') as f:
                    f.write(latex_content)
                
                # Compile LaTeX to PDF
                result = self._run_latex_compilation(temp_dir, include_log)
                
                if result['success']:
                    # Move PDF to uploads directory
                    pdf_path = self._save_pdf_output(result['pdf_path'])
                    pdf_url = url_for('file_serving.serve_file', 
                                    filename=os.path.basename(pdf_path), 
                                    _external=False)
                    
                    compilation_time = round(time.time() - start_time, 2)
                    
                    return {
                        'success': True,
                        'pdf_path': pdf_path,
                        'pdf_url': pdf_url,
                        'compilation_time': compilation_time,
                        'log': result.get('log') if include_log else None
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Compilation failed'),
                        'log': result.get('log') if include_log else None
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Compilation error: {str(e)}',
                'log': None
            }
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from PDF file"""
        try:
            text_content = ""
            
            # Try PyMuPDF first (best quality)
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text_content += page.get_text()
                doc.close()
            
            # Fallback to pdfplumber
            elif PDFPLUMBER_AVAILABLE:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content += page_text + "\n"
            
            # Fallback to PyPDF2
            elif PYPDF2_AVAILABLE:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text_content += page.extract_text() + "\n"
            
            else:
                return {
                    'success': False,
                    'error': 'No PDF processing libraries available'
                }
            
            if text_content.strip():
                return {
                    'success': True,
                    'text': text_content.strip()
                }
            else:
                return {
                    'success': False,
                    'error': 'No text content could be extracted from the PDF'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Text extraction failed: {str(e)}'
            }
    
    def _has_document_structure(self, latex_content):
        """Check if LaTeX content has complete document structure"""
        return (r'\documentclass' in latex_content and 
                r'\begin{document}' in latex_content and 
                r'\end{document}' in latex_content)
    
    def _wrap_in_document(self, latex_content):
        """Wrap LaTeX content in basic document structure"""
        # Check if content appears to be a resume/CV
        is_resume = any(keyword in latex_content.lower() for keyword in 
                       ['education', 'experience', 'skills', 'resume', 'cv'])
        
        if is_resume:
            header = r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{titlesec}

\geometry{margin=0.75in}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{\baselineskip}{0.5\baselineskip}

\begin{document}

"""
        else:
            header = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}

\geometry{margin=1in}

\begin{document}

"""
        
        footer = r"""
\end{document}"""
        
        return header + latex_content + footer
    
    def _run_latex_compilation(self, temp_dir, include_log=False):
        """Run LaTeX compilation process"""
        tex_file = os.path.join(temp_dir, 'document.tex')
        pdf_file = os.path.join(temp_dir, 'document.pdf')
        log_file = os.path.join(temp_dir, 'document.log')
        
        # Find available LaTeX engine
        latex_engine = None
        for engine in self.latex_engines:
            if shutil.which(engine):
                latex_engine = engine
                break
        
        if not latex_engine:
            return {
                'success': False,
                'error': 'No LaTeX engine found. Please install TeX Live or MiKTeX.'
            }
        
        try:
            # Run LaTeX compilation (twice for references)
            for i in range(2):
                result = subprocess.run([
                    latex_engine,
                    '-interaction=nonstopmode',
                    '-output-directory', temp_dir,
                    tex_file
                ], capture_output=True, text=True, timeout=60)
            
            # Check if PDF was generated
            if os.path.exists(pdf_file):
                response = {
                    'success': True,
                    'pdf_path': pdf_file
                }
                
                # Include compilation log if requested
                if include_log and os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            response['log'] = f.read()
                    except Exception:
                        response['log'] = 'Could not read compilation log'
                
                return response
            else:
                # Compilation failed, try to get error from log
                error_message = 'PDF generation failed'
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            log_content = f.read()
                            # Extract error messages
                            error_lines = [line for line in log_content.split('\n') 
                                         if 'error' in line.lower() or 'fatal' in line.lower()]
                            if error_lines:
                                error_message = error_lines[0][:200]  # Limit error message length
                    except Exception:
                        pass
                
                return {
                    'success': False,
                    'error': error_message,
                    'log': log_content if include_log and 'log_content' in locals() else None
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'LaTeX compilation timed out (60 seconds)'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error': f'LaTeX engine {latex_engine} not found'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Compilation error: {str(e)}'
            }
    
    def _save_pdf_output(self, temp_pdf_path):
        """Save compiled PDF to uploads directory"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        timestamp = str(int(time.time()))
        pdf_filename = f'latex_output_{timestamp}.pdf'
        pdf_path = os.path.join(upload_folder, pdf_filename)
        
        # Copy PDF from temp directory to uploads
        shutil.copy2(temp_pdf_path, pdf_path)
        
        return pdf_path
    
    def get_latex_templates(self):
        """Get predefined LaTeX templates"""
        templates = {
            'resume': {
                'name': 'Professional Resume',
                'description': 'Clean resume template with sections for education, experience, and skills',
                'content': r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{enumitem}
\usepackage{titlesec}

\geometry{margin=0.75in}
\pagestyle{empty}

\titleformat{\section}{\large\bfseries}{}{0em}{}[\titlerule]
\titlespacing*{\section}{0pt}{\baselineskip}{0.5\baselineskip}

\begin{document}

\begin{center}
    {\LARGE \textbf{Your Name}}\\
    \vspace{0.2cm}
    Email: your.email@example.com | Phone: +1 (555) 123-4567\\
    LinkedIn: linkedin.com/in/yourprofile | GitHub: github.com/yourusername
\end{center}

\section{Education}
\textbf{Your University} \hfill \textit{Year - Year}\\
Bachelor of Technology - Computer Science \hfill CGPA: 8.5/10

\section{Technical Skills}
\begin{itemize}[leftmargin=*]
    \item \textbf{Programming Languages:} Python, Java, JavaScript, C++
    \item \textbf{Databases:} MySQL, PostgreSQL, MongoDB
    \item \textbf{Tools \& Technologies:} Git, Docker, AWS, React
\end{itemize}

\section{Experience}
\textbf{Software Developer Intern} \hfill \textit{Company Name | Month Year - Month Year}
\begin{itemize}[leftmargin=*]
    \item Developed web applications using React and Node.js
    \item Collaborated with cross-functional teams on agile projects
    \item Improved application performance by 30\% through optimization
\end{itemize}

\section{Projects}
\textbf{Project Name} \hfill \textit{Technologies Used}
\begin{itemize}[leftmargin=*]
    \item Brief description of what the project does
    \item Key achievements and impact
    \item Link: github.com/yourusername/project
\end{itemize}

\end{document}"""
            },
            
            'article': {
                'name': 'Academic Article',
                'description': 'Standard article template for academic writing',
                'content': r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{graphicx}

\geometry{margin=1in}

\title{Your Article Title}
\author{Your Name}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
This is the abstract of your article. Provide a brief summary of the main points and conclusions.
\end{abstract}

\section{Introduction}
This is the introduction section. Explain the background and motivation for your work.

\section{Methodology}
Describe your approach and methods here.

\subsection{Data Collection}
Explain how you collected your data.

\subsection{Analysis}
Describe your analysis methods.

\section{Results}
Present your findings here.

\section{Conclusion}
Summarize your conclusions and future work.

\bibliographystyle{plain}
\bibliography{references}

\end{document}"""
            },
            
            'report': {
                'name': 'Business Report',
                'description': 'Professional report template with title page and sections',
                'content': r"""\documentclass[12pt]{report}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{fancyhdr}
\usepackage{tocloft}

\geometry{margin=1in}
\pagestyle{fancy}

\title{Report Title}
\author{Your Name}
\date{\today}

\begin{document}

\begin{titlepage}
    \centering
    \vspace*{2cm}
    
    {\LARGE\bfseries Report Title\par}
    \vspace{1.5cm}
    
    {\large Prepared by\par}
    \vspace{0.5cm}
    {\Large Your Name\par}
    \vspace{1cm}
    
    {\large Organization Name\par}
    \vspace{2cm}
    
    {\large \today\par}
    
    \vfill
\end{titlepage}

\tableofcontents
\newpage

\chapter{Executive Summary}
Provide a high-level overview of your report.

\chapter{Introduction}
\section{Background}
Explain the context and background.

\section{Objectives}
List your objectives and goals.

\chapter{Analysis}
\section{Data Overview}
Present your data and methodology.

\section{Findings}
Discuss your key findings.

\chapter{Recommendations}
Provide actionable recommendations based on your analysis.

\chapter{Conclusion}
Summarize the key points and conclusions.

\end{document}"""
            },
            
            'letter': {
                'name': 'Formal Letter',
                'description': 'Professional letter template with proper formatting',
                'content': r"""\documentclass{letter}
\usepackage[utf8]{inputenc}
\usepackage{geometry}

\geometry{margin=1in}

\address{Your Name\\Your Address\\City, State ZIP\\your.email@example.com}

\begin{document}

\begin{letter}{Recipient Name\\Recipient Title\\Company Name\\Company Address\\City, State ZIP}

\opening{Dear Recipient Name,}

This is the opening paragraph of your letter. State the purpose of your letter clearly.

This is the body of your letter. Provide details, explanations, or information as needed. You can have multiple paragraphs here.

This is the closing paragraph. Summarize your main points and indicate any next steps or actions you expect.

\closing{Sincerely,}

\end{letter}

\end{document}"""
            }
        }
        
        return templates
    
    def cleanup_old_files(self, max_age_hours=24):
        """Clean up old generated PDF files"""
        try:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(upload_folder):
                if filename.startswith('latex_output_') and filename.endswith('.pdf'):
                    filepath = os.path.join(upload_folder, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        current_app.logger.info(f"Cleaned up old LaTeX PDF: {filename}")
                        
        except Exception as e:
            current_app.logger.error(f"Error cleaning up LaTeX files: {str(e)}")
