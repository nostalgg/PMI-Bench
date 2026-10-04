import json


def build_messages(policy, question, documents, max_document_chars=1000):
    if (not isinstance(policy, str) or not policy.strip()
            or not isinstance(question, str) or not question.strip()
            or not isinstance(documents, list) or len(documents) > 20
            or not isinstance(max_document_chars, int) or isinstance(max_document_chars, bool)
            or not 1 <= max_document_chars <= 5000):
        raise ValueError('Invalid prompt input')
    data = []
    for document in documents:
        if (not isinstance(document, dict)
                or not isinstance(document.get('name'), str) or not document['name']
                or not isinstance(document.get('content'), str)):
            raise ValueError('Invalid document')
        data.append({'name': document['name'], 'content': document['content'][:max_document_chars]})
    return [{'role': 'system', 'content': policy},
            {'role': 'user', 'content': json.dumps({'question': question, 'documents': data}, ensure_ascii=False)}]
