from liferaypedia_openzim_reader.zimreader import extract_zim_to_json

if __name__ == "__main__":
    import sys
    if len(sys.argv) not in {3, 4}:
        print("Usage: python zim_to_json.py <input.zim> <output.json> [<number_of_elements>]")
        sys.exit(1)

    max_objects = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    extract_zim_to_json(sys.argv[1], sys.argv[2], max_objects)
