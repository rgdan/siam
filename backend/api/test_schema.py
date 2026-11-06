from django.test import SimpleTestCase
from django.urls import get_resolver
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema
from rest_framework.test import APIClient


class APIDocumentationTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.schema = SchemaGenerator().get_schema(public=True)

    def test_schema_is_valid_and_covers_every_api_operation_without_database_access(self):
        validate_schema(self.schema)
        documented = self.schema["paths"]
        operation_ids = []
        for pattern in get_resolver().url_patterns:
            if pattern.name in {"schema", "swagger-ui"}:
                continue
            route = "/" + str(pattern.pattern)
            for converter in pattern.pattern.converters:
                converter_type = "int" if converter.endswith("_id") else "str"
                route = route.replace(f"<{converter_type}:{converter}>", "{" + converter + "}")
            view = pattern.callback.cls
            for method in view.http_method_names:
                if method in {"options", "head"} or not hasattr(view, method):
                    continue
                with self.subTest(path=route, method=method):
                    operation = documented[route][method]
                    self.assertTrue(operation["summary"])
                    self.assertTrue(operation["tags"])
                    self.assertTrue(operation["responses"])
                    operation_ids.append(operation["operationId"])
        self.assertEqual(len(operation_ids), len(set(operation_ids)))

    def test_schema_documents_authentication_pagination_and_binary_exports(self):
        paths = self.schema["paths"]
        self.assertEqual(self.schema["components"]["securitySchemes"]["cookieAuth"], {
            "type": "apiKey", "in": "cookie", "name": "sessionid",
        })
        self.assertNotIn("security", paths["/api/auth/login/"]["post"])
        self.assertNotIn("security", paths["/api/events/"]["get"])
        self.assertEqual(paths["/api/events/"]["post"]["security"], [{"cookieAuth": []}])
        incident_list = paths["/api/incidents/"]["get"]
        self.assertEqual({p["name"] for p in incident_list["parameters"]}, {"page", "ordering"})
        page = self.schema["components"]["schemas"]["IncidentPage"]["properties"]
        self.assertEqual(set(page), {"count", "next", "previous", "results"})
        schemas = self.schema["components"]["schemas"]
        self.assertNotIn("password", schemas["User"]["properties"])
        self.assertIn("password", schemas["UserRequest"]["properties"])
        self.assertEqual(set(schemas["IncidentRequest"]["properties"]), {"description", "category"})
        exported = paths["/api/reports/export/{tipo}/{formato}/"]["get"]["responses"]["200"]["content"]
        self.assertEqual(set(exported), {"application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
        self.assertTrue(all(v["schema"]["format"] == "binary" for v in exported.values()))

    def test_documentation_and_schema_are_public(self):
        client = APIClient()
        response = client.get("/api/docs/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SwaggerUIBundle")
        self.assertContains(response, "csrftoken=")
        response = client.get("/api/schema/", HTTP_ACCEPT="application/vnd.oai.openapi+json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["paths"].keys(), self.schema["paths"].keys())
