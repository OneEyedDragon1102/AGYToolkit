"""Unit tests for Turnkey Tech-Stack Production Boilerplate Generators."""

import io
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agy_toolkit.cli import main
from agy_toolkit.scaffolder import scaffold_project
from agy_toolkit.scaffolder_stacks import (
    STACK_CATALOG,
    list_available_templates,
    resolve_template_name,
    sanitize_package_name,
    scaffold_stack_template,
)


class TestScaffolderStacks(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="agy_test_stacks_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sanitize_package_name_java(self):
        self.assertEqual(sanitize_package_name("my-service", "java"), "myservice")
        self.assertEqual(sanitize_package_name("order_processor_v1", "java"), "orderprocessorv1")
        self.assertEqual(sanitize_package_name("   ", "java"), "app")

    def test_sanitize_package_name_python(self):
        self.assertEqual(sanitize_package_name("my-service", "python"), "my_service")
        self.assertEqual(sanitize_package_name("order__service", "python"), "order_service")
        self.assertEqual(sanitize_package_name("123-service", "python"), "pkg_123_service")
        self.assertEqual(sanitize_package_name("   ", "python"), "app")

    def test_sanitize_package_name_node(self):
        self.assertEqual(sanitize_package_name("My Service", "node"), "my-service")
        self.assertEqual(sanitize_package_name("auth_gateway", "node"), "auth-gateway")

    def test_resolve_template_name(self):
        self.assertEqual(resolve_template_name("spring-boot-hexagonal"), "spring-boot-hexagonal")
        self.assertEqual(resolve_template_name("spring-boot"), "spring-boot-hexagonal")
        self.assertEqual(resolve_template_name("node-ts"), "node-clean-ts")
        self.assertEqual(resolve_template_name("fastapi"), "python-fastapi")

        with self.assertRaises(ValueError):
            resolve_template_name("non-existent-template")

    def test_list_available_templates(self):
        templates = list_available_templates()
        self.assertGreaterEqual(len(templates), 3)

        names = {t["name"] for t in templates}
        self.assertIn("spring-boot-hexagonal", names)
        self.assertIn("node-clean-ts", names)
        self.assertIn("python-fastapi", names)

        for t in templates:
            self.assertTrue(t["exists"], f"Template {t['name']} directory does not exist")
            self.assertIn("description", t)

    def test_scaffold_spring_boot_hexagonal(self):
        created = scaffold_stack_template(
            target_dir=self.temp_dir,
            project_name="order-service",
            template_name="spring-boot-hexagonal",
        )
        self.assertGreater(len(created), 10)

        pom_path = self.temp_dir / "pom.xml"
        self.assertTrue(pom_path.exists())
        pom_content = pom_path.read_text(encoding="utf-8")
        self.assertIn("<artifactId>order-service</artifactId>", pom_content)
        self.assertIn("spring-boot-starter-web", pom_content)

        app_java = self.temp_dir / "src" / "main" / "java" / "com" / "example" / "orderservice" / "Application.java"
        self.assertTrue(app_java.exists())
        app_content = app_java.read_text(encoding="utf-8")
        self.assertIn("package com.example.orderservice;", app_content)

        domain_item = (
            self.temp_dir
            / "src"
            / "main"
            / "java"
            / "com"
            / "example"
            / "orderservice"
            / "domain"
            / "model"
            / "Item.java"
        )
        self.assertTrue(domain_item.exists())

        test_item = (
            self.temp_dir
            / "src"
            / "test"
            / "java"
            / "com"
            / "example"
            / "orderservice"
            / "domain"
            / "model"
            / "ItemTest.java"
        )
        self.assertTrue(test_item.exists())

    def test_scaffold_node_clean_ts(self):
        created = scaffold_stack_template(
            target_dir=self.temp_dir,
            project_name="auth-gateway",
            template_name="node-clean-ts",
        )
        self.assertGreater(len(created), 5)

        pkg_json = self.temp_dir / "package.json"
        self.assertTrue(pkg_json.exists())
        pkg_content = pkg_json.read_text(encoding="utf-8")
        self.assertIn('"name": "auth-gateway"', pkg_content)
        self.assertIn('"fastify"', pkg_content)

        tsconfig = self.temp_dir / "tsconfig.json"
        self.assertTrue(tsconfig.exists())

        dockerfile = self.temp_dir / "Dockerfile"
        self.assertTrue(dockerfile.exists())

        app_ts = self.temp_dir / "src" / "app.ts"
        self.assertTrue(app_ts.exists())

        test_app = self.temp_dir / "tests" / "app.test.ts"
        self.assertTrue(test_app.exists())

    def test_scaffold_python_fastapi(self):
        created = scaffold_stack_template(
            target_dir=self.temp_dir,
            project_name="payment-service",
            template_name="python-fastapi",
        )
        self.assertGreater(len(created), 5)

        pyproject = self.temp_dir / "pyproject.toml"
        self.assertTrue(pyproject.exists())
        pyproject_content = pyproject.read_text(encoding="utf-8")
        self.assertIn('name = "payment-service"', pyproject_content)
        self.assertIn("fastapi", pyproject_content)

        main_py = self.temp_dir / "src" / "payment_service" / "main.py"
        self.assertTrue(main_py.exists())
        main_content = main_py.read_text(encoding="utf-8")
        self.assertIn("payment_service.api.routes.health", main_content)

        schema_py = self.temp_dir / "src" / "payment_service" / "schemas" / "item.py"
        self.assertTrue(schema_py.exists())

        test_health = self.temp_dir / "tests" / "test_health.py"
        self.assertTrue(test_health.exists())

    def test_scaffold_project_with_template_integrated(self):
        res = scaffold_project(
            target_path=self.temp_dir,
            project_name="quant-engine",
            stack="spring-boot",
            template="spring-boot-hexagonal",
        )
        self.assertEqual(res["template"], "spring-boot-hexagonal")
        self.assertGreater(res["template_files_count"], 0)
        self.assertTrue((self.temp_dir / "pom.xml").exists())
        self.assertTrue((self.temp_dir / ".agents").exists())
        self.assertTrue((self.temp_dir / "GEMINI.md").exists())
        self.assertTrue((self.temp_dir / "AGENTS.md").exists())

    def test_cli_init_with_template(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main([
                "init",
                str(self.temp_dir),
                "--name",
                "trade-router",
                "--template",
                "node-clean-ts",
            ])
        self.assertEqual(ret, 0)
        self.assertTrue((self.temp_dir / "package.json").exists())
        self.assertTrue((self.temp_dir / ".agents").exists())
        self.assertIn("boilerplate files scaffolded", buf.getvalue())

    def test_cli_list_templates(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            ret = main(["--list-templates"])
        self.assertEqual(ret, 0)
        out = buf.getvalue()
        self.assertIn("spring-boot-hexagonal", out)
        self.assertIn("node-clean-ts", out)
        self.assertIn("python-fastapi", out)


if __name__ == "__main__":
    unittest.main()
