import { useMutation } from "@tanstack/react-query";
import { ClipboardCopy, Play, ShieldCheck, TerminalSquare } from "lucide-react";
import { publicBase } from "@/lib/api";
import { useDashboardData } from "@/hooks/useDashboardData";
import { useAppStore } from "@/store/useAppStore";

const promptTemplates = [
  {
    id: "local-smoke",
    title: "Smoke local",
    category: "Teste",
    prompt: "Responda apenas ROUTEX_LOCAL_OK, sem explicacoes.",
  },
  {
    id: "explain-code",
    title: "Explicar codigo",
    category: "Dev",
    prompt: "Explique o arquivo selecionado em bullets objetivos: responsabilidades, riscos e proximos passos.",
  },
  {
    id: "refactor-plan",
    title: "Plano de refatoracao",
    category: "Dev",
    prompt: "Crie um plano de refatoracao incremental, seguro e testavel para este modulo.",
  },
  {
    id: "security-review",
    title: "Revisao de seguranca",
    category: "Seguranca",
    prompt: "Revise este fluxo procurando vazamento de segredo, logging indevido e bypass de politica.",
  },
  {
    id: "test-plan",
    title: "Testes",
    category: "QA",
    prompt: "Liste testes unitarios, integracao e smoke para validar esta mudanca sem flakiness.",
  },
];

type ChatResponse = {
  choices?: Array<{ message?: { content?: string } }>;
};

export function PromptsPage() {
  const { settings } = useDashboardData();
  const activeModelAlias = useAppStore((state) => state.activeModelAlias);
  const setActiveModelAlias = useAppStore((state) => state.setActiveModelAlias);
  const modelAlias =
    activeModelAlias ?? settings.data?.effective.cursor_model_alias ?? "qwen2.5-coder:latest";
  const runPrompt = useMutation({
    mutationFn: async (prompt: string) => {
      const response = await fetch(`${publicBase}/v1/chat/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model: modelAlias,
          messages: [
            { role: "system", content: "Voce responde de forma curta e objetiva." },
            { role: "user", content: prompt },
          ],
          metadata: {
            routex: {
              profile: settings.data?.effective.default_profile,
              privacy_mode: settings.data?.effective.default_profile === "private-mode",
            },
          },
          max_tokens: 80,
          stream: false,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      return response.json() as Promise<ChatResponse>;
    },
  });

  return (
    <section className="operator-grid">
      <section className="panel operator-focus">
        <header className="operator-header">
          <div>
            <p>Prompt Console</p>
            <h2>Prompts prontos para validar o RouteX</h2>
            <span>
              Use como biblioteca operacional, smoke de privacidade ou base para configurar prompts
              de Cursor/Cline/Continue.
            </span>
          </div>
          <TerminalSquare size={26} />
        </header>
        <div className="model-selector-row">
          <label>
            Alias usado no teste
            <input
              value={modelAlias}
              onChange={(event) => setActiveModelAlias(event.target.value)}
            />
          </label>
          <button
            onClick={() => void navigator.clipboard.writeText(modelAlias)}
            type="button"
          >
            Copiar alias
          </button>
        </div>
        <div className="prompt-result">
          <ShieldCheck className="ok" size={18} />
          <div>
            <strong>Resultado do ultimo teste</strong>
            <span>
              {runPrompt.isPending
                ? "Executando..."
                : runPrompt.error
                  ? runPrompt.error.message
                  : runPrompt.data?.choices?.[0]?.message?.content ?? "Nenhum prompt executado."}
            </span>
          </div>
        </div>
      </section>

      <section className="prompt-library">
        {promptTemplates.map((template) => (
          <article key={template.id} className="prompt-card">
            <header>
              <div>
                <span>{template.category}</span>
                <strong>{template.title}</strong>
              </div>
            </header>
            <p>{template.prompt}</p>
            <footer>
              <button
                onClick={() => void navigator.clipboard.writeText(template.prompt)}
                type="button"
              >
                <ClipboardCopy size={14} />
                Copiar
              </button>
              <button onClick={() => runPrompt.mutate(template.prompt)} type="button">
                <Play size={14} />
                Testar via RouteX
              </button>
            </footer>
          </article>
        ))}
      </section>
    </section>
  );
}
