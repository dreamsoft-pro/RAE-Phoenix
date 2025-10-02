import yaml
import argparse
import logging
from pathlib import Path
import sys
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] - %(message)s')
log = logging.getLogger(__name__)

# --- Language Plugins ---

class LanguagePlugin:
    """Abstract base class for language-specific plugins."""
    def parse(self, code: str):
        raise NotImplementedError
    
    def generate(self, code_ast) -> str:
        raise NotImplementedError

    def find_matches(self, pattern: dict, code_ast):
        raise NotImplementedError

class JavaScriptPlugin(LanguagePlugin):
    """Plugin for handling JavaScript code."""
    def __init__(self):
        try:
            import esprima
            import escodegen
            self.esprima = esprima
            self.escodegen = escodegen
        except ImportError:
            log.error("JavaScript dependencies (esprima, escodegen) are not installed. Please run 'pip install esprima escodegen'.")
            sys.exit(1)

    def parse(self, code: str):
        return self.esprima.parse(code, {'loc': True})

    def generate(self, code_ast) -> str:
        return self.escodegen.generate(code_ast)

    def find_matches(self, pattern: dict, code_ast):
        """Finds nodes in the AST that match the given abstract pattern."""
        node_type = pattern.get('node')
        if node_type == 'function_call':
            return self._find_function_calls(pattern, code_ast)
        return []

    def _find_function_calls(self, pattern, code_ast):
        matches = []
        callee_name_pattern = pattern.get('callee_name', '').replace('.*', '(.*)')
        
        def _traverse(node):
            if node.type == 'CallExpression':
                callee_str = self.escodegen.generate(node.callee)
                log.info(f"Checking callee: {callee_str} against pattern: {callee_name_pattern}")
                if re.match(callee_name_pattern, callee_str):
                    matches.append(node)
            
            for key in dir(node):
                if key.startswith('_'):
                    continue
                value = getattr(node, key)
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, 'type'):
                            _traverse(item)
                elif hasattr(value, 'type'):
                    _traverse(value)

        _traverse(code_ast)
        return matches

# --- Action Handlers ---

def handle_replace_string(content: str, action: dict) -> str:
    """Handles the 'replace_string' action."""
    old_string = action.get('old')
    new_string = action.get('new')
    if old_string is None or new_string is None:
        log.warning("Skipping 'replace_string' action due to missing 'old' or 'new' value.")
        return content
    
    log.info(f"Replacing string: '{old_string}' -> '{new_string}'")
    return re.sub(old_string, new_string, content, flags=re.DOTALL)

# --- Pattern Matching Engine ---

def handle_ast_match(content: str, pattern: dict, plugin) -> bool:
    """Handles the 'ast_match' pattern using a language plugin."""
    log.info(f"Checking for AST match with pattern: {pattern}")
    try:
        code_ast = plugin.parse(content)
        matches = plugin.find_matches(pattern, code_ast)
        if matches:
            log.info(f"Found {len(matches)} match(es) for AST pattern.")
            return True
        else:
            log.warning("No match found for AST pattern.")
            return False
    except Exception as e:
        log.error(f"Error during AST matching: {e}")
        return False

def handle_file_contains(content: str, pattern: dict, plugin) -> bool:
    """Handles the 'file_contains' pattern."""
    log.info(f"Checking for file content match...")
    search_pattern = pattern.get('pattern', '')
    if re.search(search_pattern, content, re.DOTALL):
        log.info(f"File content matched pattern: '{search_pattern}'.")
        return True
    else:
        log.warning(f"File content did not match pattern: '{search_pattern}'.")
        return False

PATTERN_CHECKER = {
    'file_contains': handle_file_contains,
    'ast_match': handle_ast_match,
}

def check_patterns(content: str, patterns: list, plugin) -> bool:
    """Checks if the content matches any of the given patterns using a plugin."""
    if not patterns:
        log.warning("No patterns defined in recipe. Assuming match to proceed with actions.")
        return True

    for pattern in patterns:
        pattern_type = pattern.get('type')
        handler = PATTERN_CHECKER.get(pattern_type)
        
        if handler:
            if handler(content, pattern, plugin):
                log.info(f"Successfully matched pattern of type '{pattern_type}'.")
                return True
        else:
            log.warning(f"No handler found for pattern type: '{pattern_type}'. Skipping.")
            
    log.error("No patterns in the recipe matched the file content. Aborting.")
    return False

# --- Main Engine ---

