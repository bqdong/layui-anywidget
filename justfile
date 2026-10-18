# layui-anywidget development commands.
# Run `just` (or `just --list`) to see everything.

set dotenv-load := false
set shell := ["bash", "-euo", "pipefail", "-c"]

default:
    @just --list

# --- setup -------------------------------------------------------------------

# Install the uv-managed environment (including dev tools) and git hooks.
setup:
    uv sync
    prek install

# Refresh uv.lock from pyproject.toml.
lock:
    uv lock

# --- build -------------------------------------------------------------------

# Vendor layui and regenerate the bundled ESM bridge.
build:
    node scripts/build-bridge.mjs

# Re-vendor layui 2.13.9 from the CDN (needs network access), then rebuild.
vendor:
    node scripts/sync-layui.mjs
    just build

# Verify committed build outputs match their sources (used by hooks/CI).
# Does not write anything.
check-build:
    node scripts/build-bridge.mjs --check

# Build sdist and wheel into dist/.
package:
    rm -rf dist
    uv build

# --- test --------------------------------------------------------------------

# Run Python and JS unit tests.
test:
    uv run pytest
    node --test tests/js/*.test.mjs

# Run only the Python tests.
test-py *args:
    uv run pytest {{args}}

# Run only the JS tests.
test-js:
    node --test tests/js/*.test.mjs

# Browser smoke test: light DOM + shadow root rendering (Playwright).
test-browser:
    uv run python tests/browser_check.py

# Everything CI runs.
ci: lint test check-build
    @echo "ci: ok"

# --- lint / format -----------------------------------------------------------

# Check formatting and lint rules.
lint:
    uv run ruff format --check layui_anywidget tests
    uv run ruff check layui_anywidget tests
    prek run --all-files --show-diff-on-failure --config .pre-commit-config.yaml

# Apply formatting and safe lint fixes.
fmt:
    uv run ruff format layui_anywidget tests
    uv run ruff check --fix layui_anywidget tests

# --- run ---------------------------------------------------------------------

# The demos declare `layui-anywidget` as an inline dependency, which cannot
# resolve from a package index until it is published, so marimo's sandbox is
# disabled and the project venv is used.

# Run the generic-container marimo demo in the project venv.
demo:
    uv run marimo run --no-sandbox demos/form.py

# Run the control-classes marimo demo in the project venv.
demo-controls:
    uv run marimo run --no-sandbox demos/controls.py

# Run the gallery of every supported layui component with live state values.
demo-gallery:
    uv run marimo run --no-sandbox demos/gallery.py

# List the per-component demos (each follows the layui docs page layout).
demo-components:
    uv run marimo run --no-sandbox demos/components/

# Run one per-component demo, e.g. `just demo-component button`.
demo-component name:
    uv run marimo run --no-sandbox demos/components/{{name}}.py

# Edit the generic-container demo in the project venv.
edit:
    uv run marimo edit --no-sandbox demos/form.py

# Open the browser preview (light DOM + shadow root) at http://127.0.0.1:8000.
preview:
    @echo "open http://127.0.0.1:8000/examples/preview.html"
    python3 -m http.server 8000

# --- release -----------------------------------------------------------------

# Clean local build and test caches.
clean:
    rm -rf dist build .pytest_cache .ruff_cache
    find . -name __pycache__ -type d -not -path "./.venv/*" -exec rm -rf {} +
