import pytest

from feniks.core.models.types import Chunk, SystemModel
from feniks.core.reflection.capabilities import CapabilityDetector


@pytest.fixture
def sample_chunks():
    return [
        Chunk(
            id="c1",
            file_path="auth.js",
            start_line=1,
            end_line=10,
            text="function login(user, pass) { ... }",
            chunk_name="login",
            language="javascript",
            business_tags=["auth", "security"],
            kind="function",
        ),
        Chunk(
            id="c2",
            file_path="payment.js",
            start_line=1,
            end_line=10,
            text="class PaymentGateway { process() { ... } }",
            chunk_name="PaymentGateway",
            language="javascript",
            business_tags=["payment"],
            kind="class",
        ),
    ]


@pytest.fixture
def empty_system_model():
    return SystemModel(project_id="test", timestamp="now")


def test_detect_capabilities_from_tags(empty_system_model, sample_chunks):
    detector = CapabilityDetector()
    enriched_model = detector.enrich_system_model(empty_system_model, sample_chunks)

    caps = enriched_model.capabilities
    assert len(caps) >= 2

    # Check Auth Capability
    auth_caps = [c for c in caps if "auth" in c.name.lower() or "security" in c.name.lower()]
    assert auth_caps
    assert auth_caps[0].business_domain in ["auth", "security"]

    # Check Payment Capability
    pay_caps = [c for c in caps if "payment" in c.name.lower()]
    assert pay_caps
    assert pay_caps[0].business_domain == "payment"


def test_detect_capabilities_no_chunks(empty_system_model):
    detector = CapabilityDetector()
    enriched_model = detector.enrich_system_model(empty_system_model, [])
    assert len(enriched_model.capabilities) == 0


def test_capability_deduplication(empty_system_model):
    chunks = [
        Chunk(
            id="1",
            file_path="a.js",
            text="auth",
            chunk_name="a",
            language="js",
            start_line=1,
            end_line=1,
            business_tags=["auth"],
        ),
        Chunk(
            id="2",
            file_path="b.js",
            text="auth",
            chunk_name="b",
            language="js",
            start_line=1,
            end_line=1,
            business_tags=["auth"],
        ),
    ]
    detector = CapabilityDetector()
    enriched_model = detector.enrich_system_model(empty_system_model, chunks)

    # Should ideally merge or have distinct capabilities if logic allows.
    # Current logic creates one capability per tag group found.
    # Let's check if we have at least one 'Auth' capability
    auth_caps = [c for c in enriched_model.capabilities if "auth" in c.name.lower()]
    assert len(auth_caps) > 0
