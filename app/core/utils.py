import re

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
    """
    if not text:
        return ""

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
    return result.strip()


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



