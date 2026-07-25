def test_login_page_renders(api_client):
    resp = api_client.get("/portal/login")
    assert resp.status_code == 200
    assert "request-form" in resp.text
    assert "/web/auth/request-code" in resp.text
    assert "/web/auth/verify-code" in resp.text


def test_dashboard_page_renders(api_client):
    resp = api_client.get("/portal")
    assert resp.status_code == 200
    assert "/web/cases" in resp.text
    assert "/portal/login" in resp.text  # redirect target when no token


def test_case_detail_page_renders_and_embeds_case_id(api_client):
    resp = api_client.get("/portal/case/11111111-1111-1111-1111-111111111111")
    assert resp.status_code == 200
    assert '"11111111-1111-1111-1111-111111111111"' in resp.text
    assert "/web/chat" in resp.text


def test_case_detail_page_escapes_case_id_from_url(api_client):
    """case_id comes straight from the URL path — {{ case_id | tojson }}
    must HTML-escape '<'/'>' so a case_id can't inject a raw tag into the
    surrounding <script> block (a literal '/' in the path 404s before
    reaching the template at all, since the route matches one segment)."""
    resp = api_client.get("/portal/case/x<img-onerror=alert(1)>")
    assert resp.status_code == 200
    assert "<img-onerror=alert(1)>" not in resp.text
