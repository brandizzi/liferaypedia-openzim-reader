import json
import base64
from libzim.reader import Archive


def extract_zim_to_json(zim_path: str, output_json: str, max_objects: int = 40):
    zim = Archive(zim_path)

    results = []
    total = zim.entry_count
    limit = min(max_objects, total)

    for entry_id in range(limit):
        try:
            entry = zim._get_entry_by_id(entry_id)
            item = entry.get_item()
        except Exception as e:
            print(f'Skipping entry {entry_id} due to error: {e}')
            continue

        raw_content = bytes(item.content)

        if item.mimetype == "application/json":
            continue

        if item.mimetype.startswith("text"):
            content = raw_content.decode("utf-8", errors="replace")
        else:
            content = base64.b64encode(raw_content).decode("ascii")

        entry_path = entry.path

        namespace = "main"  # default
        if entry_path.startswith('-/') or entry_path.startswith('/'):
            namespace = "main"
        elif '/' in entry_path:
            namespace_part = entry_path.split('/')[0]
            if namespace_part and namespace_part != '-':
                namespace = namespace_part

        # Determine type based on namespace and other indicators
        entry_type = "unknown"
        if namespace == "main":
            entry_type = "page"
        elif namespace == "A":
            entry_type = "article"
        elif namespace == "I":
            entry_type = "image"
        elif namespace == "Category":
            entry_type = "category"
        elif namespace == "Discussion":
            entry_type = "discussion"
        elif namespace == "File":
            entry_type = "file"
        elif namespace == "Template":
            entry_type = "template"
        elif namespace == "Help":
            entry_type = "help"
        elif namespace == "Portal":
            entry_type = "portal"
        elif namespace == "Book":
            entry_type = "book"
        elif namespace == "MediaWiki":
            entry_type = "mediawiki"

        # Additional type detection based on file extension
        if '.' in entry_path:
            extension = entry_path.split('.')[-1].lower()
            if extension in ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']:
                entry_type = "image"
            elif extension in ['pdf', 'doc', 'docx', 'txt', 'rtf']:
                entry_type = "document"
            elif extension in ['mp3', 'wav', 'ogg', 'flac', 'aac']:
                entry_type = "audio"
            elif extension in ['mp4', 'avi', 'mov', 'wmv', 'flv']:
                entry_type = "video"
            elif extension in ['zip', 'rar', '7z', 'tar', 'gz']:
                entry_type = "archive"

        results.append({
            "id": entry_id,
            "path": entry.path,
            "title": entry.title,
            "type": entry_type,
            "mime_type": item.mimetype,
            "namespace": namespace,
            "content": content,
            "size_bytes": item.size
        })

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Extracted {len(results)} entries to {output_json}")
    print(f"Namespaces found: {set(item['namespace'] for item in results)}")
    print(f"Types found: {set(item['type'] for item in results)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python zim_to_json.py <input.zim> <output.json>")
        sys.exit(1)

    extract_zim_to_json(sys.argv[1], sys.argv[2], max_objects=40)
