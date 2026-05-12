import os
import yaml
import markdown
from datetime import datetime
from pathlib import Path

# === Configuration ===
CONTENT_DIR = "content/blog"
OUTPUT_DIR = "blog"
TEMPLATE_DIR = "templates"
SITE_URL = ""  # Set if needed for absolute URLs

# === Helper Functions ===

def parse_post(filepath):
    """Parse a markdown file with YAML frontmatter."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.startswith("---"):
        return None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None

    meta = yaml.safe_load(parts[1])
    body_md = parts[2].strip()
    body_html = markdown.markdown(body_md, extensions=["fenced_code", "tables", "toc"])

    # Fallback date from filename if not in frontmatter
    filename = Path(filepath).stem
    if "date" not in meta:
        try:
            meta["date"] = datetime.strptime(filename, "%Y%m%d").date()
        except ValueError:
            meta["date"] = datetime.today().date()
    elif isinstance(meta["date"], str):
        meta["date"] = datetime.strptime(meta["date"], "%Y-%m-%d").date()

    meta.setdefault("tags", [])
    meta.setdefault("description", "")
    meta.setdefault("title", filename)
    meta["slug"] = filename
    meta["body"] = body_html

    return meta


def load_template(name):
    """Load an HTML template from the templates directory."""
    path = os.path.join(TEMPLATE_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template, **kwargs):
    """Simple placeholder replacement: {{key}} -> value."""
    result = template
    for key, value in kwargs.items():
        result = result.replace("{{" + key + "}}", str(value))
    return result


def write_file(path, content):
    """Write content to a file, creating directories as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {path}")


# === Build Steps ===

def build():
    print("Building blog...\n")

    # Load templates
    post_template = load_template("post.html")
    index_template = load_template("blog_index.html")
    tag_template = load_template("tag.html")

    # Parse all posts
    posts = []
    for filename in os.listdir(CONTENT_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(CONTENT_DIR, filename)
            post = parse_post(filepath)
            if post:
                posts.append(post)

    # Sort by date, newest first
    posts.sort(key=lambda p: p["date"], reverse=True)
    print(f"Found {len(posts)} posts.\n")

    # --- Generate individual post pages ---
    print("Generating post pages:")
    for post in posts:
        tags_html = "".join(
            f'<a href="../tags/{tag}.html" class="tag">{tag}</a>' for tag in post["tags"]
        )
        date_str = post["date"].strftime("%B %d, %Y")
        html = render_template(
            post_template,
            title=post["title"],
            date=date_str,
            tags=tags_html,
            description=post["description"],
            content=post["body"],
        )
        write_file(os.path.join(OUTPUT_DIR, "posts", f"{post['slug']}.html"), html)

    # --- Generate blog index ---
    print("\nGenerating blog index:")
    post_list_html = ""
    for post in posts:
        tags_html = "".join(f'<span class="tag">{t}</span>' for t in post["tags"])
        date_str = post["date"].strftime("%B %d, %Y")
        post_list_html += f"""
        <article class="post-preview">
            <h3><a href="posts/{post['slug']}.html">{post['title']}</a></h3>
            <div class="post-meta"><time>{date_str}</time> {tags_html}</div>
            <p>{post['description']}</p>
        </article>
        """
    html = render_template(index_template, posts=post_list_html)
    write_file(os.path.join(OUTPUT_DIR, "index.html"), html)

    # --- Generate tag pages ---
    print("\nGenerating tag pages:")
    tag_map = {}
    for post in posts:
        for tag in post["tags"]:
            tag_map.setdefault(tag, []).append(post)

    for tag, tag_posts in tag_map.items():
        post_list_html = ""
        for post in tag_posts:
            date_str = post["date"].strftime("%B %d, %Y")
            post_list_html += f"""
            <article class="post-preview">
                <h3><a href="../posts/{post['slug']}.html">{post['title']}</a></h3>
                <div class="post-meta"><time>{date_str}</time></div>
                <p>{post['description']}</p>
            </article>
            """
        html = render_template(tag_template, tag=tag, posts=post_list_html)
        write_file(os.path.join(OUTPUT_DIR, "tags", f"{tag}.html"), html)

    # --- Generate tag index (list all tags) ---
    print("\nGenerating tag index:")
    all_tags_html = "\n".join(
        f'<li><a href="{tag}.html" class="tag">{tag} ({len(tposts)})</a></li>'
        for tag, tposts in sorted(tag_map.items())
    )
    all_tags_html = f'<ul class="tag-list">{all_tags_html}</ul>'
    tag_index_html = render_template(tag_template, tag="All Tags", posts=all_tags_html)
    write_file(os.path.join(OUTPUT_DIR, "tags", "index.html"), tag_index_html)

    print(f"\n✅ Done! Generated {len(posts)} posts, {len(tag_map)} tag pages.")


if __name__ == "__main__":
    build()