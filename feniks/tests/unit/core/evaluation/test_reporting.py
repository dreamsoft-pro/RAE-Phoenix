import pytest

from feniks.core.evaluation.reporting import ReportGenerator
from feniks.core.models.types import (
    Capability,
    MetaReflection,
    Module,
    ReflectionImpact,
    ReflectionLevel,
    ReflectionScope,
    SystemModel,
)


@pytest.fixture
def sample_system_model():
    model = SystemModel(
        project_id="test-project",
        timestamp="2025-11-26T10:00:00",
        total_modules=2,
        total_files=5,
        total_chunks=10,
        avg_module_complexity=5.0,
    )

    mod_a = Module(
        name="ModuleA",
        module_type="frontend",
        avg_complexity=15.0,  # High complexity
        in_degree=5,
        out_degree=2,
        centrality=0.8,
    )
    mod_b = Module(name="ModuleB", module_type="backend", avg_complexity=2.0)

    model.modules = {"ModuleA": mod_a, "ModuleB": mod_b}
    model.hotspot_modules = ["ModuleA"]
    model.central_modules = ["ModuleA"]

    cap = Capability(name="Auth", description="Login feature", capability_type="feature", confidence=0.9)
    model.capabilities = [cap]

    return model


@pytest.fixture
def sample_reflections():
    return [
        MetaReflection(
            id="ref-1",
            timestamp="2025-11-26",
            project_id="test-project",
            level=ReflectionLevel.REFLECTION,
            scope=ReflectionScope.SYSTEM,
            impact=ReflectionImpact.CRITICAL,
            title="System Critical Issue",
            content="The system is fragile.",
            recommendations=["Fix it now"],
        )
    ]


def test_generator_init(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    assert gen.system_model == sample_system_model
    assert gen.meta_reflections == []


def test_generate_summary(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    summary = gen.generate_summary()

    assert "System Model Report: test-project" in summary
    assert "Total Modules: 2" in summary
    assert "Avg Module Complexity: 5.00" in summary


def test_generate_module_analysis(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    analysis = gen.generate_module_analysis()

    assert "## Module Analysis" in analysis
    assert "ModuleA" in analysis
    assert "Hotspot Modules" in analysis
    assert "High Complexity" in analysis


def test_generate_capability_report(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    report = gen.generate_capability_report()

    assert "## Detected Capabilities" in report
    assert "Auth" in report
    assert "Login feature" in report
    assert "Confidence: 0.90" in report


def test_generate_recommendations_data(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    data = gen.get_recommendations_data()

    assert len(data) > 0
    rec = data[0]
    assert rec["priority"] == "HIGH"
    assert "Hotspot Modules" in rec["title"]
    assert "ModuleA" in rec["modules"]


def test_generate_meta_reflections_report(sample_system_model, sample_reflections):
    gen = ReportGenerator(sample_system_model, meta_reflections=sample_reflections)
    report = gen.generate_meta_reflections_report()

    assert "## Meta-Reflections" in report
    assert "🔴 CRITICAL" in report
    assert "System Critical Issue" in report
    assert "The system is fragile" in report
    assert "- Fix it now" in report


def test_generate_full_report(sample_system_model):
    gen = ReportGenerator(sample_system_model)
    full_report = gen.generate_full_report()

    assert "System Model Report" in full_report
    assert "End of Report" in full_report
    assert "## Module Analysis" in full_report
    assert "## Detected Capabilities" in full_report
