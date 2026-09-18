import re
import os
import urllib.parse

def sanitize_bible_links(text: str) -> str:
    """
    Scans text for any external Bible links (Bible Gateway, Bible.com, ESV.org, YouVersion, Blue Letter Bible, etc.)
    and automatically transforms them into the official Daily Manna web app URL:
    https://dailymannav1.vercel.app/read?passage={passage}&version=ESV
    """
    if not text:
        return ""

    web_app_url = os.getenv("WEB_APP_URL", "https://dailymannav1.vercel.app").rstrip("/")

    # 1. Replace Bible Gateway passage links
    def replace_bg(match):
        full_url = match.group(0)
        trailing = ""
        while full_url and full_url[-1] in [')', ']', '}', '.', ',', ';', '!', '?', '*']:
            trailing = full_url[-1] + trailing
            full_url = full_url[:-1]

        parsed = urllib.parse.urlparse(full_url)
        qs = urllib.parse.parse_qs(parsed.query)
        search = qs.get("search", [""])[0]
        version = qs.get("version", ["ESV"])[0]

        target_version = "KJV" if version.upper() == "KJV" else "ESV"

        if search:
            clean_search = urllib.parse.quote_plus(search)
            return f"{web_app_url}/read?passage={clean_search}&version={target_version}{trailing}"
        return f"{web_app_url}{trailing}"

    text = re.sub(r'https?://(?:www\.)?biblegateway\.com[^\s<>"\'*]*', replace_bg, text, flags=re.IGNORECASE)

    # 2. Replace esv.org passage links
    def replace_esv(match):
        full_url = match.group(0)
        trailing = ""
        while full_url and full_url[-1] in [')', ']', '}', '.', ',', ';', '!', '?', '*']:
            trailing = full_url[-1] + trailing
            full_url = full_url[:-1]

        parsed = urllib.parse.urlparse(full_url)
        path = parsed.path.strip('/')
        if path:
            clean_passage = urllib.parse.quote_plus(path.replace('+', ' '))
            return f"{web_app_url}/read?passage={clean_passage}&version=ESV{trailing}"
        return f"{web_app_url}{trailing}"

    text = re.sub(r'https?://(?:www\.)?esv\.org[^\s<>"\'*]*', replace_esv, text, flags=re.IGNORECASE)

    # 3. Replace generic external bible websites
    def replace_generic_bible(match):
        full_url = match.group(0)
        trailing = ""
        while full_url and full_url[-1] in [')', ']', '}', '.', ',', ';', '!', '?', '*']:
            trailing = full_url[-1] + trailing
            full_url = full_url[:-1]
        return f"{web_app_url}{trailing}"

    text = re.sub(r'https?://(?:www\.)?(?:bible\.com|youversion\.com|blueletterbible\.org|biblehub\.com)[^\s<>"\'*]*', replace_generic_bible, text, flags=re.IGNORECASE)

    return text

def normalize_phone_number(raw_number: str) -> str:
    """
    Sanitizes an incoming phone number (sender ID) by:
    - Stripping any '+' prefix.
    - Removing any spaces, dashes, or parentheses.
    - Extracting the numeric core from the '@c.us' or '@g.us' suffix.
    """
    # Remove suffix if present
    if '@' in raw_number:
        raw_number = raw_number.split('@')[0]
        
    # Remove '+' and any non-digit characters
    sanitized = re.sub(r'\D', '', raw_number)
    
    return sanitized


