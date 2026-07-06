# wdym Auto-Invoke

Defense-in-depth for the hook contract: a `<prompt-detect>` block present (any verdict) ⇒ invoke the `wdym` skill via the Skill tool **before** processing the prompt; no block ⇒ passthrough, respond normally.
