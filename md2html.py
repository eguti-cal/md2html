import re
import html

def get_styling_css_v2():
    """CSSスタイル（v5から変更なし）"""
    return """<style>
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans JP", Helvetica, Arial, sans-serif; line-height: 1.6; }
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

def markdown_to_html_v6(markdown_text):
    """コードブロックの先頭の改行を修正したパーサー"""
    html_lines = [get_styling_css_v2()]
    lines = markdown_text.strip().split('\n')

    in_code_block = False
    is_first_line_of_code = False # ★コードブロックの最初の行かどうかのフラグ
    in_details_block = False
    in_blockquote = False
    in_list_block = False
    list_indent_stack = [-1] 

    i = 0
    while i < len(lines):
        line = lines[i]
        
        # --- コードブロックの処理 ---
        if line.startswith('```'):
            if in_code_block:
                html_lines.append('</code></pre>')
                in_code_block = False
            else:
                html_lines.append('<pre><code>')
                in_code_block = True
                is_first_line_of_code = True # ★フラグをTrueにセット
            i += 1
            continue

        if in_code_block:
            # ▼▼▼ ここのロジックを修正 ▼▼▼
            if is_first_line_of_code:
                # 最初の行は<pre><code>タグに直接連結する
                html_lines[-1] += html.escape(line)
                is_first_line_of_code = False # フラグをFalseに戻す
            else:
                # 2行目以降は新しい行として追加
                html_lines.append(html.escape(line))
            i += 1
            continue
        # ▲▲▲ 修正ここまで ▲▲▲

        if line.startswith(':::details'):
            # (v5から変更なし)
            summary_text = line[len(':::details'):].strip() or "詳細"
            html_lines.append(f'<details><summary>{html.escape(summary_text)}</summary>')
            in_details_block = True; i += 1; continue
        if line.startswith(':::') and in_details_block:
            html_lines.append('</details>'); in_details_block = False; i += 1; continue

        # --- 通常のMarkdown要素の処理 (v5から変更なし) ---
        indent = len(line) - len(line.lstrip(' '))
        line_content = line.lstrip(' ')
        is_new_list_item = line_content.startswith('- ')
        is_list_continuation = (in_list_block and not is_new_list_item and 
                                line.strip() and indent >= list_indent_stack[-1] + 2)

        if is_new_list_item or is_list_continuation:
            if in_blockquote: html_lines.append('</blockquote>'); in_blockquote = False
            in_list_block = True
            if is_new_list_item:
                content = line_content[2:]
                while indent < list_indent_stack[-1]:
                    html_lines.append('</li></ul>'); list_indent_stack.pop()
                if indent > list_indent_stack[-1]:
                    if html_lines[-1].startswith('<li>'): html_lines[-1] += '<ul>'
                    else: html_lines.append('<ul>')
                    list_indent_stack.append(indent)
                if html_lines[-1].startswith('<li>'): html_lines.append('</li>')
                html_lines.append(f'<li>{parse_inline(content)}')
            else:
                html_lines[-1] += f"<br>{parse_inline(line.strip())}"
        else:
            in_list_block = False
            while list_indent_stack[-1]!=-1: html_lines.append('</li></ul>'); list_indent_stack.pop()
            if in_blockquote and not line.startswith('> '): html_lines.append('</blockquote>'); in_blockquote = False
            if line.startswith('#'):
                level = len(line.split(' ')[0]); content = line[level:].strip()
                html_lines.append(f'<h{level}>{parse_inline(content)}</h{level}>')
            elif line.startswith('> '):
                if not in_blockquote: html_lines.append('<blockquote>'); in_blockquote = True
                content = line[2:]; html_lines.append(f'<p>{parse_inline(content)}</p>')
            elif not line.strip(): pass
            else: html_lines.append(f'<p>{parse_inline(line)}</p>')
        i += 1
    
    while list_indent_stack[-1]!=-1: html_lines.append('</li></ul>'); list_indent_stack.pop()
    if in_blockquote: html_lines.append('</blockquote>')
    if in_details_block: html_lines.append('</details>')
        
    return '\n'.join(html_lines)


if __name__ == '__main__':

    with open("input.md", "r", encoding="utf-8") as f:
        sample_markdown_v3 = f.read()

    html_output = markdown_to_html_v6(sample_markdown_v3)
    # print(html_output)

    # 生成されたHTMLをファイルに保存してブラウザで確認することもできます
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(html_output)