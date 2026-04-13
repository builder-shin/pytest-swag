import pytest
from pytest_swag.collector import SwagCollector


class TestCollect:
    def test_collect_single_operation(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List blogs",
            "responses": {200: {"description": "OK"}},
        })
        ops = c.get_operations()
        assert len(ops) == 1
        assert ops[0]["path"] == "/blogs"

    def test_collect_multiple_operations(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        c.collect({
            "path": "/blogs",
            "method": "post",
            "summary": "Create",
            "responses": {201: {"description": "Created"}},
        })
        ops = c.get_operations()
        assert len(ops) == 2


class TestMerge:
    def test_merge_same_path_different_methods(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        c.collect({
            "path": "/blogs",
            "method": "post",
            "summary": "Create",
            "responses": {201: {"description": "Created"}},
        })
        paths = c.merge_to_paths()
        assert "/blogs" in paths
        assert "get" in paths["/blogs"]
        assert "post" in paths["/blogs"]

    def test_merge_same_path_same_method_different_responses(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK", "content": {"application/json": {"schema": {"type": "array"}}}}},
        })
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {404: {"description": "Not found"}},
        })
        paths = c.merge_to_paths()
        method_obj = paths["/blogs"]["get"]
        assert 200 in method_obj["responses"]
        assert 404 in method_obj["responses"]


class TestDocTarget:
    def test_collect_with_doc_target(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v2",
        })
        ops = c.get_operations(doc_target="API v2")
        assert len(ops) == 1

    def test_filter_by_doc_target(self):
        c = SwagCollector()
        c.collect({
            "path": "/v1/blogs",
            "method": "get",
            "summary": "List v1",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v1",
        })
        c.collect({
            "path": "/v2/blogs",
            "method": "get",
            "summary": "List v2",
            "responses": {200: {"description": "OK"}},
            "doc_target": "API v2",
        })
        assert len(c.get_operations(doc_target="API v1")) == 1
        assert len(c.get_operations(doc_target="API v2")) == 1

    def test_no_target_defaults_to_none(self):
        c = SwagCollector()
        c.collect({
            "path": "/blogs",
            "method": "get",
            "summary": "List",
            "responses": {200: {"description": "OK"}},
        })
        ops = c.get_operations(doc_target=None)
        assert len(ops) == 1
