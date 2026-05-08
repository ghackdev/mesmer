```mermaid
mindmap
  root((Jailbreaking Large Language Models))
    PAIR["PAIR (Prompt Automatic Iterative Refinement)"]
      AM[Algorithm Mechanism]
        Attacker vs. Target LLM
        Iterative Query Loop
        Automated Refinement
        Jailbreak Scoring
      DC[Design Components]
        System Prompt Templates
        Chat History Utilization
        Chain-of-Thought Assessment
      AS[Attack Strategies]
        Role-playing
        Logical Appeal
        Authority Endorsement
      PB[Performance Benefits]
        Query Efficiency
        Human Interpretability
        Strong Transferability
    JCB["JCB (Jailbreak with Cross-Behavior Attacks)"]
      WC[Workflow Components]
        Seed Prompt Generation
        Weighted-Random Selection
        Synonym-based Perturbation
        Execution and Evaluation
      CI[Core Innovations]
        Cross-Behavior Learning
        Knowledge Sharing from Past Success
        Low-Complexity Attack Class
      EF[Efficiency]
        94% fewer queries than PAIR/TAP
        Black-Box access only
        Zero-shot transferability
    AC[Attack Classes]
      PLA[Prompt-Level Attacks]
        Semantic and interpretable
        Social engineering basis
        Human-readable payloads
      TLA[Token-Level Attacks]
        GCG["GCG (Gradient-based)"]
        White-box access requirement
        Uninterpretable token strings
        High query consumption
    EB[Evaluation and Benchmarks]
      DSx[Datasets]
        HarmBench
        JBB-Behaviors
        AdvBench
      MT[Metrics]
        ASR["Attack Success Rate (ASR)"]
        Queries per Success
        StrongREJECT Score
      TM[Target Models]
        Llama-2/3 Resilience
        GPT-3.5/4 Vulnerabilities
        Claude and Gemini results
    DSF[Defense and Safety]
      DM[Defensive Methods]
        SLP["Smooth-LLM (Perturbation)"]
        Perplexity Filtering
        Alignment Guardrails
      RTG[Red Teaming Goals]
        Stress testing blindspots
        Improving safety alignment
        Identifying inherent weaknesses
```

A few notes on what I did:

- Wrapped any node text containing parentheses in `["..."]` shape syntax — Mermaid otherwise tries to parse `(...)` as a shape modifier and chokes.
- Gave the branch nodes short ID prefixes (`AM`, `DC`, `JCB`, etc.) so I could attach the bracketed labels cleanly. Pure-text nodes (the leaves) don't need IDs.
- Indentation is 2 spaces per level — Mermaid's mindmap parser is whitespace-sensitive, so don't reformat with tabs.

If you'd rather have it as a `flowchart TD` (more layout control, less of the radial mindmap look), let me know and I'll re-do it.