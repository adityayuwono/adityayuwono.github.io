# Publishing Cozy Sushi

Build using Unity's WebGL profile with Decompression Fallback enabled. Keep the
build at `cozysushi`, including index.html, Build, TemplateData and StreamingAssets.

From the website repository root, run after every build:

```powershell
python cozysushi/tools/package_webgl.py pack
```

Python 3.11 or newer is required; no extra packages are needed. Files larger than
90 MiB are split into 50 MiB chunks in `.build-chunks`. A manifest records file
sizes and SHA-256 checksums. Originals stay on disk and are ignored by Git.
Commit the updated chunks, manifest, build files and generated `.gitignore`.
Never commit the ignored oversized originals. Existing tracked originals must
be removed from Git's index, and any unpushed commit containing them amended.

On GitHub, select **Settings > Pages > Build and deployment > Source > GitHub
Actions**. Push to `master` to deploy, or run **Deploy website** manually under
Actions. The workflow stages the entire website, preserves other games and
force-update.json, reconstructs the split files and verifies their checksums
before publishing. Git LFS is not needed. The game URL is:

https://adityayuwono.github.io/cozysushi/

The workflow file lives at `.github/workflows/deploy-pages.yml`, because GitHub
only discovers workflow files at the repository root.
