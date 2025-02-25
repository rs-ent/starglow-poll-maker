
import ast

def link_picker(group):
    sns_str = group.get('sns_parsed', [])
    if not sns_str:
        return
    urls = ast.literal_eval(sns_str)
    url = ''
    for domain in ['x.com', 'twitter.com', 'instagram.com', 'youtube.com']:
        for u in urls:
            if domain in u:
                url = u
                break
        if url:
            break
        
    return url