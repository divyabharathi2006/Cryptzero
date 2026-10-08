from pathlib import Path

source_files = [
    Path(r'D:\Project 10\indian-passwords-sorted.txt'),
    Path(r'D:\Project 10\indian-passwords-length8-20.txt'),
    Path(r'D:\Project 10\indian-passwords-length8-20-sorted.txt'),
    Path(r'D:\Project 10\10_million_password_list_top_1000000.txt'),
]

destination = Path(r'D:\Project 10\cryptzero\wordlists\wordlist.txt')
destination.parent.mkdir(parents=True, exist_ok=True)

seen = set()
count = 0

with destination.open('w', encoding='utf-8', errors='ignore') as out:
    for src in source_files:
        if not src.exists():
            print(f'SKIP: {src} does not exist')
            continue
        with src.open('r', encoding='utf-8', errors='ignore') as fh:
            for raw in fh:
                word = raw.strip()
                if not word or word.startswith('#'):
                    continue
                if word in seen:
                    continue
                seen.add(word)
                out.write(word + '\n')
                count += 1

print(f'Wrote {count} unique entries to {destination}')
