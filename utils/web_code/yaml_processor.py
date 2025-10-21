"""
YAML ⇄ JSON Processor
Handles bidirectional conversion between YAML and JSON formats with validation and formatting.
"""

import yaml
import json
import os
import tempfile
from typing import Dict, Any, Optional, Union
from datetime import datetime
import re

try:
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError as RuamelYAMLError
    RUAMEL_AVAILABLE = True
except ImportError:
    RUAMEL_AVAILABLE = False
    RuamelYAMLError = Exception

class YamlJsonProcessor:
    """Handles conversion between YAML and JSON formats"""
    
    def __init__(self):
        # Configure standard PyYAML
        self.yaml_loader = yaml.SafeLoader
        self.yaml_dumper = yaml.SafeDumper
        
        # Configure ruamel.yaml for better formatting if available
        if RUAMEL_AVAILABLE:
            self.ruamel_yaml = YAML()
            self.ruamel_yaml.preserve_quotes = True
            self.ruamel_yaml.width = 4096
            self.ruamel_yaml.indent(mapping=2, sequence=4, offset=2)
    
    def yaml_to_json(self, yaml_content: str, pretty: bool = True, sort_keys: bool = False) -> Dict[str, Any]:
        """Convert YAML content to JSON format"""
        try:
            if not yaml_content.strip():
                return {
                    'success': False,
                    'error': 'No YAML content provided'
                }
            
            # Try parsing with PyYAML first
            try:
                data = yaml.safe_load(yaml_content)
            except yaml.YAMLError as e:
                # If PyYAML fails, try ruamel.yaml if available
                if RUAMEL_AVAILABLE:
                    try:
                        data = self.ruamel_yaml.load(yaml_content)
                    except RuamelYAMLError as ruamel_error:
                        return {
                            'success': False,
                            'error': f'YAML parsing failed: {str(e)} (ruamel: {str(ruamel_error)})'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'YAML parsing failed: {str(e)}'
                    }
            
            # Handle empty or null documents
            if data is None:
                data = {}
            
            # Convert to JSON string with formatting options
            if pretty:
                json_output = json.dumps(data, indent=2, ensure_ascii=False, sort_keys=sort_keys)
            else:
                json_output = json.dumps(data, ensure_ascii=False, sort_keys=sort_keys, separators=(',', ':'))
            
            return {
                'success': True,
                'output': json_output,
                'stats': {
                    'input_length': len(yaml_content),
                    'output_length': len(json_output),
                    'input_lines': yaml_content.count('\n') + 1,
                    'output_lines': json_output.count('\n') + 1,
                    'data_type': type(data).__name__,
                    'keys_count': len(data) if isinstance(data, dict) else 0,
                    'items_count': len(data) if isinstance(data, list) else 0
                }
            }
            
        except json.JSONEncoder as json_error:
            return {
                'success': False,
                'error': f'JSON encoding failed: {str(json_error)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error during YAML to JSON conversion: {str(e)}'
            }
    
    def json_to_yaml(self, json_content: str, flow_style: bool = False, sort_keys: bool = False) -> Dict[str, Any]:
        """Convert JSON content to YAML format"""
        try:
            if not json_content.strip():
                return {
                    'success': False,
                    'error': 'No JSON content provided'
                }
            
            # Parse JSON
            try:
                data = json.loads(json_content)
            except json.JSONDecodeError as e:
                return {
                    'success': False,
                    'error': f'JSON parsing failed: {str(e)}'
                }
            
            # Convert to YAML string with formatting options
            if RUAMEL_AVAILABLE:
                # Use ruamel.yaml for better formatting
                yaml_output = self._convert_with_ruamel(data, flow_style, sort_keys)
            else:
                # Fallback to PyYAML
                yaml_output = yaml.dump(
                    data, 
                    default_flow_style=flow_style,
                    sort_keys=sort_keys,
                    indent=2,
                    allow_unicode=True,
                    Dumper=self.yaml_dumper
                )
            
            # Clean up the YAML output
            yaml_output = self._clean_yaml_output(yaml_output)
            
            return {
                'success': True,
                'output': yaml_output,
                'stats': {
                    'input_length': len(json_content),
                    'output_length': len(yaml_output),
                    'input_lines': json_content.count('\n') + 1,
                    'output_lines': yaml_output.count('\n') + 1,
                    'data_type': type(data).__name__,
                    'keys_count': len(data) if isinstance(data, dict) else 0,
                    'items_count': len(data) if isinstance(data, list) else 0
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error during JSON to YAML conversion: {str(e)}'
            }
    
    def _convert_with_ruamel(self, data: Any, flow_style: bool, sort_keys: bool) -> str:
        """Convert data to YAML using ruamel.yaml for better formatting"""
        import io
        
        stream = io.StringIO()
        
        # Configure formatting
        self.ruamel_yaml.default_flow_style = flow_style
        self.ruamel_yaml.sort_keys = sort_keys
        
        # Dump to string
        self.ruamel_yaml.dump(data, stream)
        return stream.getvalue()
    
    def _clean_yaml_output(self, yaml_content: str) -> str:
        """Clean up YAML output formatting"""
        lines = yaml_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            cleaned_lines.append(line)
        
        # Remove excessive blank lines at the end
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def validate_yaml(self, yaml_content: str) -> Dict[str, Any]:
        """Validate YAML content and return validation results"""
        try:
            if not yaml_content.strip():
                return {
                    'valid': False,
                    'error': 'No content provided',
                    'line': 0,
                    'column': 0
                }
            
            # Try parsing with PyYAML
            try:
                data = yaml.safe_load(yaml_content)
                
                return {
                    'valid': True,
                    'data_type': type(data).__name__,
                    'size': len(str(data)) if data is not None else 0,
                    'structure': self._analyze_structure(data)
                }
                
            except yaml.YAMLError as e:
                error_info = self._extract_yaml_error_info(str(e))
                return {
                    'valid': False,
                    'error': error_info['message'],
                    'line': error_info['line'],
                    'column': error_info['column']
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'line': 0,
                'column': 0
            }
    
    def validate_json(self, json_content: str) -> Dict[str, Any]:
        """Validate JSON content and return validation results"""
        try:
            if not json_content.strip():
                return {
                    'valid': False,
                    'error': 'No content provided',
                    'line': 0,
                    'column': 0
                }
            
            # Try parsing JSON
            try:
                data = json.loads(json_content)
                
                return {
                    'valid': True,
                    'data_type': type(data).__name__,
                    'size': len(json_content),
                    'structure': self._analyze_structure(data)
                }
                
            except json.JSONDecodeError as e:
                return {
                    'valid': False,
                    'error': e.msg,
                    'line': e.lineno,
                    'column': e.colno
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}',
                'line': 0,
                'column': 0
            }
    
    def _analyze_structure(self, data: Any) -> Dict[str, Any]:
        """Analyze the structure of parsed data"""
        if data is None:
            return {'type': 'null', 'count': 0}
        elif isinstance(data, dict):
            return {
                'type': 'object',
                'keys': len(data),
                'nested_objects': sum(1 for v in data.values() if isinstance(v, dict)),
                'nested_arrays': sum(1 for v in data.values() if isinstance(v, list))
            }
        elif isinstance(data, list):
            return {
                'type': 'array',
                'items': len(data),
                'nested_objects': sum(1 for item in data if isinstance(item, dict)),
                'nested_arrays': sum(1 for item in data if isinstance(item, list))
            }
        elif isinstance(data, str):
            return {'type': 'string', 'length': len(data)}
        elif isinstance(data, (int, float)):
            return {'type': 'number', 'value': data}
        elif isinstance(data, bool):
            return {'type': 'boolean', 'value': data}
        else:
            return {'type': type(data).__name__, 'value': str(data)}
    
    def _extract_yaml_error_info(self, error_message: str) -> Dict[str, Union[str, int]]:
        """Extract line and column information from YAML error message"""
        # Default values
        info = {'message': error_message, 'line': 0, 'column': 0}
        
        # Try to extract line number
        line_match = re.search(r'line (\d+)', error_message)
        if line_match:
            info['line'] = int(line_match.group(1))
        
        # Try to extract column number
        col_match = re.search(r'column (\d+)', error_message)
        if col_match:
            info['column'] = int(col_match.group(1))
        
        # Clean up error message
        if 'while parsing' in error_message:
            info['message'] = error_message.split('while parsing')[0].strip()
        
        return info
    
    def format_yaml(self, yaml_content: str, indent: int = 2, flow_style: bool = False) -> Dict[str, Any]:
        """Format YAML content with specified indentation and style"""
        try:
            # Parse and re-dump with formatting
            data = yaml.safe_load(yaml_content)
            
            formatted_yaml = yaml.dump(
                data,
                default_flow_style=flow_style,
                indent=indent,
                allow_unicode=True,
                sort_keys=False
            )
            
            formatted_yaml = self._clean_yaml_output(formatted_yaml)
            
            return {
                'success': True,
                'output': formatted_yaml,
                'changes': len(yaml_content) != len(formatted_yaml)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Formatting error: {str(e)}'
            }
    
    def format_json(self, json_content: str, indent: int = 2, sort_keys: bool = False) -> Dict[str, Any]:
        """Format JSON content with specified indentation"""
        try:
            # Parse and re-dump with formatting
            data = json.loads(json_content)
            
            formatted_json = json.dumps(
                data,
                indent=indent,
                ensure_ascii=False,
                sort_keys=sort_keys
            )
            
            return {
                'success': True,
                'output': formatted_json,
                'changes': len(json_content) != len(formatted_json)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Formatting error: {str(e)}'
            }
    
    def get_conversion_stats(self, input_content: str, output_content: str, conversion_type: str) -> Dict[str, Any]:
        """Get detailed statistics about the conversion"""
        return {
            'conversion_type': conversion_type,
            'input_size': len(input_content),
            'output_size': len(output_content),
            'size_ratio': len(output_content) / len(input_content) if len(input_content) > 0 else 0,
            'input_lines': input_content.count('\n') + 1,
            'output_lines': output_content.count('\n') + 1,
            'timestamp': datetime.now().isoformat()
        }

