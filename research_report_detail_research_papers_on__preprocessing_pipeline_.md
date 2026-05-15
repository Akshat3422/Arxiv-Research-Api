# ArXiv Research Report: Detailed Research on Preprocessing Pipelines for STT and TTS Voice Agents

**Date:** 2026-05-15 21:15:00  
**Scope:** Deep technical synthesis of the retrieved ArXiv papers, with emphasis on what each paper implies for a production voice-agent pipeline rather than only summarizing abstracts.  
**Important limitation:** The retrieved set is strongest on TTS, voice conversion, speaker adaptation, prosody transfer, and zero-shot synthesis. It is weaker on classic front-end STT preprocessing topics such as VAD, dereverberation, beamforming, packet-loss handling, barge-in, and endpoint detection. Those missing areas are called out as research gaps instead of being treated as solved by these papers.

## Executive Synthesis

The papers collectively show that "preprocessing" for voice agents should not be treated as a shallow input-cleaning step. In modern speech systems, the boundary between preprocessing, representation learning, adaptation, and generation is blurry:

- For STT and voice conversion, preprocessing often becomes **content disentanglement**: extracting linguistic content while suppressing speaker identity, channel, and nuisance variation. The ASR-to-TTS voice conversion paper makes this explicit by using decoded text as a semantic bottleneck, which removes much of the source-speaker leakage that can remain in frame-level phonetic posteriorgrams or acoustic content features.
- For TTS, preprocessing becomes **prompt and conditioning design**: text normalization, speaker embeddings, prosody codes, duration and pitch predictors, neural codec latents, and enrollment-speech selection all shape output quality before the waveform is ever synthesized.
- For real-time voice agents, the critical trade-off is no longer only accuracy. The pipeline must balance **latency, robustness, speaker similarity, prosody stability, privacy, adaptation cost, and failure recovery**.
- The strongest practical lesson is to design a modular pipeline with explicit intermediate representations: audio frames, VAD segments, denoised audio, ASR text or semantic tokens, speaker/prosody embeddings, normalized text, acoustic latents, and vocoder output. Each representation should have measurable quality gates.

## What "Preprocessing Pipeline" Means for Voice Agents

A voice-agent pipeline has two directional flows.

### STT-side pipeline

1. **Audio capture and framing**
   - Microphone or telephony stream is chunked into short frames.
   - The system should track sample rate, channel count, clipping, silence ratio, and packet loss.

2. **Signal cleanup**
   - Typical stages: automatic gain control, noise suppression, echo cancellation, dereverberation, and optional beamforming.
   - These stages are not deeply covered by the retrieved papers, but they are essential in deployment because downstream ASR and speaker embeddings are highly sensitive to channel mismatch.

3. **VAD and endpointing**
   - Voice activity detection decides which frames should be sent to ASR.
   - Endpointing decides when the user turn is complete.
   - This is a major gap in the retrieved paper set. A real report should add dedicated papers on WebRTC VAD, neural VAD, streaming endpointing, and turn-taking models.

4. **ASR feature or representation extraction**
   - In classic ASR this could be log-mel features or filterbanks.
   - In modern systems this can be self-supervised speech embeddings, discrete audio tokens, phonetic posteriorgrams, or direct encoder states.

5. **Text and semantic normalization**
   - ASR output must be normalized before the LLM/NLU layer: punctuation, casing, numbers, dates, domain terms, named entities, and partial-hypothesis stability.

### TTS-side pipeline

1. **Text preprocessing**
   - Normalize abbreviations, numbers, currency, URLs, dates, punctuation, and multilingual text.
   - Convert text into phonemes or other linguistic units when the synthesizer expects them.

2. **Speaker and style conditioning**
   - Speaker embeddings, x-vectors, enrollment prompts, or learned speaker tokens guide identity.
   - Prosody prompts or prosody codes guide rhythm, stress, intonation, and emotion.

3. **Acoustic representation generation**
   - Systems may generate mel spectrograms, codec latents, continuous latent vectors, or discrete tokens.
   - The representation choice directly affects stability, speed, and naturalness.

4. **Vocoder or waveform decoder**
   - A neural vocoder, codec decoder, or diffusion/flow decoder converts acoustic representation into waveform.

5. **Post-processing and safety checks**
   - Loudness normalization, silence trimming, clipping checks, pronunciation validation, and latency monitoring.

## Paper-by-Paper Technical Analysis

### 1. Voice Conversion by Cascading ASR and TTS with Prosody Transfer

**Core idea:** Use ASR to convert source speech into text, then use a Transformer TTS model plus WaveNet vocoder to synthesize the utterance in a target voice. The paper adds a prosody encoder so source prosody can condition the synthesized output.

