# SIAM API

[Español](api.es.md) · [English](api.md) · [Project](../README.en.md)

The API reference is generated from Django views and serializers with drf-spectacular (OpenAPI 3). Swagger UI groups endpoints by module and describes request bodies, response fields, filters, authentication and role permissions.

| Reference | Address |
| :--- | :--- |
| Local Swagger UI | [127.0.0.1:8000/api/docs/](http://127.0.0.1:8000/api/docs/) |
| Local OpenAPI schema | [127.0.0.1:8000/api/schema/](http://127.0.0.1:8000/api/schema/) |
| Published reference, after deployment | [rgdan.github.io/siam](https://rgdan.github.io/siam/) |

Start the system with the [Docker instructions](../README.en.md#docker). After updating dependencies, rebuild with `docker compose up --build -d`.

## Authentication

SIAM uses session cookies. Open **local Swagger UI** on the same host as the API to test requests:

1. Execute `GET /api/auth/csrf/` to obtain a CSRF cookie and token.
2. Execute `POST /api/auth/login/` with `email` and `password`. Use a [demo account](../README.en.md#test-accounts) for local testing.
3. Execute `GET /api/auth/me/` to inspect the authenticated account and its permissions.
4. Execute an endpoint allowed by that role, then `POST /api/auth/logout/` to end the session.

The browser manages `sessionid`. Swagger reads the current `csrftoken` cookie and sends `X-CSRFToken` on writes, including login. Login rotates the token. The Authorize dialog does not set session cookies; follow the login flow instead. Other clients must retain cookies and send the latest token themselves.

Public endpoints include health, CSRF, museum configuration and the public event list. Creating an event at the same `/api/events/` URL requires authentication and the corresponding permission. Permission names appear in each operation's description; `/api/auth/me/` is the source for the current account's permissions.

## Conventions

- Requests and normal responses use JSON. Photo upload also uses JSON with base64 content, rather than multipart files.
- Datetimes include their timezone; reporting dates use `YYYY-MM-DD` and inclusive bounds in `America/Costa_Rica`.
- Incident history has 20 entries per page and accepts `page` and `ordering` (`-timestamp` or `timestamp`). Audit history has 50 entries per page. Other lists are not paginated.
- Consolidated reports default to the current month when neither date is supplied. Collection reports reflect current inventory. PDF/Excel exports include all matching records.
- Errors use JSON field messages or `detail`/`non_field_errors`. Common statuses are `400` for invalid input, `401` for a missing session or rejected login, `403` for permission/CSRF failures and `404` for missing resources or pages. Visitor and incident writes can return `503` when saving fails.

## GitHub Pages

The [API documentation workflow](../.github/workflows/api-docs.yml) validates the schema on pull requests. Pushes to `main` regenerate and deploy the reference when backend code, the documentation page or the workflow changes. It can also run manually from Actions; only `main` deploys.

In the repository's **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source. Merge the workflow into `main` and check **Actions → API documentation** for the published URL. The workflow uses the repository's `GITHUB_TOKEN`; no personal access token or production secret is needed.

The published page is read-only. GitHub Pages serves the HTML and generated schema, and Swagger assets load from a pinned jsDelivr version. The backend and database stay on your own machine. API requests can be tested in local Swagger UI.

## Updating the reference

When changing an endpoint, update its `@extend_schema` annotations and the serializers it uses. Response objects assembled by views are described in `backend/api/schema.py`. Never put real account data, cookies or secrets in examples.

Generate and validate the schema from the repository root:

```bash
docker compose exec backend python manage.py spectacular --file /tmp/openapi.yaml --validate --fail-on-warn
docker compose cp backend:/tmp/openapi.yaml ./openapi.yaml
```

The generated file is a build artifact; it does not need to be committed. CI generates it without a running backend or database and fails on schema warnings.

Implementation references: [drf-spectacular customization](https://drf-spectacular.readthedocs.io/en/stable/customization.html), [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