def create_sample_yaml() -> str:
    """Create sample YAML content for demonstration"""
    return """# Sample YAML Configuration
app:
  name: "Cropio YAML JSON Converter"
  version: "1.0.0"
  description: "Convert between YAML and JSON formats seamlessly"

server:
  host: "localhost"
  port: 5000
  debug: true

database:
  type: "postgresql"
  host: "localhost"
  port: 5432
  name: "cropio_db"
  credentials:
    username: "admin"
    password: "${DB_PASSWORD}"

features:
  - name: "Real-time Validation"
    enabled: true
    description: "Validate syntax as you type"
  - name: "Format Preservation"
    enabled: true
    description: "Maintain original formatting when possible"
  - name: "Error Highlighting" 
    enabled: true
    description: "Visual error indicators"

logging:
  level: "INFO"
  file: "app.log"
  max_size: "10MB"
  backup_count: 5"""

def create_sample_json() -> str:
    """Create sample JSON content for demonstration"""
    return """{
  "app": {
    "name": "Cropio YAML JSON Converter",
    "version": "1.0.0",
    "description": "Convert between YAML and JSON formats seamlessly"
  },
  "server": {
    "host": "localhost",
    "port": 5000,
    "debug": true
  },
  "database": {
    "type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "name": "cropio_db",
    "credentials": {
      "username": "admin",
      "password": "${DB_PASSWORD}"
    }
  },
  "features": [
    {
      "name": "Real-time Validation",
      "enabled": true,
      "description": "Validate syntax as you type"
    },
    {
      "name": "Format Preservation",
      "enabled": true,
      "description": "Maintain original formatting when possible"
    },
    {
      "name": "Error Highlighting",
      "enabled": true,
      "description": "Visual error indicators"
    }
  ],
  "logging": {
    "level": "INFO",
    "file": "app.log",
    "max_size": "10MB",
    "backup_count": 5
  }
}"""