**Pipeline reconstructed from the paper:**

1. Source waveform enters an ASR system.
2. ASR produces decoded text.
3. A prosody encoder extracts a global prosody code from the source utterance.
4. A multi-speaker Transformer TTS model conditions on text, target speaker x-vector, and prosody code.
5. The model predicts acoustic features.
6. A WaveNet vocoder generates the converted waveform.

**Why this matters for preprocessing:**  
The decoded text acts as a strong linguistic bottleneck. Compared with frame-level PPG or acoustic-content features, text strips away many source speaker and channel artifacts. That is valuable for voice agents because the system can separate "what the user said" from "how the user sounded." The trade-off is that ASR errors become irreversible: if the transcription is wrong, the TTS stage will faithfully synthesize the wrong content.

**Notable implementation details from the PDF:**  
The authors compare a commercial iFLYTEK ASR engine with an ESPnet ASR model and report substantially lower error for iFLYTEK: CER 0.958% and WER 2.954%, versus ESPnet CER 2.415% and WER 7.057%. This is a concrete reminder that upstream ASR quality is not a side detail in cascaded systems; it becomes the content source for every downstream stage.

**Strengths:**

- Clean modular decomposition: ASR, prosody extraction, TTS, vocoder.
- Text intermediate representation improves content-speaker disentanglement.
- Prosody transfer reduces the flatness often caused by pure text bottlenecks.

**Weaknesses and risks:**

- Cascading creates error propagation from ASR into TTS.
- Global prosody codes may miss local word-level emphasis and timing.
- Real-time voice agents would need streaming ASR and low-latency synthesis; the paper is not primarily a streaming architecture paper.

**Voice-agent implication:**  
Use text as the safest semantic representation when content fidelity is more important than preserving source acoustics. Add separate prosody/style features only when they are measured and controlled, because prosody embeddings can accidentally carry speaker identity or emotion in ways that are undesirable for privacy-sensitive agents.

### 2. Transfer Learning from Speech Synthesis to Voice Conversion with Non-Parallel Training Data

**Core idea:** Train a multi-speaker TTS system first, then transfer its text-to-context representation knowledge into a voice conversion model. The voice conversion encoder takes speech instead of text, while the decoder resembles the TTS decoder and is conditioned on speaker embeddings.

**Pipeline reconstructed from the abstract:**

1. Build a multi-speaker sequence-to-sequence TTS model.
2. Let the TTS encoder learn robust linguistic context vectors from text.
3. Train a voice conversion encoder to map source speech into similar latent linguistic representations.
4. Use a decoder conditioned on target speaker embedding to generate acoustic features.
5. Train with non-parallel data by presenting text to the TTS model and speech to the VC model.

**Why this matters for preprocessing:**  
This paper treats representation alignment as a preprocessing problem. Instead of requiring parallel utterances from source and target speakers, it uses the TTS model as a teacher for linguistic structure. The preprocessing objective is not simply to denoise audio; it is to transform speech into a latent space where content is preserved and speaker identity can be swapped.

**Strengths:**

- Avoids the expensive requirement for parallel source-target recordings.
- Uses speaker embeddings to enable any-to-any conversion.
- Shows how TTS can act as a representation-learning scaffold for VC.

**Weaknesses and risks:**

- Quality depends on how speaker-independent the learned linguistic representation really is.
- If the speech encoder leaks source speaker traits, target similarity suffers.
- If text and speech latent spaces are poorly aligned, generated speech may sound unnatural even when content is correct.

**Voice-agent implication:**  
For personalization, use a shared latent representation between STT/TTS/VC modules where possible. A useful production pattern is to train or choose encoders whose outputs are explicitly tested for content preservation, speaker leakage, noise robustness, and accent coverage.

### 3. Latent Linguistic Embedding for Cross-Lingual TTS and Voice Conversion

**Core idea:** Use latent linguistic embeddings to support cross-lingual TTS and voice conversion, including speakers producing speech in languages they did not originally speak. The paper builds on NAUTILUS-style voice cloning with unseen voices and untranscribed speech.

**Pipeline reconstructed from the abstract:**

1. Learn or reuse a latent linguistic embedding, trained in English.
2. Apply it to cross-lingual TTS and VC for German, Finnish, and Mandarin speakers from Voice Conversion Challenge 2020.
3. Generate target-speaker speech in a different language without extra cross-lingual conversion steps.

**Why this matters for preprocessing:**  
Multilingual voice agents need language-agnostic or language-aware intermediate representations. A purely English preprocessing pipeline will break when the user code-switches, pronounces names from another language, or asks the agent to speak in a different language. Latent linguistic embeddings can reduce the dependence on manually engineered phoneme mappings, but they also create new evaluation problems.

