#!/usr/bin/env python3
"""
Quick script to add WTForms imports and form instantiation to converter routes
"""
import os
import re

# Mapping of route files to their corresponding form classes
ROUTE_FORM_MAPPING = {
    'document_converter_routes.py': 'DocumentConverterForm',
    'excel_converter_routes.py': 'ExcelConverterForm',
    'notebook_converter.py': 'NotebookConverterForm'
}

def update_route_file(file_path, form_class):
    """Update a single route file to use WTForms"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if forms import already exists
    if 'from forms import' not in content:
        # Add forms import after existing imports
        import_pattern = r'(from utils\.helpers import.*?\n)'
        if re.search(import_pattern, content):
            content = re.sub(import_pattern, f'\\1from forms import {form_class}\n', content)
        else:
            # Fallback: add after werkzeug import
            werkzeug_pattern = r'(from werkzeug\..*?\n)'
            if re.search(werkzeug_pattern, content):
                content = re.sub(werkzeug_pattern, f'\\1from forms import {form_class}\n', content)
    
    # Update route function to use form
    # Pattern to find the route function and add form instantiation
    route_pattern = r'(@.*?\.route\(.*?\)\n(?:@.*?\n)*def\s+\w+\(\):?\n)(.*?)(\n    if request\.method == [\'"]POST[\'"]:\s*\n)'
    
    def replace_route(match):
        decorators = match.group(1)
        initial_code = match.group(2)
        rest = match.group(3)
        
        # Add form instantiation
        if 'form = ' not in initial_code:
            # Find the allowed_extensions line and add form after it
            if 'allowed_extensions = ' in initial_code:
                initial_code = re.sub(
                    r'(allowed_extensions = .*?\n)',
                    f'\\1    form = {form_class}()\n    \n',
                    initial_code
                )
            else:
                # Add form at the beginning of function body
                initial_code += f'    form = {form_class}()\n    \n'
        
        return decorators + initial_code + rest
    
    if re.search(route_pattern, content, re.DOTALL):
        content = re.sub(route_pattern, replace_route, content, flags=re.DOTALL)
    
    # Update POST request handling
    post_pattern = r'if request\.method == [\'"]POST[\'"]:'
    if re.search(post_pattern, content):
        content = re.sub(post_pattern, 'if form.validate_on_submit():', content)
    
    # Update form field access
    content = re.sub(r'request\.form\.get\([\'"]format[\'"][)]', 'form.format.data', content)
    content = re.sub(r'request\.files\[[\'"]file[\'"]]\s*', 'form.file.data', content)
    content = re.sub(r'request\.files\.get\([\'"]file[\'"][)]', 'form.file.data', content)
    
    # Update template render calls
    template_pattern = r'return render_template\([\'"]([^\'\"]+\.html)[\'"]([^)]*)\)'
    def update_template_call(match):
        template_name = match.group(1)
        existing_args = match.group(2)
        
        if existing_args and existing_args.strip():
            # Add form to existing arguments
            if 'form=' not in existing_args:
                existing_args = existing_args.rstrip() + ', form=form'
        else:
            existing_args = ', form=form'
        
        return f'return render_template(\'{template_name}\'{existing_args})'
    
    content = re.sub(template_pattern, update_template_call, content)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Updated {file_path}")
    return True

def main():
    """Update all converter route files"""
    routes_dir = 'routes'
    
    for route_file, form_class in ROUTE_FORM_MAPPING.items():
        file_path = os.path.join(routes_dir, route_file)
        if os.path.exists(file_path):
            update_route_file(file_path, form_class)
        else:
            print(f"⚠️  File not found: {file_path}")

if __name__ == '__main__':
    main()
