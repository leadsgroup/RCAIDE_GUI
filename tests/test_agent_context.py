"""Regression tests for context bounding, API validation, and grounding."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from agent_service.context import (
    build_agent_context,
    compact_value,
    find_project_parameters,
    inspect_project,
    summarize_mission_results,
    summarize_vehicle_parameters,
)
from agent_service import bootstrap
from agent_service import provider
from agent_service.provider import _response_text
from agent_service.provider import _ground_response, _messages_with_live_status
from agent_server import model
from agent_server.model import (
    _bounded_context_text,
    _bounded_messages,
    _model_response_text,
)
from agent_server.app import Message
from tabs.ai_assistant.chat_widgets import prepare_attachment


# Repository-relative fixture paths keep tests independent of the launch folder.
ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# Project inspection, sanitization, and context-size behavior
# ---------------------------------------------------------------------------

def test_empty_project_reports_required_setup():
    result = inspect_project({})
    codes = {item["code"] for item in result["diagnostics"]}
    assert {"vehicle_missing", "analyses_missing", "mission_missing"} <= codes


def test_sample_aircraft_is_summarized_without_mutation():
    path = ROOT / "app_data" / "aircraft" / "Cessna_172.json"
    project = json.loads(path.read_text(encoding="utf-8"))
    original_tag = project["rcaide_vehicle"]["tag"]

    result = inspect_project(project)

    assert result["vehicle_tag"] == "Cessna_172"
    assert result["components"]["wings"] >= 1
    assert project["rcaide_vehicle"]["tag"] == original_tag


def test_context_bounds_deep_and_long_input():
    # Construct data deeper and longer than the production context limits.
    project = {"rcaide_vehicle": {"tag": "x", "nested": {}}}
    cursor = project["rcaide_vehicle"]["nested"]
    for index in range(12):
        cursor[str(index)] = {}
        cursor = cursor[str(index)]
    project["notes"] = "a" * 10_000

    context = build_agent_context(project, "e" * 10_000)

    assert "<nested data omitted>" in json.dumps(context["project"])
    assert len(context["latest_error"]) == 4_000
    assert len(compact_value(project["notes"])) < 4_010


def test_hosted_service_text_is_extracted():
    assert _response_text({"message": "Hello from RCAIDE"}) == "Hello from RCAIDE"


def test_remote_context_redacts_paths_and_secrets():
    # Neither Windows usernames nor credential-like fields may reach the model.
    context = build_agent_context({
        "rcaide_vehicle": {"tag": "test", "wings": {"main": {}}},
        "source_file": r"C:\Users\Someone\private\airfoil.dat",
        "api_token": "do-not-send",
    }, r"Traceback at C:\Users\Someone\project\run.py")
    serialized = json.dumps(context)
    assert "Someone" not in serialized
    assert "do-not-send" not in serialized
    assert "<sensitive value omitted>" in serialized


# ---------------------------------------------------------------------------
# Desktop-to-FastAPI request contract and authoritative live-state injection
# ---------------------------------------------------------------------------

def test_desktop_client_contract(monkeypatch):
    # Replace network I/O with a context-manager response matching urlopen.
    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"message":"Natural RCAIDE answer"}'

    # Capture the outgoing request so its URL, body, and timeout can be asserted.
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("RCAIDE_AGENT_SERVICE_URL", "https://assistant.example")
    monkeypatch.setattr(provider, "urlopen", fake_urlopen)
    answer = provider.generate_reply(
        [{"role": "user", "content": "What does this GUI do?"}],
        {"inspection": {"vehicle_tag": "test"}},
    )
    assert answer == "Natural RCAIDE answer"
    assert captured["url"] == "https://assistant.example/api/chat"
    assert captured["body"]["messages"][-1]["role"] == "user"
    assert captured["body"]["context"]["inspection"]["vehicle_tag"] == "test"


def test_desktop_client_injects_authoritative_loaded_result_status():
    messages = _messages_with_live_status(
        [{"role": "user", "content": "Summarize the run"}],
        {
            "runtime": {"mission_results_available": True},
            "mission_results": {"segment_count": 9},
        },
    )
    assert "completed mission result object is loaded" in messages[-1]["content"]
    assert "9 segment(s)" in messages[-1]["content"]


def test_desktop_client_embeds_actual_vehicle_values_in_latest_turn():
    messages = _messages_with_live_status(
        [{"role": "user", "content": "Describe the wing"}],
        {
            "runtime": {},
            "vehicle_parameter_inventory": {
                "parameters": [{
                    "path": "rcaide_vehicle.wings.main_wing.spans.projected",
                    "value": 35.8,
                    "unit": "m",
                }],
            },
        },
    )
    content = messages[-1]["content"]
    assert "Describe the wing" in content
    assert "rcaide_vehicle.wings.main_wing.spans.projected = 35.8 m" in content


# ---------------------------------------------------------------------------
# Deterministic grounding fallbacks for known model contradictions
# ---------------------------------------------------------------------------

def test_false_no_results_answer_is_replaced_with_verified_summary():
    context = {
        "runtime": {"mission_results_available": True},
        "mission_results": {
            "segment_count": 1,
            "segments": [{
                "tag": "cruise",
                "series": {
                    "true_airspeed": {
                        "unit": "m/s", "minimum": 50, "maximum": 60,
                        "first": 50, "last": 60,
                    },
                },
            }],
        },
    }
    answer = _ground_response("There are no mission simulation results.", context)
    assert "completed mission run **is loaded**" in answer
    assert "50 to 60 m/s" in answer


def test_vehicle_inventory_exposes_real_values_for_broad_question():
    # Use a real bundled aircraft to protect exact parameter extraction behavior.
    project = json.loads(
        (ROOT / "app_data" / "aircraft" / "Boeing_737_800.json").read_text(encoding="utf-8")
    )
    inventory = summarize_vehicle_parameters(project, "What is in Vehicle Setup?")
    by_path = {item["path"]: item for item in inventory["parameters"]}

    assert by_path["rcaide_vehicle.mass_properties.max_takeoff"] == {
        "path": "rcaide_vehicle.mass_properties.max_takeoff",
        "value": 79000.0,
        "unit": "kg",
    }
    assert by_path["rcaide_vehicle.wings.main_wing.spans.projected"]["value"] == 35.8
    assert inventory["total_scalar_parameters_found"] > 1_000


def test_generic_nested_parameter_disclaimer_is_replaced():
    context = {
        "vehicle_parameter_inventory": {
            "total_scalar_parameters_found": 1,
            "parameters": [{"path": "rcaide_vehicle.reference_area", "value": 124.862, "unit": "m^2"}],
        }
    }
    answer = _ground_response("The details are deeply nested and large.", context)
    assert "124.862" in answer
    assert "m^2" in answer


def test_hidden_excerpt_wording_is_replaced_with_actual_parameters():
    context = {
        "vehicle_parameter_inventory": {
            "total_scalar_parameters_found": 1,
            "parameters": [{"path": "rcaide_vehicle.length", "value": 38.02, "unit": "m"}],
        }
    }
    answer = _ground_response(
        "Specific dimension parameters like length are not visible in the project excerpt.",
        context,
    )
    assert "38.02" in answer
    assert "read directly" in answer


def test_unsupported_passenger_and_landing_gear_diagnosis_is_corrected():
    context = {
        "vehicle_parameter_inventory": {
            "parameters": [{"path": "rcaide_vehicle.number_of_passengers", "value": 166}],
        }
    }
    answer = _ground_response(
        "Update rcaide_vehicle.fuselages.fuselage.number_of_passengers to 166. "
        "Also set rcaide_vehicle.landing_gears.main_gear.length because it is zero.",
        context,
    )
    assert "should **not** be applied" in answer
    assert "vehicle-level `number_of_passengers` value (166)" in answer
    assert "methods use `strut_length`" in answer


def test_rcaide_identity_answer_names_leads_uiuc_and_matthew_clarke():
    answer = _ground_response(
        "RCAIDE is developed by a community of researchers and engineers.",
        {"user_query": "Who built RCAIDE?"},
    )
    assert "RCAIDE-LEADS" in answer
    assert "University of Illinois Urbana-Champaign" in answer
    assert "Dr. Matthew Clarke" in answer
    assert "https://www.leadsresearchgroup.com" in answer
    assert "https://grainger.illinois.edu" in answer
    assert "https://grainger.illinois.edu/about/directory/faculty/maclarke" in answer


# ---------------------------------------------------------------------------
# FastAPI-to-GitHub-Models adapter contract and provider configuration
# ---------------------------------------------------------------------------

def test_private_model_text_is_extracted():
    result = {"choices": [{"message": {"content": "RCAIDE answer"}}]}
    assert _model_response_text(result) == "RCAIDE answer"


def test_private_model_server_contract(monkeypatch):
    # Simulate the OpenAI-compatible response returned by GitHub Models.
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"Private RCAIDE answer"}}]}'

    # Verify credentials and context are assembled server-side as intended.
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "github-secret")
    monkeypatch.setenv("GITHUB_MODELS_URL", "https://models.github.test/inference")
    monkeypatch.setenv("RCAIDE_GITHUB_MODEL", "openai/gpt-4.1-mini")
    monkeypatch.setattr(model, "urlopen", fake_urlopen)

    answer = model.complete(
        [{"role": "user", "content": "How do I load a vehicle?"}],
        {"inspection": {"vehicle_tag": "vehicle"}},
    )

    request = captured["request"]
    body = captured["body"]
    assert answer == "Private RCAIDE answer"
    assert request.full_url == "https://models.github.test/inference/chat/completions"
    assert request.get_header("Authorization") == "Bearer github-secret"
    assert request.get_header("X-github-api-version") == "2022-11-28"
    assert body["model"] == "openai/gpt-4.1-mini"
    assert body["messages"][0]["role"] == "system"
    assert "Current live RCAIDE context" in body["messages"][0]["content"]
    assert body["messages"][-1]["role"] == "user"


def test_private_model_marks_loaded_mission_as_authoritative(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"Summary"}}]}'

    captured = {}

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse()

    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "secret")
    monkeypatch.setattr(model, "urlopen", fake_urlopen)
    model.complete(
        [{"role": "user", "content": "Summarize my results"}],
        {
            "runtime": {"mission_results_available": True},
            "mission_results": {"segment_count": 2, "segments": []},
        },
    )

    system = captured["body"]["messages"][0]["content"]
    assert "A completed mission result object is loaded" in system
    assert "Never tell the user that the mission has not been run" in system


def test_github_models_token_is_required(monkeypatch):
    monkeypatch.delenv("GITHUB_MODELS_TOKEN", raising=False)
    try:
        model.complete([{"role": "user", "content": "Hello"}], {})
    except model.ModelError as exc:
        assert "GITHUB_MODELS_TOKEN" in str(exc)
    else:
        raise AssertionError("Expected a missing-token error")


# ---------------------------------------------------------------------------
# Model request bounding and multimodal validation
# ---------------------------------------------------------------------------

def test_github_prompt_content_is_bounded():
    context_text = _bounded_context_text({
        "inspection": {"vehicle_tag": "large-aircraft"},
        "project": {"geometry": "x" * 100_000},
        "query_parameter_matches": [{"path": "rcaide_vehicle.mass", "value": 1234}],
        "mission_results": {"segments": [{"true_airspeed": [50, 55, 60]}]},
        "latest_error": "important error",
    })
    messages = _bounded_messages([
        {"role": "user", "content": "old" * 10_000},
        {"role": "assistant", "content": "answer" * 10_000},
        {"role": "user", "content": "latest question"},
    ])

    assert len(context_text) <= 12_000
    assert "large-aircraft" in context_text
    assert "important error" in context_text
    assert "rcaide_vehicle.mass" in context_text
    assert "true_airspeed" in context_text
    assert sum(len(message["content"]) for message in messages) <= 8_000
    assert messages[-1]["content"] == "latest question"


def test_current_multimodal_message_preserves_image_and_bounds_text():
    # Only current-turn images survive message-history reduction.
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}
    messages = _bounded_messages([{
        "role": "user",
        "content": [{"type": "text", "text": "question " + "x" * 20_000}, image],
    }])

    assert messages[-1]["content"][0]["text"].startswith("question ")
    assert messages[-1]["content"][1] == image
    assert len(messages[-1]["content"][0]["text"]) <= 6_000


def test_api_accepts_embedded_image_message():
    message = Message(role="user", content=[
        {"type": "text", "text": "Inspect this plot"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}},
    ])
    assert isinstance(message.content, list)


def test_text_attachment_is_prepared_for_model(tmp_path):
    # tmp_path avoids reading or writing user-owned files during the test.
    path = tmp_path / "results.csv"
    path.write_text("time,airspeed\n0,50\n1,55", encoding="utf-8")
    attachment = prepare_attachment(str(path))

    assert attachment["kind"] == "text"
    assert "airspeed" in attachment["prompt_text"]


# ---------------------------------------------------------------------------
# Query-aware parameter and numerical mission-result extraction
# ---------------------------------------------------------------------------

def test_vehicle_parameter_query_finds_real_saved_value():
    project = {
        "rcaide_vehicle": {
            "tag": "test",
            "wings": {"main_wing": {"spans": {"total": [35.8, 0]}}},
        }
    }
    matches = find_project_parameters(project, "What is the main wing span?")
    assert any(match["path"].endswith("spans.total") and match["value"] == 35.8 for match in matches)


def test_mission_context_contains_true_airspeed_values():
    # SimpleNamespace mirrors the attribute access used by RCAIDE Data objects.
    conditions = SimpleNamespace(
        frames=SimpleNamespace(inertial=SimpleNamespace(
            time=np.array([[0.0], [10.0], [20.0]]),
            aircraft_range=np.array([[0.0], [1000.0], [2100.0]]),
        )),
        freestream=SimpleNamespace(
            velocity=np.array([[50.0], [55.0], [60.0]]),
            altitude=np.array([[1000.0], [1200.0], [1400.0]]),
            mach_number=np.array([[0.15], [0.16], [0.18]]),
        ),
    )
    results = SimpleNamespace(segments=[SimpleNamespace(tag="cruise", conditions=conditions)])

    summary = summarize_mission_results(results, "What was the true airspeed?")

    velocity = summary["segments"][0]["series"]["true_airspeed"]
    assert velocity["unit"] == "m/s"
    assert velocity["sample_values"] == [50.0, 55.0, 60.0]
    assert summary["segments"][0]["series"]["true_airspeed_knots"]["maximum"] > 116


# ---------------------------------------------------------------------------
# Local backend bootstrap and encrypted-token error reporting
# ---------------------------------------------------------------------------

def test_main_bootstrap_reuses_running_service(monkeypatch):
    # An already healthy service must be reused instead of spawning a duplicate.
    monkeypatch.delenv("RCAIDE_AGENT_SERVICE_URL", raising=False)
    monkeypatch.setattr(bootstrap, "_service_is_ready", lambda *_: True)

    process = bootstrap.start_local_agent_service()

    assert process is None
    assert bootstrap.os.environ["RCAIDE_AGENT_SERVICE_URL"] == bootstrap.LOCAL_SERVICE_URL


def test_bootstrap_distinguishes_unreadable_saved_token(monkeypatch, tmp_path):
    # Simulate DPAPI ciphertext created by another Windows user or computer.
    token_file = tmp_path / ".rcaide-agent-token.dat"
    token_file.write_text("encrypted-for-another-user", encoding="utf-8")
    monkeypatch.setattr(bootstrap, "_TOKEN_FILE", token_file)
    monkeypatch.setattr(bootstrap, "_read_windows_encrypted_token", lambda: "")
    monkeypatch.setattr(bootstrap, "_service_is_ready", lambda *_: False)
    monkeypatch.delenv("GITHUB_MODELS_TOKEN", raising=False)
    monkeypatch.delenv("RCAIDE_AGENT_SERVICE_URL", raising=False)

    process = bootstrap.start_local_agent_service()

    assert process is None
    assert "cannot be decrypted by this Windows account or PC" in bootstrap.os.environ[
        "RCAIDE_AGENT_STARTUP_ERROR"
    ]