**Strengths:**

- Supports both cross-lingual TTS and VC in a unified framework.
- Useful for voice agents that need multilingual output or cross-lingual persona consistency.
- Reduces the need for explicitly transcribed target-speaker data.

**Weaknesses and risks:**

- Naturalness varies by target speaker, according to the authors' abstract.
- Cross-lingual speaker similarity can be misleading: a voice may sound similar but phonotactically unnatural.
- Language-specific prosody and pronunciation may not transfer cleanly through a single latent embedding.

**Voice-agent implication:**  
For multilingual voice agents, the preprocessing pipeline needs language identification, code-switch detection, multilingual text normalization, pronunciation lexicons, and per-language prosody controls. A single embedding layer can help, but it should not be the only safeguard.

### 4. Meta-TTS: Meta-Learning for Few-Shot Speaker Adaptive TTS

**Core idea:** Apply Model-Agnostic Meta-Learning (MAML) to speaker adaptation so a multi-speaker TTS model can adapt to unseen speakers with few enrollment samples and fewer fine-tuning steps.

**Pipeline reconstructed from the abstract:**

1. Train a multi-speaker TTS model with meta-learning across many speaker adaptation tasks.
2. Learn an initialization that can adapt quickly to a new speaker.
3. At enrollment time, fine-tune with a small number of target-speaker samples.
4. Synthesize target-speaker speech after fewer adaptation steps than conventional speaker adaptation.

**Why this matters for preprocessing:**  
For personalization, enrollment audio becomes part of the preprocessing pipeline. Its quality, diversity, phonetic coverage, noise profile, and segmentation determine how well the model adapts. This is easy to overlook if "preprocessing" is viewed only as what happens immediately before ASR.

**Strengths:**

- Targets practical few-shot personalization.
- Addresses the gap between speaker adaptation and speaker encoding.
- Reduces adaptation effort compared with standard fine-tuning.

**Weaknesses and risks:**

- Few-shot adaptation can overfit to enrollment noise, microphone color, or emotional state.
- Fine-tuning is harder to deploy safely on-device than pure speaker-embedding inference.
- Requires careful enrollment validation and consent handling for voice cloning use cases.

**Voice-agent implication:**  
Enrollment preprocessing should include speech-quality scoring, silence trimming, phonetic diversity checks, speaker verification, consent metadata, and rejection of noisy or emotionally extreme samples. The adaptation method is only as reliable as the data admitted into it.

### 5. NaturalSpeech 2: Latent Diffusion Models for Zero-Shot Speech and Singing Synthesis

**Core idea:** Use a neural audio codec with residual vector quantizers to produce quantized latent vectors, then use a diffusion model conditioned on text and speech prompt information to generate speech. The system is scaled to 44K hours of speech and singing data and targets zero-shot synthesis.

**Pipeline reconstructed from the abstract:**

1. Use a neural audio codec to encode speech into latent vectors.
2. Use residual vector quantizers as part of the latent representation.
3. Condition a diffusion model on text input.
4. Add a speech prompting mechanism for in-context speaker/style learning.
5. Use duration and pitch predictors influenced by the prompt.
6. Decode generated latents into speech or singing waveform.

**Why this matters for preprocessing:**  
NaturalSpeech 2 shifts preprocessing from hand-designed acoustic features toward learned audio-codec latents and prompt-conditioned generation. In a voice agent, this means the "input sample" used for TTS style or speaker prompting becomes a first-class conditioning artifact. The prompt must be cleaned, segmented, normalized, and quality-checked because it controls timbre and prosody.

**Strengths:**

- Avoids some instability of autoregressive discrete-token generation, such as word skipping or repetition, as stated in the abstract.
- Supports zero-shot speaker generalization through speech prompts.
- Models prosody, timbre, and style at scale using large speech and singing data.

**Weaknesses and risks:**

- Diffusion sampling can be computationally expensive unless heavily optimized.
- Prompt sensitivity can cause inconsistent style or identity in production.
- Large-scale training improves coverage but does not remove the need for runtime quality gates.

**Voice-agent implication:**  
For high-quality TTS, prefer architectures that separate text content, duration, pitch, speaker identity, and acoustic latent generation. In production, cache speaker/style prompts, score prompt quality, and monitor for skipped/repeated words after synthesis.

## Cross-Paper Comparison

