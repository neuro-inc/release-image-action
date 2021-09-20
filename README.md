# release-image-action
GitHub action for publishing Docker image on ghcr.io


Workflow with the action usage example:

```
name: Release Image

on:
  workflow_run:
	workflows:
	  - CI
	types:
	  - completed

permissions:
  contents: read
  packages: write

jobs:
  publish:
	name: Publish
	runs-on: ubuntu-latest
	concurrency: release_image
	steps:
	- name: Checkout commit
	  uses: neuro-inc/release-image-action@v21.9.1
	  with:
		github: ${{ toJson(github) }}
		image: platformstorageapi
		token: ${{ secrets.GITHUB_TOKEN }}
```


Arguments:

`github` -- JSON string, the content of `github` workflow context.
`image` -- the image name without tag, e.g. `platformstorageapi`.
`token` -- secret github token, pass: `${{ secrets.GITHUB_TOKEN }}` or generated Personal Access Token.
`artifact` -- uploaded artifact name, `image` by default.  Use https://github.com/neuro-inc/upload-image-action` to build the artifact.
