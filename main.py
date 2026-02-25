from liferaypedia_openzim_reader.zimreader import extract_zim_to_json

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python zim_to_json.py <input.zim> <output.json>")
        sys.exit(1)

    extract_zim_to_json(sys.argv[1], sys.argv[2], max_objects=40)
