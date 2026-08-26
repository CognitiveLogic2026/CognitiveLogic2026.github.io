# Cognitive Logic Nginx reference

This directory documents the canonical public-site Nginx behaviour.

## Active VPS configuration

The live server configuration is currently maintained at:

`/etc/nginx/sites-enabled/cognitivelogic`

The files in this directory are reference material and must not be copied blindly over the active server configuration.

## Legacy QEN URL

The historical public URL:

`https://cognitivelogic.it/qen.html`

is permanently redirected with HTTP 301 to:

`https://cognitivelogic.it/framework.html`

This consolidates the public QEN Framework identity and avoids duplicate/legacy search-engine signals.

QEN Sovereign remains a distinct public product area at:

`https://cognitivelogic.it/qen-sovereign/`

## Deployment safety

Before changing Nginx:

1. Back up the active configuration outside `/etc/nginx/sites-enabled/`.
2. Run `sudo nginx -t`.
3. Reload only after a successful test.
4. Verify redirects and canonical pages with `curl`.
