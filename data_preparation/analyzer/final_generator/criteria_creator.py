import json
from typing import List
from pydantic import BaseModel, Field
# Importiamo il client di OpenAI, supponendo che sia accessibile in questo modo
from interviewer.llm_service import get_structured_llm_response
from . import prompts_criteria

# --- 1. Definizione dello Schema Dati con Pydantic ---

class Criterion(BaseModel):
    step_id: int = Field(description="L'ID del reasoning step a cui questo criterio si riferisce.")
    criteria: str = Field(description="Il testo completo dell'accomplishment criterion per lo step corrispondente.")

class CriteriaForCase(BaseModel):
    question_id: str = Field(description="L'ID del caso di studio a cui questi criteri appartengono. Deve corrispondere all'ID del caso in input.")
    accomplishment_criteria: List[Criterion] = Field(description="Una lista di criteri, uno per ogni reasoning step del caso.")

class CriteriaCollection(BaseModel):
    """Il modello di primo livello che contiene la lista dei criteri per tutti i casi."""
    criteria_sets: List[CriteriaForCase] = Field(description="Una lista contenente i set di criteri per ciascun caso fornito in input.")

# --- 2. Logica di Generazione ---

FINAL_MODEL = "gpt-4.1-2025-04-14"

def generate_final_criteria(icp_text: str, cases_json_str: str, seniority_level: str) -> CriteriaCollection | None:
    """
    Genera una collezione di accomplishment criteria strutturati in formato JSON.
    """
    print("1. Creazione del prompt per la generazione dei criteri...")
    final_prompt = prompts_criteria.create_criteria_generation_prompt(icp_text, cases_json_str, seniority_level)

    print(f"2. Invio della richiesta al modello '{FINAL_MODEL}' per la generazione dei criteri...")
    
    # vvv MODIFICA QUI: Usiamo la nuova funzione del servizio LLM vvv
    tool_call_args = get_structured_llm_response(
        prompt=final_prompt,
        model=FINAL_MODEL,
        system_prompt=prompts_criteria.SYSTEM_PROMPT,
        tool_name="save_generated_criteria",
        tool_schema=CriteriaCollection.model_json_schema()
    )

    if not tool_call_args:
        print("Errore critico: la chiamata all'LLM per i criteri non ha restituito dati.")
        return None

    try:
        print("3. Output strutturato ricevuto, ora lo valido...")
        parsed_json = json.loads(tool_call_args)
        validated_data = CriteriaCollection.model_validate(parsed_json)
        print("4. Criteri validati con successo. Generazione completata.")
        return validated_data
    except Exception as e:
        print(f"Errore critico durante la validazione dei criteri: {e}")
        return None