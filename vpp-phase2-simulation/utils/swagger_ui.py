"""
Swagger UI Setup for VPP Phase 2 Simulation Framework.

Provides interactive API documentation using Swagger UI.
Integrates with Bottle.py application to serve Swagger UI at /api/docs.
"""

import json
from bottle import Bottle, static_file, response
from utils.openapi_spec import get_openapi_spec


def setup_swagger_ui(app: Bottle, base_path: str = "/api") -> None:
    """
    Setup Swagger UI for the application.
    
    Args:
        app: Bottle application instance
        base_path: Base path for API endpoints (default: /api)
    """
    
    @app.route(f"{base_path}/openapi.json")
    def openapi_spec():
        """
        Serve OpenAPI specification as JSON.
        
        Returns:
            OpenAPI 3.0 specification
        """
        response.content_type = "application/json"
        spec = get_openapi_spec()
        return json.dumps(spec, indent=2)
    
    @app.route(f"{base_path}/docs")
    def swagger_ui():
        """
        Serve Swagger UI HTML.
        
        Returns:
            HTML page with Swagger UI
        """
        response.content_type = "text/html"
        return get_swagger_ui_html(base_path)
    
    @app.route(f"{base_path}/docs/")
    def swagger_ui_redirect():
        """Redirect to Swagger UI."""
        response.status = 301
        response.set_header("Location", f"{base_path}/docs")
        return ""


def get_swagger_ui_html(base_path: str = "/api") -> str:
    """
    Generate Swagger UI HTML.
    
    Args:
        base_path: Base path for API endpoints
        
    Returns:
        HTML string for Swagger UI
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VPP Phase 2 Simulation Framework - API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
        <style>
            html {{
                box-sizing: border-box;
                overflow: -moz-scrollbars-vertical;
                overflow-y: scroll;
            }}
            *, *:before, *:after {{
                box-sizing: inherit;
            }}
            body {{
                margin: 0;
                padding: 0;
                font-family: sans-serif;
            }}
            .swagger-ui {{
                max-width: 1460px;
                margin: 0 auto;
            }}
            .topbar {{
                background-color: #fafafa;
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .topbar-title {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
                margin: 0 20px;
            }}
        </style>
    </head>
    <body>
        <div class="topbar">
            <div class="topbar-title">VPP Phase 2 Simulation Framework - API Documentation</div>
        </div>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: "{base_path}/openapi.json",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout",
                    defaultModelsExpandDepth: 1,
                    defaultModelExpandDepth: 1,
                    docExpansion: "list",
                    filter: true,
                    showRequestHeaders: true,
                    supportedSubmitMethods: [
                        'get',
                        'post',
                        'put',
                        'delete',
                        'patch',
                        'head',
                        'options',
                        'trace'
                    ]
                }})
                window.ui = ui
            }}
        </script>
    </body>
    </html>
    """
