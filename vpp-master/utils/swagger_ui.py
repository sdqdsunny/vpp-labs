"""
Swagger UI integration for VPP Master API
Provides interactive API documentation
"""

import json
from bottle import response


def get_swagger_ui_html(spec_url="/api/openapi.json"):
    """
    Generate Swagger UI HTML page
    
    Args:
        spec_url: URL to the OpenAPI specification
        
    Returns:
        HTML string for Swagger UI
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VPP Master API - Swagger UI</title>
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
            }}
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
        <script>
            window.onload = function() {{
                const ui = SwaggerUIBundle({{
                    url: "{spec_url}",
                    dom_id: '#swagger-ui',
                    deepLinking: true,
                    presets: [
                        SwaggerUIBundle.presets.apis,
                        SwaggerUIStandalonePreset
                    ],
                    plugins: [
                        SwaggerUIBundle.plugins.DownloadUrl
                    ],
                    layout: "StandaloneLayout"
                }})
                window.ui = ui
            }}
        </script>
    </body>
    </html>
    """


def get_redoc_html(spec_url="/api/openapi.json"):
    """
    Generate ReDoc HTML page (alternative to Swagger UI)
    
    Args:
        spec_url: URL to the OpenAPI specification
        
    Returns:
        HTML string for ReDoc
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>VPP Master API - ReDoc</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
        <style>
            body {{
                margin: 0;
                padding: 0;
            }}
        </style>
    </head>
    <body>
        <redoc spec-url='{spec_url}'></redoc>
        <script src="https://cdn.jsdelivr.net/npm/redoc@latest/bundles/redoc.standalone.js"></script>
    </body>
    </html>
    """
