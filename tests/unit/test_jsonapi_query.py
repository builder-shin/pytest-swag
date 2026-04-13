from pytest_swag.adapters.jsonapi.query import JsonApiQuery


class TestJsonApiQueryDataclass:
    def test_default_all_none(self):
        q = JsonApiQuery()
        assert q.fields is None
        assert q.include is None
        assert q.filter is None
        assert q.sort is None
        assert q.page is None

    def test_full_construction(self):
        q = JsonApiQuery(
            fields={"articles": ["title", "body"]},
            include=["author"],
            filter={"status": "published"},
            sort=["-created_at"],
            page={"number": 1, "size": 20},
        )
        assert q.fields == {"articles": ["title", "body"]}
        assert q.include == ["author"]
        assert q.filter == {"status": "published"}
        assert q.sort == ["-created_at"]
        assert q.page == {"number": 1, "size": 20}


class TestToQueryParams:
    def test_empty_query(self):
        q = JsonApiQuery()
        assert q.to_query_params() == {}

    def test_sparse_fieldsets(self):
        q = JsonApiQuery(fields={"articles": ["title", "body"], "people": ["name"]})
        params = q.to_query_params()
        assert params["fields[articles]"] == "title,body"
        assert params["fields[people]"] == "name"

    def test_include(self):
        q = JsonApiQuery(include=["author", "comments.author"])
        params = q.to_query_params()
        assert params["include"] == "author,comments.author"

    def test_simple_filter(self):
        q = JsonApiQuery(filter={"status": "published", "author": "1"})
        params = q.to_query_params()
        assert params["filter[status]"] == "published"
        assert params["filter[author]"] == "1"

    def test_operator_filter(self):
        q = JsonApiQuery(filter={"created_at": {"gte": "2026-01-01", "lte": "2026-12-31"}})
        params = q.to_query_params()
        assert params["filter[created_at][gte]"] == "2026-01-01"
        assert params["filter[created_at][lte]"] == "2026-12-31"

    def test_mixed_filter(self):
        q = JsonApiQuery(filter={
            "status": "published",
            "created_at": {"gte": "2026-01-01"},
        })
        params = q.to_query_params()
        assert params["filter[status]"] == "published"
        assert params["filter[created_at][gte]"] == "2026-01-01"

    def test_sort(self):
        q = JsonApiQuery(sort=["-created_at", "title"])
        params = q.to_query_params()
        assert params["sort"] == "-created_at,title"

    def test_page(self):
        q = JsonApiQuery(page={"number": 1, "size": 20})
        params = q.to_query_params()
        assert params["page[number]"] == "1"
        assert params["page[size]"] == "20"

    def test_full_query(self):
        q = JsonApiQuery(
            fields={"articles": ["title"]},
            include=["author"],
            filter={"status": "published"},
            sort=["-created_at"],
            page={"number": 1, "size": 10},
        )
        params = q.to_query_params()
        assert len(params) == 6
        assert "fields[articles]" in params
        assert "include" in params
        assert "filter[status]" in params
        assert "sort" in params
        assert "page[number]" in params
        assert "page[size]" in params
