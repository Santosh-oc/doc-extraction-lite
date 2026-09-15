from typing import List, Dict
from app.schemas import FieldDefinition

def build_extraction_prompt(
    page_texts: Dict[str, str],
    field_defs: List[FieldDefinition],
    instructions: str = None
) -> Dict[str, str]:
    system_message = (
        "You are an expert document extraction AI. Your task is to extract specific fields "
        "from the provided document text. You must respond with a JSON object where the "
        "top-level key is 'fields' and its value is a JSON array of objects. Each object "
        "in this array must correspond to a requested field and contain 'name', 'value', "
        "'confidence' (0.0-1.0), 'page' (1-indexed), and 'evidence' (the exact text snippet found). "
        "If a field is not found, its 'value' should be null, 'found' should be false, and 'confidence', 'page', 'evidence' should be null. "
        "Do not guess values. Extract only what is explicitly present in the document."
    )

    document_content = []
    for page_num, text in page_texts.items():
        document_content.append(f"--- Page {page_num} ---")
        document_content.append(text)
    document_content_str = "\n".join(document_content)

    field_definitions_str = "\n".join([
        f"- Name: {f.name}, Description: {f.description}, Type: {f.type}, Required: {f.required}"
        for f in field_defs
    ])

    user_message = (
        f"Document Text:\n{document_content_str}\n\n"
        f"Fields to Extract:\n{field_definitions_str}\n\n"
        f"Instructions: {instructions if instructions else 'Extract all specified fields. If a field is not found, return null for its value.'}\n\n"
        "Your response must be a JSON object in the format: "
        "{\"fields\": [{\"name\": \"field_name\", \"value\": \"extracted_value\", \"confidence\": 0.9, \"page\": 1, \"evidence\": \"text_evidence\"}, ...]}\n"
        "Ensure all fields are present in the output JSON array, even if their value is null."
    )

    return {"system": system_message, "user": user_message}
