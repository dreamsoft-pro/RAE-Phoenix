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
        self.factory_node = None

    def _find_factory_node(self):
        """Finds the factory declaration node in the AST."""
        for node in self.ast.body:
            if (
                node.type == 'ExpressionStatement' and
                node.expression.type == 'CallExpression' and
                node.expression.callee.type == 'MemberExpression' and
                node.expression.callee.property.name == 'factory'
            ):
                # Support for multiple factories in one file: transform the first one found.
                self.factory_node = node
                return True
        return False

    def _get_returned_identifier_name(self, factory_body):
        """Finds the name of the identifier in the return statement."""
        for node in reversed(factory_body):
            if node.type == 'ReturnStatement' and node.argument.type == 'Identifier':
                return node.argument.name
        return None

    def _get_function_declarations_from_returned_object(self, factory_body):
        """
        Handles the pattern where an object literal is returned, e.g.,
        return { func1: func1, func2: func2 };
        """
        returned_function_names = []
        for node in reversed(factory_body):
            if node.type == 'ReturnStatement' and node.argument.type == 'ObjectExpression':
                returned_function_names = [prop.key.name for prop in node.argument.properties]
                break
        
        if not returned_function_names:
            return []

        new_body = []
        for node in factory_body:
            if node.type == 'FunctionDeclaration' and node.id.name in returned_function_names:
                export_declaration = esprima.nodes.ExportNamedDeclaration(
                    declaration=node,
                    specifiers=[],
                    source=None
                )
                new_body.append(export_declaration)
        return new_body

    def _get_function_declarations_from_identifier(self, factory_body, identifier_name: str):
        """
        Handles the pattern where a service object is built and its identifier is returned, e.g.,
        var MyService = {}; MyService.func1 = function() {}; return MyService;
        """
        new_body = []
        for node in factory_body:
            if (
                node.type == 'ExpressionStatement' and
                node.expression.type == 'AssignmentExpression' and
                node.expression.left.type == 'MemberExpression' and
                hasattr(node.expression.left.object, 'name') and
                node.expression.left.object.name == identifier_name and
                node.expression.right.type == 'FunctionExpression'
            ):
                func_name = node.expression.left.property.name
                func_body = node.expression.right.body
                func_params = node.expression.right.params

                # Create a new FunctionDeclaration
                func_declaration = esprima.nodes.FunctionDeclaration(
                    id=esprima.nodes.Identifier(name=func_name),
                    params=func_params,
                    body=func_body,
                    generator=False
                )

                # Wrap it in an ExportNamedDeclaration
                export_declaration = esprima.nodes.ExportNamedDeclaration(
                    declaration=func_declaration,
                    specifiers=[],
                    source=None
                )
                new_body.append(export_declaration)
        return new_body

    def transform_to_exported_functions(self):
        """Transforms the factory into a set of exported functions."""
        if not self._find_factory_node():
            return None

        factory_func = self.factory_node.expression.arguments[1]
        if factory_func.type != 'FunctionExpression':
            return None
        
        factory_body = factory_func.body.body
        
        # Try the "return identifier" pattern first
        returned_identifier = self._get_returned_identifier_name(factory_body)
        if returned_identifier:
            log.info(f"Found factory pattern: 'return {returned_identifier}'")
            new_body_nodes = self._get_function_declarations_from_identifier(factory_body, returned_identifier)
        else:
            # Fallback to the "return object literal" pattern
            log.info("Found factory pattern: 'return { ... }'")
            new_body_nodes = self._get_function_declarations_from_returned_object(factory_body)

        if not new_body_nodes:
            return None

        # Replace the original factory declaration with the new exported functions
        original_ast_body = self.ast.body
        new_ast_body = []
        for node in original_ast_body:
            if node == self.factory_node:
                new_ast_body.extend(new_body_nodes)
            else:
                # Preserve other statements in the file (e.g., other factories)
                new_ast_body.append(node)
        
        self.ast.body = new_ast_body
        return self.ast

# --- Pattern Matching Engine ---

def _is_node_match(node, pattern_dict: dict) -> bool:
    """Recursively checks if an AST node matches a pattern dictionary."""
    if not node or not isinstance(pattern_dict, dict):
        return False

    for key, pattern_value in pattern_dict.items():
        if not hasattr(node, key):
            return False
        
        node_value = getattr(node, key)

        if isinstance(pattern_value, dict):
            if not _is_node_match(node_value, pattern_value):
                return False
        elif isinstance(pattern_value, list):
            if not isinstance(node_value, list) or len(node_value) != len(pattern_value):
                return False
            for i, item in enumerate(pattern_value):
                if not _is_node_match(node_value[i], item):
                    return False
        else:
            if node_value != pattern_value:
                return False
    return True

class AstMatcher:
    """Traverses an AST to find if any node matches the given pattern."""

    def __init__(self, pattern: dict):
        self.pattern = pattern
        self.match_found = False

    def visit(self, node):
        if self.match_found or not node:
            return

        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return

        if not hasattr(node, 'type'):
            return

        if _is_node_match(node, self.pattern):
            self.match_found = True
            return

        # Manually traverse known properties that can contain child nodes
        for prop in ['body', 'expression', 'callee', 'object', 'property', 'arguments', 'declarations', 'init', 'update', 'test', 'consequent', 'alternate', 'left', 'right', 'elements', 'id', 'params', 'argument']:
            if hasattr(node, prop):
                child = getattr(node, prop)
                self.visit(child)

def handle_ast_match(content: str, pattern: dict) -> bool:
    """Handles the 'ast_match' pattern by parsing and traversing the AST."""
    log.info("Checking for AST match...")
    try:
        code_ast = esprima.parseScript(content, options={'loc': True, 'tolerant': True})
        
        match_pattern = pattern.get('match', {})

        matcher = AstMatcher(match_pattern)
        matcher.visit(code_ast)
        
        if matcher.match_found:
            log.info("AST pattern matched.")
        else:
            log.warning("AST pattern did not match.")
            
        return matcher.match_found
    except esprima.Error as e:
        log.error(f"Failed to parse JavaScript for AST matching: {e}")
        return False
    except Exception as e:
        log.error(f"An error occurred during AST matching: {e}", exc_info=True)
        return False

PATTERN_CHECKER = {
    'ast_match': handle_ast_match,
}

def check_patterns(content: str, patterns: list) -> bool:
    """Checks if the content matches any of the given patterns."""
    if not patterns:
        log.warning("No patterns defined in recipe. Assuming match to proceed with actions.")
        return True

    for pattern in patterns:
        pattern_type = pattern.get('type')
        handler = PATTERN_CHECKER.get(pattern_type)
        
        if handler:
            if handler(content, pattern):
                log.info(f"Successfully matched pattern of type '{pattern_type}'.")
                return True
        else:
            log.warning(f"No handler found for pattern type: '{pattern_type}'. Skipping.")
            
    log.error("No patterns in the recipe matched the file content. Aborting.")
    return False

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

    # First, check if any pattern matches before proceeding
    if not check_patterns(original_content, recipe.get('patterns', [])):
        return

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