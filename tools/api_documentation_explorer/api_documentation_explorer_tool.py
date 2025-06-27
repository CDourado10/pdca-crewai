from langchain_openai import AzureChatOpenAI
from browser_use import Agent, BrowserConfig, Browser
from dotenv import load_dotenv
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

load_dotenv()

class ApiDocumentationExplorerInput(BaseModel):
    """Schema de entrada para ApiDocumentationExplorerTool."""
    task: str = Field(..., description="Descrição da dúvida, objetivo ou tarefa a ser respondida com base na documentação da API.")
    url: str = Field(None, description="URL da documentação da API (opcional). Se não fornecida, utilizar fontes padrão ou conhecimento prévio.")

class ApiDocumentationExplorerTool(BaseTool):
    name: str = "ApiDocumentationExplorerTool"
    description: str = (
        "Explora e extrai informações relevantes de documentações de API para responder a perguntas ou objetivos específicos. "
        "Recebe uma task obrigatória e uma URL de documentação opcional, retornando uma resposta semântica e contextualizada."
    )
    args_schema: Type[BaseModel] = ApiDocumentationExplorerInput

    def _run(self, task: str, url: str = None) -> str:
        """
        Executa um agente de IA para explorar a documentação de uma API (opcionalmente acessando a URL fornecida) e responder à task informada.
        """
        import asyncio
        import os
        async def main():
            config = BrowserConfig(
                headless=True,
                disable_security=True
            )
            browser = Browser(config=config)
            initial_actions = []
            if url:
                initial_actions.append({'open_tab': {'url': url}})
            agent = Agent(
                task=(
                    f"# Consulta sobre documentação de API\n\n"
                    f"## Objetivo\n"
                    f"{task}\n\n"
                    + (f"## URL da documentação\n{url}\n\n" if url else "")
                    + "Analise a documentação e forneça uma resposta clara, objetiva e contextualizada para a task informada, citando trechos relevantes se necessário. Responda SEMPRE em português brasileiro."
                ),
                initial_actions=initial_actions,
                llm=AzureChatOpenAI(model="gpt-4.1", api_version="2025-01-01-preview", api_key=os.getenv("AZURE_API_KEY"), azure_endpoint=os.getenv("AZURE_API_BASE")),
                planner_llm=AzureChatOpenAI(model="gpt-4.1", api_version="2025-01-01-preview", api_key=os.getenv("AZURE_API_KEY"), azure_endpoint=os.getenv("AZURE_API_BASE")),
                browser=browser,
                use_vision=True,
                use_vision_for_planner=True,
                max_actions_per_step=30,
                max_failures=5,
                save_conversation_path="logs/api_documentation_explorer"
            )
            result = await agent.run()
            await browser.close()
            return result

        result = asyncio.run(main())
        resultado_final = result.final_result()
        return resultado_final


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python api_documentation_explorer_tool.py 'Sua task aqui' [url_opcional]")
        sys.exit(1)
    
    task = sys.argv[1]
    url = sys.argv[2] if len(sys.argv) > 2 else None
    
    tool = ApiDocumentationExplorerTool()
    result = tool._run(task=task, url=url)
    
    print("\nResultado:")
    print(result)
