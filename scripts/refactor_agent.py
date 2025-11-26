import argparse
import os
from qdrant_client import QdrantClient
import yaml
from feniks.config.settings import settings
from feniks.utils import get_git_root, get_llm
from feniks.plugins import get_plugin


def score_recipe(recipe, chunk):
    """
    Scores how well a recipe matches a code chunk.
    """
    score = 0
    recipe_tags = recipe.get("tags", [])
    recipe_lang = recipe.get("language")
    chunk_lang = chunk.payload.get("language")
    chunk_kind = chunk.payload.get("meta", {}).get("kind")
    chunk_content = chunk.payload.get("content", "")

    if recipe_lang and chunk_lang and recipe_lang == chunk_lang:
        score += 10

    if chunk_kind and chunk_kind in recipe_tags:
        score += 10

    for tag in recipe_tags:
        if tag in chunk_content:
            score += 5

    return score


def find_best_recipe(recipe_path, chunk):
    """
    Finds the best recipe in a directory for a given chunk.
    """
    if not os.path.isdir(recipe_path):
        if os.path.exists(recipe_path):
            return recipe_path
        else:
            return None

    best_recipe_path = None
    max_score = -1

    for filename in os.listdir(recipe_path):
        if filename.endswith((".yml", ".yaml")):
            filepath = os.path.join(recipe_path, filename)
            try:
                with open(filepath, "r") as f:
                    recipe = yaml.safe_load(f)

                current_score = score_recipe(recipe, chunk)

                if current_score > max_score:
                    max_score = current_score
                    best_recipe_path = filepath
            except Exception as e:
                print(f"Error processing recipe {filepath}: {e}")

    return best_recipe_path


def main():
    parser = argparse.ArgumentParser(description="Refactor agent")
    parser.add_argument("--query", required=True, help="Query for retrieving code chunks")
    parser.add_argument("--recipe", required=True, help="Path to the recipe file or directory")
    parser.add_argument("--limit", type=int, default=3, help="Number of chunks to retrieve")
    args = parser.parse_args()

    config = settings
    client = QdrantClient(host=config.qdrant_host, port=config.qdrant_port)

    chunks = client.search(
        collection_name=config.qdrant_collection,
        query_text=args.query,
        limit=args.limit,
        with_payload=True,
    )

    llm = get_llm()

    for chunk in chunks:
        print(f"Processing chunk {chunk.id} from {chunk.payload['file_path']}...")

        # Dynamic plugin selection
        language = chunk.payload.get("language")
        if not language:
            print(f"Skipping chunk {chunk.id} due to missing language.")
            continue

        try:
            plugin = get_plugin(language)
            print(f"Using '{language}' plugin for chunk {chunk.id}")
        except ValueError as e:
            print(e)
            continue

        # Find best recipe if a directory is provided
        recipe_path = find_best_recipe(args.recipe, chunk)
        if not recipe_path:
            print(f"No suitable recipe found for chunk {chunk.id} in {args.recipe}")
            continue

        print(f"Using recipe: {recipe_path}")
        with open(recipe_path, "r") as f:
            recipe = yaml.safe_load(f)

        prompt = recipe["prompt_template"].format(
            code=chunk.payload["content"],
            file_path=chunk.payload["file_path"],
            description=recipe["description"],
        )

        response = llm.invoke(prompt)
        print("=" * 20)
        print("Refactored code suggestion:")
        print(response.content)
        print("=" * 20)

        # TODO: Apply changes to the file using the selected plugin
        # transformed_code = plugin.transform(chunk.payload["content"], response.content)
        # print("Transformation result:", transformed_code)