def format_for_whatsapp(text: str, strip_all_asterisks: bool = True) -> str:
    """
    Converts standard Markdown (tables, headers, double asterisks, horizontal rules)
    into clean, natural, WhatsApp-friendly formatted text without unwanted asterisks.
    Also ensures any Bible references link strictly to the official Daily Manna web app.
    """
    if not text:
        return ""

    text = sanitize_bible_links(text)

    lines = text.splitlines()
    output_lines = []
    
    in_table = False
    headers = []
    
    for line in lines:
        stripped = line.strip()

        # Remove horizontal divider lines (---, ***, ___, —, --)
        if re.match(r'^[-*_—]{1,}$', stripped):
            output_lines.append("")
            continue

        # Check if line is a table divider like |---|---| or |:---|:---|
        if re.match(r'^\|?[\s:-]*[-]{2,}[\s:-]*(\|[\s:-]*[-]{2,}[\s:-]*)+\|?$', stripped):
            in_table = True
            continue

        # Check if line starts with | but doesn't end with | (incomplete table line)
        if stripped.startswith('|') and not stripped.endswith('|'):
            cleaned_text = re.sub(r'^\|+\s*|\s*\*+|\*+|\s*_+$', '', stripped).strip()
            if cleaned_text:
                if strip_all_asterisks:
                    output_lines.append(f"📌 {cleaned_text.upper()}")
                else:
                    output_lines.append(f"*{cleaned_text}*")
            continue

        # Check if line is a table row like | col1 | col2 |
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [re.sub(r'^\*+|\*+$|^_+|_+$', '', cell.strip()) for cell in stripped.strip('|').split('|')]
            
            if not headers and not in_table:
                headers = cells
                continue
            
            in_table = True
            if headers and len(cells) == len(headers):
                main_item = cells[0]
                details = []
                for h, v in zip(headers[1:], cells[1:]):
                    clean_h = h.strip('*_')
                    clean_v = v.strip('*_')
                    if clean_h and clean_v:
                        details.append(f"{clean_h}: {clean_v}")
                
                if details:
                    if strip_all_asterisks:
                        output_lines.append(f"📌 {main_item.upper()}\n  " + "\n  ".join([f"• {d}" for d in details]))
                    else:
                        output_lines.append(f"📌 *{main_item}*\n  " + "\n  ".join([f"• {d}" for d in details]))
                else:
                    output_lines.append(f"• {main_item}")
            else:
                row_str = " - ".join([c for c in cells if c])
                output_lines.append(f"• {row_str}")
            continue
        else:
            in_table = False
            headers = []

        # Convert Markdown headers (## 1. Header -> 📌 1. HEADER)
        header_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if header_match:
            header_text = header_match.group(2).strip()
            header_text = re.sub(r'^\*+|\*+$|^_+|_+$', '', header_text)
            if strip_all_asterisks:
                output_lines.append(f"📌 {header_text.upper()}")
            else:
                output_lines.append(f"*{header_text}*")
            continue

        # Remove asterisks if strip_all_asterisks is True
        if strip_all_asterisks:
            processed_line = line.replace('*', '')
        else:
            # Convert double asterisks Markdown bold **text** to WhatsApp single asterisk *text*
            processed_line = re.sub(r'\*\*(.*?)\*\*', r'*\1*', line)

        output_lines.append(processed_line)

    result = "\n".join(output_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return sanitize_bible_links(result.strip())


def split_long_message(text: str, max_chars: int = 1200) -> list[str]:
    """
    Splits a long message into multiple smaller chunks at natural section 
    or paragraph boundaries so it fits into consecutive WhatsApp messages 
    without getting truncated.
    """
    if not text or len(text) <= max_chars:
        return [text] if text else []

    sections = re.split(r'(?=\n📌|\n\n)', text)
    chunks = []
    current_chunk = ""

    for section in sections:
        if not section:
            continue
        if len(current_chunk) + len(section) > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = section
        else:
            current_chunk += section

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            final_chunks.append(chunk)
        else:
            lines = chunk.splitlines(keepends=True)
            sub_chunk = ""
            for line in lines:
                if len(sub_chunk) + len(line) > max_chars and sub_chunk:
                    final_chunks.append(sub_chunk.strip())
                    sub_chunk = line
                else:
                    sub_chunk += line
            if sub_chunk.strip():
                final_chunks.append(sub_chunk.strip())

    return final_chunks