| Dimension | ASR-TTS Cascade | TTS-to-VC Transfer | Cross-Lingual Latent Embedding | Meta-TTS | NaturalSpeech 2 |
|---|---|---|---|---|---|
| Main representation | Text + prosody code | TTS context vectors | Latent linguistic embedding | Meta-learned model initialization | Codec latents + diffusion prompt |
| Best fit | Voice conversion with strong content control | Non-parallel any-to-any VC | Multilingual TTS/VC | Few-shot personalization | Zero-shot high-quality synthesis |
| Preprocessing focus | ASR accuracy, prosody extraction | Latent alignment, speaker disentanglement | Language-independent linguistic encoding | Enrollment sample quality | Prompt quality, codec latent generation |
| Major risk | ASR error propagation | Speaker leakage in latent space | Uneven naturalness across languages/speakers | Overfitting few samples | Latency and prompt instability |
| Voice-agent relevance | Strong for modular STT-to-TTS architecture | Strong for personalization and VC | Strong for multilingual agents | Strong for user-specific voices | Strong for premium natural TTS |

## Deeper Design Recommendations for a Voice-Agent Pipeline

### 1. Treat every boundary as a measurable contract

Do not only measure final WER or MOS. Measure each intermediate stage:

- Audio quality: SNR, clipping, dropped frames, echo level, speech/silence ratio.
- VAD: false start rate, missed speech, endpoint latency, barge-in recovery.
- ASR: WER/CER, partial hypothesis churn, named-entity error rate, punctuation quality.
- Semantic bottleneck: content preservation and speaker leakage.
- TTS text normalization: number/date expansion accuracy, pronunciation consistency.
- Speaker/prosody conditioning: speaker similarity, prosody drift, emotional stability.
- Waveform output: loudness, clipping, latency, skipped/repeated words.

### 2. Prefer explicit representations over hidden coupling

The strongest papers separate content from speaker and style. A robust voice-agent pipeline should maintain explicit artifacts:

- `clean_audio`
- `speech_segments`
- `asr_text`
- `normalized_text`
- `language_id`
- `speaker_embedding`
- `prosody_embedding`
- `duration_pitch_controls`
- `acoustic_latents`
- `synthesized_audio`

This makes debugging possible. If the output voice is wrong, the team can inspect whether the failure came from ASR, text normalization, speaker prompt, prosody prompt, or vocoder output.

### 3. Use text bottlenecks when correctness matters

The ASR-to-TTS cascade shows why text is useful: it is interpretable and strips many acoustic artifacts. For customer support, healthcare, finance, or task execution, text bottlenecks are safer than fully speech-to-speech black boxes because they allow validation and policy checks.

### 4. Use learned acoustic latents when naturalness matters

NaturalSpeech 2 shows the value of codec latents and diffusion for natural, zero-shot synthesis. For emotionally rich assistants or expressive avatars, learned latents can outperform rigid mel-spectrogram pipelines. The cost is harder debugging and higher compute.

### 5. Make enrollment data a controlled asset

Meta-TTS and NaturalSpeech 2 both imply that a small speech prompt or enrollment set can strongly influence output. Production systems should reject or flag bad enrollment clips:

- Too short or too long.
- Too noisy or reverberant.
- Contains background voices.
- Contains strong emotion inconsistent with target persona.
- Poor phonetic coverage.
- Fails speaker-consent or identity checks.

### 6. Keep prosody separate from identity

Prosody transfer improves naturalness, but it can leak speaker identity or emotional state. The ASR-TTS cascade addresses this with a speaker-adversarial idea around the prosody code. For voice agents, the broader rule is: prosody features should be tested for what they encode, not merely whether they improve MOS.

## What the Current Retrieval Misses

To make the research fully complete for STT/TTS preprocessing, add papers in these areas:

- Streaming VAD and endpoint detection for low-latency agents.
- Acoustic echo cancellation for full-duplex voice agents.
- Speech enhancement and dereverberation before ASR.
- Robust ASR under far-field, telephony, accented, and noisy speech.
- Text normalization for TTS in multilingual and code-switched settings.
- Neural codec tokenization and discrete speech representation papers beyond NaturalSpeech 2.
- Evaluation methods for turn-taking, barge-in, interruption handling, and perceived responsiveness.

## Practical Pipeline Blueprint

```text
User audio stream
  -> capture health checks
  -> echo cancellation / noise suppression / gain control
  -> VAD + endpointing
  -> speech enhancement quality gate
  -> streaming ASR
  -> ASR confidence + entity correction
  -> normalized text + language ID
  -> LLM / dialog policy
  -> TTS text normalization
  -> speaker/style/prosody prompt selection
  -> acoustic latent or mel generation
  -> vocoder / codec decoder
  -> loudness + clipping + repetition checks
  -> assistant audio stream
```

