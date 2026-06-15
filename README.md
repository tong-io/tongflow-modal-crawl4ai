# tongflow-modal-crawl4ai

Official TongFlow plugin. URL/link-to-text extraction with **Crawl4AI**, running on [Modal](https://modal.com). Fetches a page and turns its content into clean text.

## Capabilities

- **Link → text** (`link`) — fetch a web page and convert its content to text.

## Credentials

Add in TongFlow **Settings** (gear icon, top-right):

| Key | Required | Notes |
| --- | --- | --- |
| `MODAL_TOKEN_ID` | ✅ | Create at [modal.com/settings/tokens](https://modal.com/settings/tokens). |
| `MODAL_TOKEN_SECRET` | ✅ | Paired with `MODAL_TOKEN_ID`. |

On first use the plugin deploys to your Modal account automatically and caches the build. No Hugging Face token required.
