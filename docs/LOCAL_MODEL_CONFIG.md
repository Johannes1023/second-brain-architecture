# Local model configuration: loopback-only, no cloud fallback

`AGENTS.md` rule 0 asks any AI reading the vault to run entirely on your own hardware. This document is about making that true at the network level, not just by convention, for whichever model runner you use. None of this is enforced by this repository's own code; it cannot reach into a model runner's process to configure or verify it for you.

## The goal

The model process that reads this vault should have no route to the internet at all, or, at minimum, no route to any known cloud-AI endpoint. "No cloud fallback" specifically means: a runner that silently calls a hosted API when the local model is unavailable, slow, or below some confidence threshold defeats rule 0 exactly as thoroughly as manually pointing ChatGPT at the vault, and is easier to miss because nothing about it looks like a mistake at the time.

## LM Studio

- Use LM Studio's local server (OpenAI-compatible, listens on `localhost` by default). Do not enable any "cloud models" or "LM Studio Hub" remote-model feature for the same workspace or agent configuration you point at this vault.
- If you use LM Studio's agent/tool-use features with file access, confirm the model selected for that session is a downloaded, local `.gguf` model, not a placeholder that falls back to a hosted one.
- Check LM Studio's own network settings for any "allow remote connections" toggle: leave it off unless you specifically need another machine on your LAN to reach it, and never expose that port beyond your LAN.

## Ollama

- Ollama serves models on `localhost:11434` by default. Confirm `OLLAMA_HOST` is not set to a non-loopback address unless you intend LAN access, and if you do, restrict it at your router/firewall to your own LAN, never a public interface.
- Ollama itself does not call cloud APIs as a fallback. The risk with Ollama is usually one level up, in whatever agent framework or script drives it: check that framework's own config for a "fallback model" or "cloud model" setting pointed at a hosted provider, and disable it.

## llama.cpp / a custom local agent script

- If you wrote or are using a script that drives `llama.cpp` directly, audit it (or have your local model help you audit it) for any HTTP client import or API key pointed at a hosted provider, even one meant only as an emergency fallback. Remove it rather than gating it behind a flag you might forget is off.
- Prefer running the inference process itself with no outbound network access at the OS level (a restrictive firewall rule scoped to that process, or running it in a container/VM with no network device attached) over trusting the script's own logic. This is the closest this setup gets to a technical enforcement of rule 0, and it is worth doing even though it is outside what this repository's own tooling can set up for you.

## Verifying no outbound access

A reasonable manual check after setting up any of the above: with the model runner running and a chat/agent session open, disconnect the machine's network entirely (turn off Wi-Fi, unplug ethernet) and confirm the vault-reading session still works. If it breaks in a way that suggests it was reaching out to something, that "something" was never local in the first place.

## What this repository's tooling does and does not check

- `lint.py` and `build_export.py` never make a network call themselves; they are pure filesystem tools.
- Neither tool inspects, nor can inspect, whether the model process reading their output (or your vault directly) has network access. That verification is entirely on you, using the steps above.