## Reading Priority

1. **ASR-TTS cascade with prosody transfer**: best starting point for understanding modular content/prosody/speaker separation.
2. **NaturalSpeech 2**: strongest paper in this set for modern zero-shot synthesis and learned acoustic latent design.
3. **Meta-TTS**: important for personalized voices and enrollment-data design.
4. **TTS-to-VC transfer learning**: useful for non-parallel VC and shared latent representation thinking.
5. **Cross-lingual latent linguistic embedding**: useful for multilingual agents, but should be paired with dedicated multilingual ASR/TTS preprocessing papers.

## Retrieved Papers

### 1. Voice Conversion by Cascading Automatic Speech Recognition and Text-to-Speech Synthesis with Prosody Transfer
- **Authors:** Jing-Xuan Zhang, Li-Juan Liu, Yan-Nian Chen, Ya-Jun Hu, Yuan Jiang, Zhen-Hua Ling, Li-Rong Dai
- **Published:** 2020-09-03
- **Categories:** eess.AS, cs.SD, eess.SP
- **PDF:** [https://arxiv.org/pdf/2009.01475v1](https://arxiv.org/pdf/2009.01475v1)
- **Role in this report:** Evidence for using ASR text as a semantic bottleneck, plus prosody-code conditioning for more natural voice conversion.

### 2. Transfer Learning from Speech Synthesis to Voice Conversion with Non-Parallel Training Data
- **Authors:** Mingyang Zhang, Yi Zhou, Li Zhao, Haizhou Li
- **Published:** 2020-09-30
- **Categories:** eess.AS, cs.SD
- **PDF:** [https://arxiv.org/pdf/2009.14399v2](https://arxiv.org/pdf/2009.14399v2)
- **Role in this report:** Evidence for using TTS-learned linguistic context vectors to supervise speech-side voice conversion representations.

### 3. Latent Linguistic Embedding for Cross-Lingual Text-to-Speech and Voice Conversion
- **Authors:** Hieu-Thi Luong, Junichi Yamagishi
- **Published:** 2020-10-08
- **Categories:** eess.AS, cs.CL, cs.SD
- **PDF:** [https://arxiv.org/pdf/2010.03717v1](https://arxiv.org/pdf/2010.03717v1)
- **Role in this report:** Evidence for unified cross-lingual TTS/VC using latent linguistic embeddings.

### 4. Meta-TTS: Meta-Learning for Few-Shot Speaker Adaptive Text-to-Speech
- **Authors:** Sung-Feng Huang, Chyi-Jiunn Lin, Da-Rong Liu, Yi-Chen Chen, Hung-yi Lee
- **Published:** 2021-11-07
- **Categories:** cs.SD, cs.CL, eess.AS
- **PDF:** [https://arxiv.org/pdf/2111.04040v3](https://arxiv.org/pdf/2111.04040v3)
- **Role in this report:** Evidence for few-shot speaker adaptation and enrollment-quality requirements.

### 5. NaturalSpeech 2: Latent Diffusion Models are Natural and Zero-Shot Speech and Singing Synthesizers
- **Authors:** Kai Shen, Zeqian Ju, Xu Tan, Yanqing Liu, Yichong Leng, Lei He, Tao Qin, Sheng Zhao, Jiang Bian
- **Published:** 2023-04-18
- **Categories:** eess.AS, cs.AI, cs.CL, cs.LG, cs.SD
- **PDF:** [https://arxiv.org/pdf/2304.09116v3](https://arxiv.org/pdf/2304.09116v3)
- **Role in this report:** Evidence for neural-codec latents, diffusion generation, speech prompting, and zero-shot synthesis at scale.

## References

- Zhang et al., **Voice Conversion by Cascading Automatic Speech Recognition and Text-to-Speech Synthesis with Prosody Transfer**. Available at: https://arxiv.org/abs/2009.01475
- Zhang et al., **Transfer Learning from Speech Synthesis to Voice Conversion with Non-Parallel Training Data**. Available at: https://arxiv.org/abs/2009.14399
- Luong and Yamagishi, **Latent Linguistic Embedding for Cross-Lingual Text-to-Speech and Voice Conversion**. Available at: https://arxiv.org/abs/2010.03717
- Huang et al., **Meta-TTS: Meta-Learning for Few-Shot Speaker Adaptive Text-to-Speech**. Available at: https://arxiv.org/abs/2111.04040
- Shen et al., **NaturalSpeech 2: Latent Diffusion Models are Natural and Zero-Shot Speech and Singing Synthesizers**. Available at: https://arxiv.org/abs/2304.09116
