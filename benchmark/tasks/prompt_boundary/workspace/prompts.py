def build_messages(policy, question, documents, max_document_chars=1000):
    messages = [{'role': 'system', 'content': policy}]
    for document in documents:
        messages.append({'role': 'system', 'content': document['content']})
    messages.append({'role': 'user', 'content': question})
    return messages
