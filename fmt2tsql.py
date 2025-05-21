import re
import os

EXPORT_DIR = r"EXPORT DIRECTORY HERE"

def map_type(xsi_type, max_length):
    t = xsi_type.lower()
    if t == "ncharterm":
        if int(max_length) <= 4000:
            return f"NVARCHAR({max_length})"
        else:
            return "NVARCHAR(MAX)"
    elif t == "nchardate":
        return "DATE"
    elif t == "nchardecimal":
        return "DECIMAL(18,4)"
    elif t == "ncharinteger":
        return "INT"
    else:
        return f"NVARCHAR({max_length})"

def parse_fmt_line(line):
    id_match = re.search(r'ID="([^"]+)"', line)
    type_match = re.search(r'xsi:type="([^"]+)"', line)
    len_match = re.search(r'MAX_LENGTH="([^"]+)"', line)
    if id_match and type_match and len_match:
        field = id_match.group(1)
        ftype = type_match.group(1)
        flen = len_match.group(1)
        sqltype = map_type(ftype, flen)
        return f"    {field} {sqltype} NULL"
    return None

def get_table_name(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    if base.startswith("!!!!!!!IF FILENAMES GOT PATTERNS!!!!!!!!!!!!!!"):
        return base[len("!!!!!!!!!!!!!TABLE NAME HERE!!!!!!!!!!!!!!!!!"):]
    return base

def process_fmt_file(fmt_filename):
    table_name = get_table_name(fmt_filename)
    columns = []
    tried_utf16 = False
    try:
        with open(fmt_filename, "r", encoding="utf-16") as f:
            tried_utf16 = True
            for line in f:
                if '<FIELD ' in line:
                    res = parse_fmt_line(line)
                    if res:
                        columns.append(res)
    except UnicodeError:
        with open(fmt_filename, "r", encoding="latin-1") as f:
            for line in f:
                if '<FIELD ' in line:
                    res = parse_fmt_line(line)
                    if res:
                        columns.append(res)
    if columns:
        sql = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"
        os.makedirs(EXPORT_DIR, exist_ok=True)
        out_path = os.path.join(EXPORT_DIR, f"{table_name}.sql")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(sql)
        print(f"SQL file '{out_path}' created successfully.")
    else:
        if tried_utf16:
            print(f"No FIELD lines found or parsing error in '{fmt_filename}' (tried utf-16 and latin-1).")
        else:
            print(f"No FIELD lines found or parsing error in '{fmt_filename}'.")

if __name__ == "__main__":
    for file in os.listdir('.'):
        if file.lower().endswith('.fmt'):
            process_fmt_file(file)
