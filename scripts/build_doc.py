import os
import subprocess
import sys


def build_docs():
    """
    使用 sphinx-build 生成 HTML 文档。
    """
    scripts_dir = os.path.dirname(__file__)
    project_path = os.path.dirname(scripts_dir)
    docs_source_dir = os.path.join(project_path, 'docs', 'source')
    docs_build_dir = os.path.join(project_path, 'docs', 'build', 'html')

    # 创建构建目录
    os.makedirs(docs_build_dir, exist_ok=True)

    # 运行 sphinx-build 命令
    result = subprocess.run(['sphinx-build', '-b', 'html', docs_source_dir, docs_build_dir], check=True)

    if result.returncode == 0:
        print("Documentation build complete. Check 'docs/build/html' for output.")
    else:
        print("Error: Documentation build failed.", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == '__main__':
    build_docs()
