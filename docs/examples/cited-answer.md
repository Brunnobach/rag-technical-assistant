# Example: question answered with cited passages

Default behaviour (`USE_LOCAL_LLM=false`): the API does **not** call a generative model. It retrieves the nearest chunks and assembles them into a template, then returns those chunks as `sources`.

Question:

```text
What temperature range favors mesophilic digestion?
```

Against the sample note `docs/samples/anaerobic-digestion-notes.pdf` (and the same wording in the desk UI demo corpus), a typical `/query` body looks like:

```json
{
  "answer": "Based on the retrieved technical documents, here is the information related to your question:\n\n[1] anaerobic-digestion-notes.pdf (chunk 0):\n--- Page 1 --- Mesophilic anaerobic digestion typically operates between 35 and 40 °C. Prolonged drops below 32 °C reduce methanogenic activity and daily biogas yield. ...\n\nAnswer the question using the passages above. If the context does not contain enough information, say that you cannot answer confidently.",
  "sources": [
    {
      "document": "anaerobic-digestion-notes.pdf",
      "chunk_index": 0,
      "page": 1,
      "text": "--- Page 1 --- Mesophilic anaerobic digestion typically operates between 35 and 40 °C. Prolonged drops below 32 °C reduce methanogenic activity and daily biogas yield. ...",
      "score": 0.81
    }
  ]
}
```

The desk UI in demo mode uses the same idea: lexical overlap over an embedded biogas / telemetry corpus, then a template that quotes the hits. Screenshot: [`docs/desk-ui-cited-answer.png`](../desk-ui-cited-answer.png).
