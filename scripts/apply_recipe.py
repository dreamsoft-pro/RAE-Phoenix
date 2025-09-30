import yaml
import argparse
import logging
from pathlib import Path
import esprima
import escodegen

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] - %(message)s')
log = logging.getLogger(__name__)

# --- Action Handlers ---

def handle_replace_string(content: str, action: dict) -> str:
    """Handles the 'replace_string' action."""
    old_string = action.get('old')
    new_string = action.get('new')
    if old_string is None or new_string is None:
        log.warning("Skipping 'replace_string' action due to missing 'old' or 'new' value.")
        return content
    
    log.info(f"Replacing string: '{old_string}' -> '{new_string}'")
    return content.replace(old_string, new_string)

def handle_ast_transform(content: str, action: dict) -> str:
    """Handles the 'ast_transform' action for AngularJS factories."""
    log.info("Performing AST transformation (AngularJS factory to TS functions).")
    try:
        code_ast = esprima.parseScript(content, options={'loc': True})
        transformer = AstTransformer(code_ast)
        
        modified_ast = transformer.transform_to_exported_functions()
        if not modified_ast:
            log.warning("AST transform: Could not find a suitable AngularJS factory to transform.")
            return content
        
        return escodegen.generate(to_dict(modified_ast))

    except esprima.Error as e:
        log.error(f"Failed to parse JavaScript file for AST transform: {e}")
        return content
    except Exception as e:
        log.error(f"An error occurred during AST transformation: {e}")
        return content

# --- AST Transformation Logic (specific to AngularJS factory) ---

def to_dict(node):
    """Recursively converts an esprima node to a dictionary."""
    if isinstance(node, esprima.nodes.Node):
        result = {'type': node.type}
        for key in node.keys():
            if key == 'loc':
                continue
            value = getattr(node, key)
            result[key] = to_dict(value)
        return result
    elif isinstance(node, list):
        return [to_dict(item) for item in node]
    elif isinstance(node, dict):
        result = {}
        for key, value in node.items():
            if key == 'loc':
                continue
            result[key] = to_dict(value)
        return result
    else:
        return node

class AstTransformer:
    """Handles AST-based transformations for AngularJS factories."""

    def __init__(self, code_ast):
        self.ast = code_ast

    def find_factory_function_body(self):
        """Finds the body of the factory function."""
        for node in self.ast.body:
            if (
                node.type == 'ExpressionStatement' and
                node.expression.type == 'CallExpression' and
                node.expression.callee.type == 'MemberExpression' and
                node.expression.callee.property.name == 'factory'
            ):
                factory_func = node.expression.arguments[1]
                if factory_func.type == 'FunctionExpression':
                    return factory_func.body.body
        return None

    def get_returned_function_names(self, factory_body):
        """Gets the names of the functions returned by the factory."""
        for node in reversed(factory_body):
            if node.type == 'ReturnStatement' and node.argument.type == 'ObjectExpression':
                return [prop.key.name for prop in node.argument.properties]
        return []

    def transform_to_exported_functions(self):
        """Transforms the factory into a set of exported functions."""
        factory_body = self.find_factory_function_body()
        if not factory_body:
            return None

        returned_function_names = self.get_returned_function_names(factory_body)
        if not returned_function_names:
            return None

        new_body = []
        for node in factory_body:
            if node.type == 'FunctionDeclaration' and node.id.name in returned_function_names:
                export_declaration = esprima.nodes.ExportNamedDeclaration(
                    declaration=node,
                    specifiers=[],
                    source=None
                )
                new_body.append(export_declaration)
            elif node.type != 'ReturnStatement':
                new_body.append(node)

        self.ast.body = new_body
        return self.ast

# --- Main Engine ---

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

def apply_recipe(recipe: dict, file_path: Path, dry_run: bool = True):
    """Applies a loaded recipe to a specific file."""
    log.info(f"Applying recipe '{(recipe.get('name'))}' to file: {file_path}")
    original_content = file_path.read_text()
    modified_content = original_content

    for action in recipe.get('actions', []):
        action_type = action.get('type')
        handler = ACTION_DISPATCHER.get(action_type)
        
        if handler:
            modified_content = handler(modified_content, action)
        else:
            log.warning(f"No handler found for action type: '{action_type}'. Skipping.")

    if modified_content == original_content:
        log.warning("No changes were made to the file.")
        return

    if dry_run:
        log.info("Dry run mode: Changes will not be written to disk.")
        print("\n--- ORIGINAL ---\n")
        print(original_content)
        print("\n--- MODIFIED (dry-run) ---\n")
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
    args = parser.parse_args()

    try:
        recipe = load_recipe(Path(args.recipe))
        apply_recipe(recipe, Path(args.file_path), args.dry_run)
        log.info("Successfully applied recipe.")
    except (FileNotFoundError, yaml.YAMLError) as e:
        log.error(f"Failed to apply recipe: {e}")

if __name__ == "__main__":
    main()