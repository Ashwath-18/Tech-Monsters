import unittest
from unittest.mock import MagicMock, patch
import io
import os
import sys
import json
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import gemma_client
from gemma_client import (
    preprocess_image,
    extract_netlist_from_image,
    check_unsupported_components,
    GemmaTimeoutError,
    GemmaBadJSONError,
    GemmaUnsupportedComponentError,
    GemmaAPIError
)
import main
from fastapi.testclient import TestClient

client = TestClient(main.app)

class TestGemmaClient(unittest.TestCase):

    def test_preprocess_image_downscaling(self):
        """Test image preprocessing downscales to <= 1280px, RGB, JPEG quality 85."""
        orig_img = Image.new("RGBA", (2000, 1000), color=(255, 0, 0, 128))
        buf = io.BytesIO()
        orig_img.save(buf, format="PNG")
        orig_bytes = buf.getvalue()

        processed_bytes = preprocess_image(orig_bytes, max_dim=1280, quality=85)
        out_img = Image.open(io.BytesIO(processed_bytes))

        self.assertEqual(out_img.mode, "RGB")
        self.assertEqual(out_img.format, "JPEG")
        self.assertLessEqual(max(out_img.size), 1280)
        self.assertEqual(out_img.size, (1280, 640))

    def test_check_unsupported_components(self):
        """Test check_unsupported_components detects diodes, LEDs, capacitors, and non-R/V/I types."""
        valid_netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": []
        }
        self.assertIsNone(check_unsupported_components(valid_netlist))

        # Unsupported component type (e.g. Diode D1)
        diode_netlist = {
            "components": [
                {"id": "D1", "type": "D", "value": 0.7, "nodes": ["N1", "0"]}
            ],
            "uncertain": []
        }
        self.assertIsNotNone(check_unsupported_components(diode_netlist))

        # Unsupported keyword in uncertain list (e.g. LED)
        led_netlist = {
            "components": [
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": ["Circuit has an LED drawn at output junction"]
        }
        self.assertIsNotNone(check_unsupported_components(led_netlist))

    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_valid_json_success(self, mock_get_client, mock_invoke):
        """Test valid JSON on attempt 1 returns extracted netlist dictionary."""
        mock_get_client.return_value = MagicMock()
        sample_json = json.dumps({
            "components": [
                {"id": "V1", "type": "V", "value": 12.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": []
        })
        mock_invoke.return_value = f"```json\n{sample_json}\n```"

        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        self.assertEqual(len(result["components"]), 2)
        self.assertEqual(result["components"][0]["id"], "V1")

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_timeout_then_success(self, mock_get_client, mock_invoke, mock_sleep):
        """Test timeout on attempt 1, followed by success on retry."""
        mock_get_client.return_value = MagicMock()
        sample_json = json.dumps({
            "components": [{"id": "R1", "type": "R", "value": 500.0, "nodes": ["N1", "0"]}],
            "uncertain": []
        })
        mock_invoke.side_effect = [
            GemmaTimeoutError("Deadline exceeded"),
            sample_json
        ]

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        self.assertEqual(result["components"][0]["value"], 500.0)
        self.assertEqual(mock_invoke.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_timeout_twice_raises_timeout_error(self, mock_get_client, mock_invoke, mock_sleep):
        """Test timeout on both attempts raises GemmaTimeoutError."""
        mock_get_client.return_value = MagicMock()
        mock_invoke.side_effect = GemmaTimeoutError("Request timed out")

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        with self.assertRaises(GemmaTimeoutError):
            extract_netlist_from_image(buf.getvalue())

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_bad_json_then_retry_success(self, mock_get_client, mock_invoke, mock_sleep):
        """Test invalid JSON on attempt 1, then valid JSON on retry succeeds."""
        mock_get_client.return_value = MagicMock()
        valid_json = json.dumps({
            "components": [{"id": "V1", "type": "V", "value": 5.0, "nodes": ["N1", "0"]}],
            "uncertain": []
        })
        mock_invoke.side_effect = ["Invalid non-json text...", valid_json]

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        self.assertEqual(result["components"][0]["id"], "V1")

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_immediate_api_error_on_400_401_403(self, mock_get_client, mock_invoke, mock_sleep):
        """Test HTTP 400, 401, 403 errors fail immediately without retrying and include HTTP status in message."""
        mock_get_client.return_value = MagicMock()
        
        for status in (400, 401, 403):
            mock_invoke.reset_mock()
            mock_sleep.reset_mock()
            mock_invoke.side_effect = GemmaAPIError(f"HTTP {status}: Client authentication / permission failure", status_code=status)

            img = Image.new("RGB", (100, 100))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")

            with self.assertRaises(GemmaAPIError) as ctx:
                extract_netlist_from_image(buf.getvalue())

            self.assertIn(str(status), str(ctx.exception))
            # Verify no retry occurred
            self.assertEqual(mock_invoke.call_count, 1)
            mock_sleep.assert_not_called()

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_retry_on_429_then_success(self, mock_get_client, mock_invoke, mock_sleep):
        """Test HTTP 429 quota exhaustion triggers retry and succeeds on attempt 2."""
        mock_get_client.return_value = MagicMock()
        valid_json = json.dumps({
            "components": [{"id": "R1", "type": "R", "value": 220.0, "nodes": ["N1", "0"]}],
            "uncertain": []
        })
        mock_invoke.side_effect = [
            GemmaAPIError("HTTP 429: Quota exhausted / Resource exhausted", status_code=429),
            valid_json
        ]

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        self.assertEqual(result["components"][0]["value"], 220.0)
        self.assertEqual(mock_invoke.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("gemma_client.time.sleep")
    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_extract_retry_on_500_then_success(self, mock_get_client, mock_invoke, mock_sleep):
        """Test HTTP 500 server error triggers retry and succeeds on attempt 2."""
        mock_get_client.return_value = MagicMock()
        valid_json = json.dumps({
            "components": [{"id": "V1", "type": "V", "value": 9.0, "nodes": ["N1", "0"]}],
            "uncertain": []
        })
        mock_invoke.side_effect = [
            GemmaAPIError("HTTP 500: Internal Server Error", status_code=500),
            valid_json
        ]

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        self.assertEqual(result["components"][0]["value"], 9.0)
        self.assertEqual(mock_invoke.call_count, 2)
        mock_sleep.assert_called_once()


class TestApiReadEndpoints(unittest.TestCase):

    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_ok(self, mock_extract):
        """Test /api/read returns code OK on valid schematic."""
        mock_extract.return_value = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": []
        }

        response = client.post("/api/read", files={"file": ("test.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "OK")
        self.assertTrue(data["is_valid"])
        self.assertIn("node_voltages", data["solved"])

    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_timeout_code(self, mock_extract):
        """Test /api/read returns code TIMEOUT when model times out."""
        mock_extract.side_effect = GemmaTimeoutError("Gemma model timed out after 45s.")

        response = client.post("/api/read", files={"file": ("test.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "TIMEOUT")
        self.assertFalse(data["is_valid"])
        self.assertIn("timed out", data["message"].lower())

    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_unsupported_component_code(self, mock_extract):
        """Test /api/read returns code UNSUPPORTED_COMPONENT when non-R/V/I component is present."""
        mock_extract.return_value = {
            "components": [
                {"id": "V1", "type": "V", "value": 9.0, "nodes": ["N1", "0"]},
                {"id": "D1", "type": "D", "value": 0.7, "nodes": ["N1", "0"]}
            ],
            "uncertain": ["LED diode drawn in schematic"]
        }

        response = client.post("/api/read", files={"file": ("led_circuit.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "UNSUPPORTED_COMPONENT")
        self.assertFalse(data["is_valid"])
        self.assertIn("unsupported", data["message"].lower())

    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_bad_json_code(self, mock_extract):
        """Test /api/read returns code BAD_JSON when output is not parseable."""
        mock_extract.side_effect = GemmaBadJSONError("Model response could not be parsed into valid JSON.")

        response = client.post("/api/read", files={"file": ("test.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "BAD_JSON")
        self.assertFalse(data["is_valid"])

    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_api_error_with_http_status(self, mock_extract):
        """Test /api/read returns API_ERROR with HTTP status code in message."""
        mock_extract.side_effect = GemmaAPIError("HTTP 401: Unauthorized API key", status_code=401)

        response = client.post("/api/read", files={"file": ("test.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "API_ERROR")
        self.assertFalse(data["is_valid"])
        self.assertIn("401", data["message"])

    @patch.object(main, "repair_netlist_from_image")
    @patch.object(main, "extract_netlist_from_image")
    def test_api_read_validation_failed_code(self, mock_extract, mock_repair):
        """Test /api/read returns code VALIDATION_FAILED when netlist violates electrical rules."""
        # Missing ground node 0
        invalid_netlist = {
            "components": [
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]}
            ],
            "uncertain": []
        }
        mock_extract.return_value = invalid_netlist
        mock_repair.return_value = invalid_netlist

        response = client.post("/api/read", files={"file": ("test.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "VALIDATION_FAILED")
        self.assertFalse(data["is_valid"])

    def test_battery_with_label_E_not_unsupported(self):
        """A battery with id 'V1' and label 'E' does not produce UNSUPPORTED_COMPONENT."""
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "label": "E", "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": []
        }
        # Component TYPE is "V", so check_unsupported_components must return None
        self.assertIsNone(check_unsupported_components(netlist))

    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_netlist_with_null_values_returns_values_missing_and_never_solved(self, mock_get_client, mock_invoke):
        """A netlist with null values returns VALUES_MISSING through real /api/read path mocking only Gemma client."""
        mock_get_client.return_value = MagicMock()
        mock_invoke.return_value = json.dumps({
            "components": [
                {"id": "V1", "type": "V", "value": None, "label": "E", "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": None, "label": "R1", "nodes": ["N1", "0"]},
                {"id": "R2", "type": "R", "value": None, "label": "R2", "nodes": ["N1", "0"]}
            ],
            "symbolic": ["E", "R1", "R2"],
            "uncertain": []
        })

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        response = client.post("/api/read", files={"file": ("symbolic_circuit.jpg", buf.getvalue(), "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "VALUES_MISSING")
        self.assertEqual(
            data["message"],
            "The drawing has symbols but no numbers (E, R1, R2). Enter values and re-simulate."
        )
        self.assertFalse(data["is_valid"])
        self.assertIsNone(data["solved"])

    @patch.object(main, "extract_netlist_from_image")
    def test_led_still_returns_unsupported_component(self, mock_extract):
        """An LED still returns UNSUPPORTED_COMPONENT."""
        mock_extract.return_value = {
            "components": [
                {"id": "D1", "type": "LED", "value": 2.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 330.0, "nodes": ["N1", "0"]}
            ],
            "uncertain": ["Red indicator LED present"]
        }

        response = client.post("/api/read", files={"file": ("led.jpg", b"fake_img_data", "image/jpeg")})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["code"], "UNSUPPORTED_COMPONENT")
        self.assertFalse(data["is_valid"])
        self.assertIn("unsupported", data["message"].lower())

    @patch.object(gemma_client, "_invoke_model_call")
    @patch.object(gemma_client, "get_genai_client")
    def test_current_arrow_annotations_do_not_create_I_components(self, mock_get_client, mock_invoke):
        """Current-arrow annotations (I, I1, I2) do not create I-type components."""
        mock_get_client.return_value = MagicMock()
        mock_invoke.return_value = json.dumps({
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "label": "E", "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "label": "R1", "nodes": ["N1", "0"]},
                {"id": "R2", "type": "R", "value": 1000.0, "label": "R2", "nodes": ["N1", "0"]}
            ],
            "symbolic": [],
            "uncertain": ["Arrows I, I1, I2 interpreted as branch current annotations"]
        })

        img = Image.new("RGB", (100, 100))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")

        result = extract_netlist_from_image(buf.getvalue())
        component_types = [c["type"] for c in result["components"]]
        self.assertNotIn("I", component_types)
        self.assertEqual(component_types, ["V", "R", "R"])
        self.assertIsNone(check_unsupported_components(result))

if __name__ == "__main__":
    unittest.main()