def handle_ast_transform(content: str, action: dict, plugin) -> str:
    """Handles the 'ast_transform' action."""
    log.info("Performing AST transformation.")
    try:
        code_ast = plugin.parse(content)
        # For this specific recipe, we assume a single pattern.
        pattern = action.get('pattern') 
        matches = plugin.find_matches(pattern, code_ast)

        if not matches:
            log.warning("No AST nodes found to transform.")
            return content

        # For simplicity, this example transforms the first match found.
        # A more robust implementation would handle multiple matches.
        node_to_replace = matches[0]
        
        # Extract the factory function
        factory_function = node_to_replace.arguments[1]
        if factory_function.type != 'FunctionExpression':
            log.warning("Second argument to factory is not a function. Skipping.")
            return content

        # Find the return statement in the factory function
        return_statement = None
        for item in factory_function.body.body:
            if item.type == 'ReturnStatement':
                return_statement = item
                break
        
        if not return_statement or return_statement.argument.type != 'ObjectExpression':
            log.warning("No object literal returned from factory. Skipping.")
            return content

        # Generate new functions
        new_functions = []
        for prop in return_statement.argument.properties:
            func_name = prop.key.name
            func_body = plugin.generate(prop.value)
            new_functions.append(f"export const {func_name} = {func_body};")

        new_code = '\n'.join(new_functions)
        
        # Replace the old factory call with the new functions
        # This is a simplification. A real implementation would use a more robust replacement.
        start = node_to_replace.loc.start.line -1 
        end = node_to_replace.loc.end.line
        lines = content.split('\n')
        
        modified_lines = lines[:start] + [new_code] + lines[end:]
        return '\n'.join(modified_lines)

    except Exception as e:
        log.error(f"Error during AST transformation: {e}")
        return content


ACTION_DISPATCHER = {
    'replace_string': handle_replace_string,
    'ast_transform': handle_ast_transform,
}

def load_recipe(recipe_path: Path) -> dict:
    """Loads and parses a YAML recipe file."""
    log.info(f"Loading recipe from: {recipe_path}")
    if not recipe_path.is_file():
        raise FileNotFoundError(f"Recipe file not found at: {recipe_path}")
    with open(recipe_path, 'r') as f:
        return yaml.safe_load(f)

def get_language_plugin(file_path: Path):
    """
    Dynamically selects a language plugin based on the file extension.
    For now, it's hardcoded to return JavaScriptPlugin for .js files.
    """
    if file_path.suffix == '.js':
        log.info("JavaScript file detected. Loading JavaScriptPlugin.")
        return JavaScriptPlugin()
    # In the future, you could add more plugins here, e.g.:
    # elif file_path.suffix == '.py':
    #     return PythonPlugin()
    else:
        log.warning(f"No language plugin found for file extension: {file_path.suffix}")
        return None

def apply_recipe(recipe: dict, file_path: Path, dry_run: bool = True):
    """Applies a loaded recipe to a specific file."""
    log.info(f"Applying recipe '{(recipe.get('name'))}' to file: {file_path}")
    
    plugin = get_language_plugin(file_path)
    if not plugin:
        log.error("Aborting recipe application due to missing language plugin.")
        return

    original_content = file_path.read_text()

    # Check patterns using the plugin if they exist
    patterns = recipe.get('patterns', [])
    if patterns and not check_patterns(original_content, patterns, plugin):
        return

    modified_content = original_content
    for action in recipe.get('actions', []):
        action_type = action.get('type')
        handler = ACTION_DISPATCHER.get(action_type)
        
        if handler:
            # Pass the plugin to handlers that need it
            if action_type in ['ast_transform']:
                modified_content = handler(modified_content, action, plugin)
            else:
                modified_content = handler(modified_content, action)
        else:
            log.warning(f"No handler found for action type: '{action_type}'. Skipping.")

    if modified_content == original_content:
        log.warning("No changes were made to the file.")
        return

    if dry_run:
        log.info("Dry run mode: Changes will not be written to disk.")
        print("""
--- ORIGINAL ---
""")
        print(original_content)
        print("""
--- MODIFIED (dry-run) ---
""")
        print(modified_content)
    else:
        log.info(f"Writing changes to {file_path}")
        file_path.write_text(modified_content)

    log.info("Recipe application finished.")

def main():
    parser = argparse.ArgumentParser(description="Apply a refactoring recipe to a source file.")
    parser.add_argument("--recipe", required=True, help="Path to the recipe YAML file.")
    parser.add_argument("--file-path", required=True, help="Path to the file to be transformed.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without modifying files.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        recipe = load_recipe(Path(args.recipe))
        apply_recipe(recipe, Path(args.file_path), args.dry_run)
        log.info("Successfully applied recipe.")
    except (FileNotFoundError, yaml.YAMLError) as e:
        log.error(f"Failed to apply recipe: {e}")

if __name__ == "__main__":
    main()
