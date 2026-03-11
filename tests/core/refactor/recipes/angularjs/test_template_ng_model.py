from unittest.mock import MagicMock

from feniks.core.models.types import Chunk
from feniks.core.refactor.recipe import RefactorPlan, RefactorRisk
from feniks.core.refactor.recipes.angularjs.template_to_jsx import (
    AngularHTMLParser,
    TemplateMetadata,
    TemplateToJsxRecipe,
)


def test_template_parser_ng_model():
    html = '<input type="text" ng-model="vm.user.name" />'
    parser = AngularHTMLParser()
    parser.feed(html)
    jsx = parser.get_jsx()

    assert "value={vm.user.name}" in jsx
    assert "onChange={(e) => handleModelChange('vm.user.name', e.target.value)}" in jsx

    def test_template_to_jsx_ng_model_conversion():
        recipe = TemplateToJsxRecipe()
        html = '<input ng-model="search" />'
        # Chunk doesn't accept content in constructor by keyword, it accepts 'text'
        chunk = Chunk(
            file_path="test.html", text=html, start_line=1, end_line=1, id="1", chunk_name="test", language="html"
        )

        # Need to manually inject the chunk into system model or mock behavior
        # Actually, execute takes chunks directly.

        # Metadata mock extraction
        recipe._extract_template_metadata = MagicMock(
            return_value=TemplateMetadata(
                file_path="test.html",
                raw_html=html,
                interpolations=[],
                directives={"ng-model": ["search"]},
                filters=[],
                controller_ref=None,
                complexity_score=1,
            )
        )
        recipe._find_chunk_by_path = MagicMock(return_value=chunk)

        plan = RefactorPlan(
            recipe_name="angularjs.template-to-jsx",
            project_id="test",
            target_modules=[],
            target_files=["test.html"],
            rationale="test",
            risks=[],
            risk_level=RefactorRisk.LOW,
            estimated_changes=1,
            validation_steps=[],
            metadata={"templates": [{"path": "test.html", "complexity": 1, "directives": ["ng-model"], "filters": []}]},
        )

        result = recipe.execute(plan, [chunk])
        if not result.success:
            print(result.errors)
        assert result.success
        assert "value={search}" in result.file_changes[0].modified_content
