/**
 * Prompt Template Options for Evidence AI Research Platform
 * Modular configuration structure for prompt template versions.
 */
export const PROMPT_TEMPLATE_OPTIONS = [
  {
    value: 'rag_prompt_v1',
    label: 'RAG Prompt v1.0 (Grounded Citations)',
    description: 'Standard grounded research prompt with comprehensive citations',
  },
  {
    value: 'rag_prompt_v1_1',
    label: 'RAG Prompt v1.1 (Concise Evidence)',
    description: 'High-density, concise response format with citations',
  },
  {
    value: 'rag_prompt_v2',
    label: 'RAG Prompt v2.0 (Strict Grounding)',
    description: 'Strict audit protocol with zero extrapolation and gap detection',
  },
];
