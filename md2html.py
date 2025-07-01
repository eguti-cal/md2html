import argparse
import re
import html

# css
def get_styling_css():
    return """<style>
    body { 
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", Helvetica, Arial, sans-serif; 
        line-height: 1.5;
    }
    ul, ol { padding-left: 2em; }
    li { margin-bottom: 0.2em; }
    pre {
        background-color: #f4f4f4; border: 1px solid #ddd;
        border-radius: 4px; padding: 16px; overflow-x: auto;
    }
    code {
        font-family: Consolas, 'Courier New', monospace; background-color: #f4f4f4;
        padding: 2px 4px; border-radius: 3px;
    }
    pre code { background-color: transparent; border: none; padding: 0; }
    blockquote { border-left: 4px solid #ddd; padding-left: 16px; color: #555; }
    details {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 0.75em 1.5em;
        margin: 1em 0;
    }
    summary {
        cursor: pointer;
        font-weight: bold;
        margin: -0.75em -1.5em;
        padding: 0.75em 1.5em;
    }
    details[open] > summary {
        border-bottom: 1px solid #ddd;
        margin-bottom: 1em;
    }
</style>"""

def parse_inline(text):
    """行内のインライン要素を解析する（変更なし）"""
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    return text

def markdown_to_html(markdown_text):
    html_lines = [get_styling_css()]
    lines = markdown_text.strip().split('\n')

    in_code_block = False; is_first_line_of_code = False
    in_details_block = False
    in_blockquote = False
    list_stack = [(-1, None)] 

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # --- トップレベルのブロック処理 ---
        if list_stack[-1][0] == -1 and line.startswith('```'):
            if in_code_block: html_lines.append('</code></pre>'); in_code_block = False
            else: html_lines.append('<pre><code>'); in_code_block = True; is_first_line_of_code = True
            i += 1; continue
        if in_code_block:
            if is_first_line_of_code: html_lines[-1] += html.escape(line); is_first_line_of_code = False
            else: html_lines.append(html.escape(line))
            i += 1; continue
        if line.startswith(':::details'):
            summary_text = line[len(':::details'):].strip() or "詳細"
            html_lines.append(f'<details><summary>{html.escape(summary_text)}</summary>'); in_details_block = True; i += 1; continue
        if line.startswith(':::') and in_details_block:
            html_lines.append('</details>'); in_details_block = False; i += 1; continue

        # --- リスト、引用、見出し、段落などの処理 ---
        indent = len(line) - len(line.lstrip(' '))
        line_content = line.lstrip(' ')
        
        list_type = None; content_offset = 0
        ol_match = re.match(r'^(\d+)\. ', line_content)
        if line_content.startswith('- '): list_type = 'ul'; content_offset = 2
        elif ol_match: list_type = 'ol'; content_offset = len(ol_match.group(0))
        
        is_new_list_item = list_type is not None
        in_list_block = list_stack[-1][1] is not None
        is_list_continuation = (in_list_block and not is_new_list_item and 
                                line.strip() and indent > list_stack[-1][0])

        if is_new_list_item or is_list_continuation:
            if in_blockquote: html_lines.append('</blockquote>'); in_blockquote = False
            if is_new_list_item:
                content = line_content[content_offset:]
                while indent < list_stack[-1][0] or (indent == list_stack[-1][0] and list_type != list_stack[-1][1]):
                    closed_type = list_stack.pop()[1]; html_lines.append(f"</li></{closed_type}>")
                if indent > list_stack[-1][0]:
                    tag = f'<{list_type}>'
                    if html_lines[-1].startswith('<li>'): html_lines[-1] += tag
                    else: html_lines.append(tag)
                    list_stack.append((indent, list_type))
                if html_lines[-1].startswith('<li>'): html_lines.append('</li>')
                html_lines.append(f'<li>{parse_inline(content)}')
            elif is_list_continuation:
                if line_content.startswith('```'):
                    html_lines.append('<pre><code>'); is_first = True
                    code_block_indent = indent; i += 1
                    while i < len(lines):
                        code_line = lines[i]
                        if code_line.lstrip().startswith('```'): html_lines.append('</code></pre>'); break
                        unindented_line = code_line[code_block_indent:] if len(code_line) >= code_block_indent else code_line
                        if is_first: html_lines[-1] += html.escape(unindented_line); is_first = False
                        else: html_lines.append(html.escape(unindented_line))
                        i += 1
                else: html_lines[-1] += f"<br>{parse_inline(line.strip())}"
        else:
            while list_stack[-1][1] is not None:
                closed_type = list_stack.pop()[1]; html_lines.append(f"</li></{closed_type}>")
            if in_blockquote and not line.startswith('> '): html_lines.append('</blockquote>'); in_blockquote = False
            
            if line.lstrip().startswith('#'):
                level = len(line_content.split(' ')[0]); content = line_content[level:].strip()
                html_lines.append(f'<h{level}>{parse_inline(content)}</h{level}>')
            elif line.lstrip().startswith('> '):
                if not in_blockquote: html_lines.append('<blockquote>'); in_blockquote = True
                content = line_content[2:]; html_lines.append(f'<p>{parse_inline(content)}</p>')
            elif line.strip(): # 空行でない、かつ他のどのブロックでもない -> 段落の開始
                paragraph_lines = []
                temp_i = i
                while temp_i < len(lines):
                    p_line = lines[temp_i]
                    p_line_content = p_line.lstrip()
                    # 段落の終了条件
                    if (not p_line.strip() or p_line_content.startswith('- ') or
                        re.match(r'^\d+\. ', p_line_content) or p_line_content.startswith('#') or
                        p_line_content.startswith('>') or p_line_content.startswith('```') or
                        p_line_content.startswith(':::')):
                        break
                    paragraph_lines.append(p_line)
                    temp_i += 1
                
                # 収集した段落を<br>で連結して処理
                processed_content = "<br>".join([parse_inline(p.strip()) for p in paragraph_lines])
                html_lines.append(f"<p>{processed_content}</p>")
                
                i = temp_i - 1 # メインループのインデックスを更新
            # 空行はここでは何もしない（段落の区切りとなる）
        i += 1
    
    while list_stack[-1][1] is not None:
        closed_type = list_stack.pop()[1]; html_lines.append(f"</li></{closed_type}>")
    if in_blockquote: html_lines.append('</blockquote>')
    if in_details_block: html_lines.append('</details>')
        
    return '\n'.join(html_lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default="input.md")
    parser.add_argument("-o", "--output", default="output.html")

    args = parser.parse_args()
    input_file = args.input
    output_file = args.output

    with open(input_file, "r", encoding="utf-8") as f:
        sample_markdown_v3 = f.read()

    html_output = markdown_to_html(sample_markdown_v3)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_output)


if __name__ == '__main__':
    main()
