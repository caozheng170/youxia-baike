"""One-shot deploy of the backend to a Hugging Face Docker Space.

Uses the huggingface_hub HTTP API (no git required). Run it like:

    .\\.venv\\Scripts\\python.exe deploy_hf.py

You'll be asked to paste your HF *write* token (input is hidden). The token
stays on your machine. Get a token at https://huggingface.co/settings/tokens
"""

import os
import sys
from getpass import getpass

from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

REPO_ID = "caozheng/youxia"
REPO_TYPE = "space"

# Only the backend needs to go up. Skip the frontend, data, venv, git, secrets.
IGNORE = [
    "client/**",
    "data/**",
    ".venv/**",
    ".git/**",
    "**/__pycache__/**",
    "*.pyc",
    ".env",
    ".env.*",
    "start.sh",
    "deploy_hf.py",
    "deploy_hf.bat",
    "netlify.toml",
]


def _token_role(whoami: dict) -> str:
    auth = whoami.get("auth") or {}
    token = auth.get("accessToken") or {}
    return (token.get("role") or "unknown").lower()


def _upload(api: HfApi, *, create_pr: bool) -> object:
    return api.upload_folder(
        folder_path=".",
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        ignore_patterns=IGNORE,
        commit_message="Deploy 游侠百科 backend (Docker)",
        create_pr=create_pr,
    )


def main() -> int:
    token = os.environ.get("HF_TOKEN") or getpass("粘贴你的 HF write 令牌 (hf_...): ").strip()
    if not token:
        print("未提供令牌，已取消。", file=sys.stderr)
        return 1

    api = HfApi(token=token)

    try:
        who = api.whoami()
        role = _token_role(who)
        print(f"已登录为: {who.get('name')}  (令牌权限: {role})")
        if role not in ("write", "admin", "unknown"):
            print(
                "\n⚠ 当前令牌看起来是只读 (read)。请重新创建 Write 令牌：\n"
                "  https://huggingface.co/settings/tokens → New token → 类型选 Write\n",
                file=sys.stderr,
            )
            return 1
    except Exception as e:
        print(f"令牌校验失败: {e}", file=sys.stderr)
        return 1

    print(f"开始上传到 Space: {REPO_ID} ...")

    try:
        info = _upload(api, create_pr=False)
        print("\n上传完成！已直接提交到 main 分支。")
    except HfHubHTTPError as e:
        if e.response.status_code != 403:
            raise
        print("直接提交 main 被拒绝 (403)，改用 Pull Request 方式重试 ...")
        try:
            info = _upload(api, create_pr=True)
            pr_url = getattr(info, "pr_url", None) or getattr(info, "pr_revision", None)
            print("\n上传完成！已创建 Pull Request。")
            if pr_url:
                print(f"  请到 HF 页面合并 PR: {pr_url}")
            else:
                print(f"  请到 Space 的 Community 标签合并 PR: https://huggingface.co/spaces/{REPO_ID}/discussions")
        except HfHubHTTPError as e2:
            if e2.response.status_code == 403:
                print(
                    "\n仍然 403 Forbidden。请检查：\n"
                    "  1. 令牌类型必须是 Write（不是 Read）\n"
                    "     https://huggingface.co/settings/tokens\n"
                    "  2. Space 所有者必须是 caozheng（当前登录账号）\n"
                    "  3. 若用的是 Fine-grained token，需勾选该 Space 的 write 权限\n",
                    file=sys.stderr,
                )
            raise

    print(f"  构建/日志: https://huggingface.co/spaces/{REPO_ID}?logs=build")
    print(f"  接口文档:  https://{REPO_ID.replace('/', '-')}.hf.space/docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
